from investments.connector.market_api import MarketApi
from investments.models import Forex


class ForexHandler(object):

    def __init__(self):
        self.market_api = MarketApi()

    def update_forex_data(self):
        forex_symbols = Forex.objects.values_list('symbol', flat=True).distinct()
        forex_data = self.market_api.get_forex_snapshot(tickers=forex_symbols)
        for data in forex_data:
            Forex.objects.filter(symbol=data['symbol']).update(price=data['price'])
        return forex_data
