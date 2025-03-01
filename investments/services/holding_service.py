import logging
import time
from datetime import datetime
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.forms.models import model_to_dict
from requests import RequestException
from rest_framework.exceptions import ValidationError

from investments.connector.market_api import MarketApi
from investments.models import Holding, StockSplit, Portfolio
from investments.serializers.response_serializers import ResponseHoldingSerializer
from investments.serializers.serializers import HoldingSerializer
from investments.validators.holding_validator import CreateHoldingValidator

logger = logging.getLogger(__name__)

is_dev_env = settings.ENV == 'dev'
if not is_dev_env:
    try:
        from google.appengine.api import taskqueue
    except ImportError:
        logging.exception('Failed to import taskqueue from google.appengine.api')

class HoldingDaemonService:

    def enqueue_holding_values_refresh_tasks(self):
        try:
            portfolios = Portfolio.cron_objects.values_list('id', flat=True).distinct()
            if is_dev_env:
                for portfolio in portfolios:
                    service = HoldingService()
                    service.refresh_holdings_with_current_price({'portfolio': portfolio})
                    time.sleep(5)
            else:
                for portfolio in portfolios:
                    taskqueue.add(
                        queue_name='sync-holding-values',
                        method='GET',
                        url='/investments/portfolio/holdings/refresh/',
                        target='coincraftservice',
                        headers={'Secret': f"{settings.SECRET_KEY}"},
                        params={'portfolio': portfolio}
                    )
            return True
        except Exception as e:
            logging.exception('Failed to create growth tasks: ')
            return False

