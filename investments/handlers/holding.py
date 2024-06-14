import logging
from datetime import date
from decimal import Decimal
from google.appengine.api import taskqueue

from investments.connector.market_api import MarketApi
from investments.models import Holding, StockDailyPrice
from investments.serializers.serializers import HoldingSerializer, StockDailyPriceSerializer

STOCK_DATA_UPDATE_URL = '/investments/refresh/stock-data'
QUEUE_NAME = 'update-stock-value'


class HoldingHandler(object):

    def __init__(self):
        self.market_api = MarketApi()

    def merge_holding(self, symbol, update_params):
        if not symbol or not update_params:
            raise ValueError('No symbol or update_params provided')

        quantity = update_params.get('quantity', None)
        purchase_price = update_params.get('purchase_price', None)
        if not quantity or not purchase_price:
            raise ValueError('No quantity or  purchase_price provided')
        exist_holding = Holding.objects.filter(company_id=symbol)
        if exist_holding.exists():
            exist_holding = exist_holding.first()
            exist_holding.new_quantity = quantity + exist_holding.quantity
            exist_holding.total_investment = exist_holding.total_investment + Decimal(quantity * purchase_price)
            exist_holding.save()

        else:
            update_params['average_price'] = purchase_price
            update_params['total_investment'] = round(purchase_price * quantity, 2)
            serializer = HoldingSerializer(data=update_params)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
        taskqueue.add(
            url=STOCK_DATA_UPDATE_URL,
            queue_name=QUEUE_NAME,
            method='GET',
            params={'tickers': symbol})

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

                current_holding.current_price = current_price
                current_holding.current_value = current_value
                current_holding.profit_loss = Decimal(current_value) - current_holding.total_investment
                current_holding.price_updated_at = date.today()
                current_holding.save()

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