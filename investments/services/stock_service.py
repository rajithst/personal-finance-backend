import logging
from datetime import date
from decimal import Decimal

from investments.connector.market_api import MarketApi
from investments.models import Holding, StockDailyPrice, StockPurchaseHistory
from investments.serializers.response_serializers import ResponseHoldingSerializer, \
    ResponseStockPurchaseHistorySerializer
from investments.serializers.serializers import StockDailyPriceSerializer, HoldingSerializer, \
    StockPurchaseHistorySerializer


class StockService:

    def update_daily_price(self, companies):
        logging.info('fetching market data..')
        if not companies:
            raise ValueError('No symbols provided')
        market_api = MarketApi()
        daily_data = market_api.get_day_snapshot(tickers=companies)
        for data in daily_data:
            queryset = StockDailyPrice.objects.filter(company_id=data['symbol'], date=data.get('date')).first()
            if queryset:
                queryset.current_price = data.get('current_price')
                queryset.change_percentage = data.get('change_percentage')
                queryset.change = data.get('change')
                queryset.day_high_price = data.get('day_high_price')
                queryset.day_low_price = data.get('day_low_price')
                queryset.save()
            else:
                serializer = StockDailyPriceSerializer(data=data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
        return daily_data
        #
        # market_api = MarketApi()
        # daily_data = market_api.get_day_snapshot(tickers=companies)
        # for data in daily_data:
        #     current_holding = Holding.objects.filter(company_id=data.get('symbol'))
        #     if current_holding.exists():
        #         current_holding = current_holding.first()
        #         current_price = data.get('current_price')
        #         current_value = current_price * current_holding.quantity
        #         current_holding.average_price = round((current_holding.total_investment / current_holding.quantity), 2)
        #         current_holding.current_price = current_price
        #         current_holding.current_value = current_value
        #         current_holding.profit_loss = Decimal(current_value) - current_holding.total_investment
        #         current_holding.price_updated_at = date.today()
        #         current_holding.save()
        #
        #         self.save_stock_price_history(data)

    def merge_holding(self, company, update_params):
        if not company or not update_params:
            raise ValueError('No symbol or update_params provided')

        quantity = update_params.get('quantity', 0)
        purchase_price = update_params.get('purchase_price', None)
        if not quantity or not purchase_price:
            raise ValueError('No quantity or  purchase_price provided')
        exist_holding = Holding.objects.filter(company_id=company)
        market_api = MarketApi()
        daily_data = market_api.get_day_snapshot(tickers=[company])
        current_price = None
        if daily_data:
            daily_data = daily_data[0]
            current_price = daily_data.get('current_price')
        try:
            if exist_holding.exists():
                exist_holding = exist_holding.first()
                exist_holding.quantity = quantity + exist_holding.quantity
                exist_holding.total_investment = exist_holding.total_investment + Decimal(quantity * purchase_price)
                exist_holding.current_price = current_price
                exist_holding.current_value = current_price * exist_holding.quantity
                exist_holding.average_price = round((exist_holding.total_investment / exist_holding.quantity), 2)
                exist_holding.profit_loss = Decimal(exist_holding.current_value) - exist_holding.total_investment
                exist_holding.price_updated_at = date.today()
                exist_holding.save()
                return True
            else:
                update_params['average_price'] = purchase_price
                update_params['total_investment'] = round(purchase_price * quantity, 2)
                update_params['current_price'] = current_price
                update_params['current_value'] = current_price * quantity
                update_params['profit_loss'] = update_params['current_value'] - update_params['total_investment']
                exist_holding['price_updated_at'] = date.today()
                serializer = HoldingSerializer(data=update_params)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    return True
        except Exception as e:
            logging.error(e)
            return False

    def create_purchase(self, request_data):
        company = request_data.get('company')
        serializer = StockPurchaseHistorySerializer(data=request_data)
        if serializer.is_valid(raise_exception=True):
            merge_results = self.merge_holding(company, update_params=request_data)
            if merge_results:
                instance = serializer.save()
                if instance:
                    updated_holding = Holding.objects.select_related('company').filter(company_id=company).first()
                    holding_serializer = ResponseHoldingSerializer(updated_holding)
                    return True, holding_serializer.data
        return False, serializer.errors

    def create_bulk_purchase(self, trade_data):
        purchase_history_serializer = StockPurchaseHistorySerializer(data=trade_data, many=True)
        if purchase_history_serializer.is_valid(raise_exception=True):
            purchase_history_serializer.save()
            return True, purchase_history_serializer.data
        return False, purchase_history_serializer.errors

    def get_purchase_history(self, company=None):
        filter_params = {}
        if company:
            filter_params['company_id'] = company
        queryset = StockPurchaseHistory.objects.select_related('company').filter(**filter_params).all()
        serializer = ResponseStockPurchaseHistorySerializer(queryset, many=True)
        return serializer.data

    def get_price_history(self, company, start_date=None, end_date=None):
        today = date.today()
        if not start_date and not end_date:
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)

        queryset = StockDailyPrice.objects.filter(company_id=company, date__range=(start_date, end_date)).order_by(
            'date')
        serializer = StockDailyPriceSerializer(queryset, many=True)
        return serializer.data

    def import_historical_data(self, request_data):
        tickers = request_data.get('tickers')
        from_date = request_data.get('from_date', None)
        to_date = request_data.get('to_date', None)
        market_api = MarketApi()
        historical_data = market_api.get_historical_data(tickers, from_date=from_date, to_date=to_date)
        instances = [StockDailyPrice(**params) for params in historical_data]
        try:
            StockDailyPrice.objects.bulk_create(instances)
            return historical_data
        except Exception as e:
            logging.exception('Failed to update historical data')
            return False
