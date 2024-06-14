import logging

from investments.connector.market_api import MarketApi
from investments.models import Forex
from investments.serializers.serializers import ForexSerializer


class ForexHandler(object):

    def __init__(self):
        self.market_api = MarketApi()

    def update_forex_data(self, forex_symbols):
        logging.info('fetching forex data..')
        if not forex_symbols:
            raise ValueError('No symbols provided')
        forex_data = self.market_api.get_forex_snapshot(tickers=forex_symbols)
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