class HoldingService:
    def __init__(self, market_api=None):
        self.market_api = market_api or MarketApi()

    def refresh_holdings_with_current_price(self, request_data):
        try:
            queryset = Holding.cron_objects.select_related('company').filter(portfolio_id=request_data.get('portfolio'))
            for holding in queryset:
                existing_holding_dict = model_to_dict(holding)
                company = existing_holding_dict.get('company')
                current_price = float(round(self.get_current_holding_price(company), 2))
                total_quantity = int(existing_holding_dict['quantity'])
                total_investment = float(round(existing_holding_dict['total_investment'], 2))

                current_value = round(current_price * total_quantity, 2)
                profit_loss = round(current_value - total_investment, 2)
                Holding.cron_objects.filter(id=holding.id).update(current_price=current_price, current_value=current_value, profit_loss=profit_loss)
            return True
        except Exception as e:
            logging.exception('failed to refresh holdings')
            return False

    def get_current_holdings(self, request_data):
        try:
            queryset = Holding.objects.select_related('company').filter(portfolio_id=request_data.get('portfolio'))
            return ResponseHoldingSerializer(queryset, many=True).data
        except Exception as e:
            logging.exception('failed to get current holdings')
            return None

    def get_current_holding_price(self, company):
        for attempt in range(3):
            try:
                daily_data = self.market_api.get_day_snapshot(tickers=[company])
                if not daily_data:
                    raise MarketApiError("Failed to fetch daily data.")
                return daily_data[0].get('current_price')
            except RequestException as e:
                logging.warning(f"Retry {attempt + 1} for fetching price failed: {e}")
                time.sleep(2)
        raise MarketApiError(f"Failed to fetch data for {company} after 3 retries.")

    def create_holding_object(self, create_params):
        try:
            validated_params = CreateHoldingValidator.validate(create_params)
            company = validated_params['company']
            quantity = validated_params['quantity']
            purchase_price = validated_params['purchase_price']
            portfolio = validated_params['portfolio']
            current_price = create_params.get('current_price', None)

            if not current_price:
                current_price = float(self.get_current_holding_price(company))
            else:
                current_price = float(current_price)
            purchase_price = float(purchase_price)

            # Build the holding object
            holding_object = {
                'quantity': quantity,
                'average_price': Decimal("%.2f" % purchase_price),
                'current_price': Decimal("%.2f" % current_price),
                'current_value': Decimal("%.2f" % (current_price * quantity)),
                'total_investment': Decimal("%.2f" % (purchase_price * quantity)),
                'profit_loss': Decimal("%.2f" % (quantity * (current_price - purchase_price))),
                'stock_currency': create_params.get('stock_currency'),
                'price_updated_at': date.today(),
                'company': company,
                'portfolio': portfolio,
            }
            return holding_object
        except ValidationError as e:
            logging.error(f"Create holding validation error: {e}")
            return None

    def update_holding_object(self, existing_holding_dict, trade, current_price):
        trade_purchase_price = trade['purchase_price']
        trade_purchase_quantity = trade['quantity']
        current_price = float(current_price)
        total_quantity = int(trade['quantity']) + int(existing_holding_dict['quantity'])
        total_investment = round(trade_purchase_quantity * trade_purchase_price, 2) + float(round(existing_holding_dict[
                                                                                                      'total_investment'],
                                                                                                  2))
        current_value = round(current_price * total_quantity, 2)
        updated_holding = {
            'quantity': total_quantity,
            'average_price': Decimal("%.2f" % (total_investment / total_quantity)),
            'current_price': Decimal("%.2f" % current_price),
            'total_investment': Decimal("%.2f" % total_investment),
            'current_value': Decimal("%.2f" % current_value),
            'profit_loss': Decimal("%.2f" % (current_value - total_investment)),
            'stock_currency': trade.get('stock_currency'),
            'price_updated_at': date.today(),
            'company': existing_holding_dict['company'],
            'portfolio': existing_holding_dict['portfolio'],
        }
        if 'id' in existing_holding_dict:
            updated_holding['id'] = existing_holding_dict['id']

        return updated_holding

    def save_holding(self, holding, is_bulk=False):
        if is_bulk:
            if not isinstance(holding, list):
                raise ValidationError("Bulk holding data should be a list.")
            serializer = HoldingSerializer(data=holding, many=True)
        else:
            serializer = HoldingSerializer(data=holding)
        if serializer.is_valid(raise_exception=True):
            instance = serializer.save()
            if is_bulk:
                response_serializer = ResponseHoldingSerializer(instance, many=True)
            else:
                response_serializer = ResponseHoldingSerializer(instance=instance)
            return response_serializer.data
        return None

    def update_holding(self, holding_id, update_params):
        try:
            Holding.objects.filter(id=holding_id).update(**update_params)
        except ValidationError as e:
            logging.error(f"Validation error: {e}")
            raise e

    def merge_holding(self, update_params):
        try:
            validated_params = CreateHoldingValidator.validate(update_params)
            company = validated_params['company']
            portfolio = validated_params['portfolio']

            existing_holding = Holding.objects.filter(company_id=company, portfolio_id=portfolio).first()
            stock_splits = self.get_stock_splits(companies=[company])
            stock_splits_for_company = stock_splits.get(company, [])
            adjusted_trades = self.apply_stock_splits([update_params], stock_splits_for_company)
            update_params = adjusted_trades[0]
            if existing_holding:
                existing_holding_dict = model_to_dict(existing_holding)
                current_price = Decimal(round(self.get_current_holding_price(company), 2))
                update_params = self.update_holding_object(existing_holding_dict, update_params, current_price)
                self.update_holding(existing_holding.id, update_params)
                updated_holding = Holding.objects.filter(id=existing_holding.id).first()
                return ResponseHoldingSerializer(updated_holding).data
            else:
                new_holding = self.create_holding_object(update_params)
                return self.save_holding(new_holding)
        except ValidationError as e:
            logging.error(f"Validation error: {e}")
            raise e

    def merge_bulk_holdings(self, trades):
        try:
            current_value_map = {}
            company_wise_trades = {}
            company_list = []
            for trade in trades:
                company = trade['company']
                if company not in company_list:
                    company_list.append(company)

                if company not in current_value_map:
                    current_value_map[company] = self.get_current_holding_price(company)
                if company not in company_wise_trades:
                    company_wise_trades[company] = []
                company_wise_trades[company].append(trade)

            stock_splits = self.get_stock_splits(companies=company_list)

            for company, trade_list in company_wise_trades.items():
                if not trade_list:
                    continue
                portfolio = trade_list[0]['portfolio']

                stock_splits_for_company = stock_splits.get(company, [])
                trade_list = self.apply_stock_splits(trade_list, stock_splits_for_company)
                existing_holding_dict = {}
                existing_holding_id = None
                existing_holding = Holding.objects.filter(company_id=company, portfolio_id=portfolio).first()
                if existing_holding:
                    existing_holding_id = existing_holding.id
                    existing_holding_dict = model_to_dict(existing_holding)
                for trade in trade_list:
                    if existing_holding_dict:
                        existing_holding_dict = self.update_holding_object(existing_holding_dict, trade,
                                                                           current_value_map[company])
                    else:
                        trade['current_price'] = current_value_map[company]
                        existing_holding_dict = self.create_holding_object(trade)
                if existing_holding_id:
                    self.update_holding(existing_holding_id, existing_holding_dict)
                else:
                    self.save_holding(existing_holding_dict)
            return True
        except ValidationError as e:
            logging.exception(f"Validation error: {e}")
            return False

    def apply_stock_splits(self, trade_list, stock_splits):
        adjusted_purchases = []
        for trade in trade_list:
            trade_copy = trade.copy()
            for stock_split in stock_splits:
                purchase_date = trade_copy['purchase_date']
                purchase_price = trade_copy['purchase_price']
                if not isinstance(purchase_date, datetime) and isinstance(purchase_date, str):
                    purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d')
                if isinstance(purchase_price, Decimal):
                    purchase_price = round(float(purchase_price), 2)
                if stock_split.split_date >= purchase_date.date():
                    denominator, numerator = stock_split.split_ratio.split(':')
                    split_ratio = int(numerator) / int(denominator)
                    trade_copy['quantity'] = int(trade['quantity']) * split_ratio
                    trade_copy['purchase_price'] = float(round((purchase_price / split_ratio), 2))
            adjusted_purchases.append(trade_copy)
        return adjusted_purchases

    def get_stock_splits(self, companies=None):
        stock_split_history = StockSplit.cron_objects.select_related('company').filter(company_id__in=companies).order_by(
            'company_id', '-split_date') if companies else StockSplit.objects.select_related('company').all().order_by(
            'company_id', '-split_date')
        stock_split_map = {}
        for stock_split in stock_split_history:
            if stock_split.company_id not in stock_split_map:
                stock_split_map[stock_split.company_id] = []
            stock_split_map[stock_split.company_id].append(stock_split)
        return stock_split_map


class MarketApiError(Exception):
    """Custom exception for errors in fetching market data."""

    def __init__(self, message="Error fetching market data."):
        """
        Initialize the exception with a custom error message.

        Args:
            message (str, optional): Custom error message. Defaults to "Error fetching market data.".
        """
        self.message = message
        super().__init__(self.message)
