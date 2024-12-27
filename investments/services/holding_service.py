import logging
import time
from datetime import date
from decimal import Decimal

from requests import RequestException
from rest_framework.exceptions import ValidationError

from investments.connector.market_api import MarketApi
from investments.models import Holding
from investments.serializers.response_serializers import ResponseHoldingSerializer
from investments.serializers.serializers import HoldingSerializer
from investments.validators.holding_validator import CreateHoldingValidator, ListHoldingValidator

logger = logging.getLogger(__name__)


class HoldingService:
    def __init__(self, market_api=None):
        self.market_api = market_api or MarketApi()

    def get_current_holdings(self, request_data):
        ListHoldingValidator().validate(request_data)
        queryset = Holding.objects.select_related('company').filter(portfolio_id=request_data.get('portfolio'))
        return ResponseHoldingSerializer(queryset, many=True).data

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

    def create_holding(self, create_params):
        try:
            validated_params = CreateHoldingValidator.validate(create_params)
            company = validated_params['company']
            quantity = validated_params['quantity']
            purchase_price = validated_params['purchase_price']
            portfolio = validated_params['portfolio']

            # Fetch the current price
            current_price = Decimal(round(self.get_current_holding_price(company), 2))
            purchase_price = Decimal(round(purchase_price, 2))

            # Build the holding object
            holding_object = {
                'quantity': quantity,
                'average_price': Decimal(round(purchase_price, 2)),
                'current_price': Decimal(round(current_price, 2)),
                'total_investment': Decimal(round(purchase_price * quantity, 2)),
                'profit_loss': Decimal(round(quantity * (current_price - purchase_price), 2)),
                'stock_currency': create_params.get('stock_currency'),
                'price_updated_at': date.today(),
                'company': company,
                'portfolio': portfolio,
            }

            # Serialize and save the holding
            serializer = HoldingSerializer(data=holding_object)
            if serializer.is_valid(raise_exception=True):
                instance = serializer.save()
                response_serializer = ResponseHoldingSerializer(instance=instance)
                return response_serializer.data
            return None
        except ValidationError as e:
            logging.error(f"Create holding validation error: {e}")
            return None

    def merge_holding(self, update_params):
        try:
            validated_params = CreateHoldingValidator.validate(update_params)
            company = validated_params['company']
            quantity = validated_params['quantity']
            purchase_price = validated_params['purchase_price']
            portfolio = validated_params['portfolio']

            existing_holding = Holding.objects.filter(company_id=company, portfolio_id=portfolio).first()
            if existing_holding:
                current_price = Decimal(self.get_current_holding_price(company))
                existing_holding.quantity += quantity
                existing_holding.total_investment += Decimal(round(quantity * purchase_price, 2))
                existing_holding.current_price = round(current_price, 2)
                existing_holding.current_value = round(current_price * existing_holding.quantity, 2)
                existing_holding.average_price = round(existing_holding.total_investment / existing_holding.quantity, 2)
                existing_holding.profit_loss = Decimal(
                    existing_holding.current_value) - existing_holding.total_investment
                existing_holding.price_updated_at = date.today()
                existing_holding.save()
                return ResponseHoldingSerializer(instance=existing_holding).data
            else:
                return self.create_holding(update_params)
        except ValidationError as e:
            logging.error(f"Validation error: {e}")
            raise e


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
