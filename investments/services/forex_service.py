import logging

from investments.connector.market_api import MarketApi
from investments.models import Forex
from investments.serializers.serializers import ForexSerializer


class ForexService:

    def update_daily_price(self, currencies):
        market_api = MarketApi()
        forex_data = market_api.get_forex_snapshot(tickers=currencies)
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
