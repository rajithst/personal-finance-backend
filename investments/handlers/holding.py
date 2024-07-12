import logging
from datetime import date
from decimal import Decimal
from django.conf import settings

from investments.connector.market_api import MarketApi
from investments.models import Holding, StockDailyPrice
from investments.serializers.serializers import HoldingSerializer, StockDailyPriceSerializer


class HoldingHandler(object):

    def __init__(self):
        self.market_api = MarketApi()
        self.is_dev_env = settings.ENV == 'dev'

    def merge_holding(self, symbol, update_params):
        if not symbol or not update_params:
            raise ValueError('No symbol or update_params provided')

        quantity = update_params.get('quantity', 0)
        purchase_price = update_params.get('purchase_price', None)
        if not quantity or not purchase_price:
            raise ValueError('No quantity or  purchase_price provided')
        exist_holding = Holding.objects.filter(company_id=symbol)
        daily_data = self.market_api.get_day_snapshot(tickers=[symbol])
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
                exist_holding.average_price = round((exist_holding.total_investment / exist_holding.quantity),2)
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

    def update_daily_price(self, symbols):
        logging.info('fetching market data..')
        if not symbols:
            raise ValueError('No symbols provided')
        daily_data = self.market_api.get_day_snapshot(tickers=symbols)
        for data in daily_data:
            current_holding = Holding.objects.filter(company_id=data.get('symbol'))
            if current_holding.exists():
                current_holding = current_holding.first()
                current_price = data.get('current_price')
                current_value = current_price * current_holding.quantity
                current_holding.average_price = round((current_holding.total_investment / current_holding.quantity),2)
                current_holding.current_price = current_price
                current_holding.current_value = current_value
                current_holding.profit_loss = Decimal(current_value) - current_holding.total_investment
                current_holding.price_updated_at = date.today()
                current_holding.save()

                self.save_stock_price_history(data)
        return daily_data

    def save_stock_price_history(self, data):
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
