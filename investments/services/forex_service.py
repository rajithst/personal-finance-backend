import logging

from investments.connector.market_api import MarketApi
from investments.models import Forex
from investments.serializers.serializers import ForexSerializer
from investments.validators.forex_validator import ForexValidator


class ForexService:
    def __init__(self, market_api=None):
        self.market_api = market_api or MarketApi()

    def update_daily_price(self, request_data):
        ForexValidator().validate_request(request_data)
        currency = request_data.get('currency', None)
        currencies = currency.split(',')
        forex_data = self.market_api.get_forex_snapshot(tickers=currencies)
        for data in forex_data:
            current_forex = Forex.objects.filter(symbol=data.get('symbol'))
            if current_forex.exists():
                current_forex = current_forex.first()
                current_forex.price = data.get('price')
                current_forex.save()
            else:
                serializer = ForexSerializer(data=data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
        return forex_data
