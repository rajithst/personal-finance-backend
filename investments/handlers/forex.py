from datetime import date
from dateutil.relativedelta import relativedelta

from investments.connector.market_api import MarketApi
from investments.models import Forex, Company, Dividend
from investments.serializers.serializers import DividendSerializer


class ForexHandler(object):

    def __init__(self):
        self.market_api = MarketApi()

    def update_forex_data(self):
        forex_symbols = Forex.objects.values_list('symbol', flat=True).distinct()
        forex_data = self.market_api.get_forex_snapshot(tickers=forex_symbols)
        for data in forex_data:
            Forex.objects.filter(symbol=data['symbol']).update(price=data['price'])
        return forex_data


class DividendHandler(object):
    def __init__(self):
        self.market_api = MarketApi()

    def update_dividend_data(self, from_date=None, to_date=None):
        tickers = Company.objects.values_list('symbol', flat=True).distinct()
        if not from_date:
            from_date = date.today().strftime('%Y-%m-%d')
        if not to_date:
            to_date = date.today() + relativedelta(months=+3)
            to_date = to_date.strftime('%Y-%m-%d')
        dividend_data = self.market_api.get_dividend_calendar(tickers=tickers, from_date=from_date, to_date=to_date)
        for data in dividend_data:
            company = data['symbol']
            ex_divided_date = data['ex_dividend_date']
            payment_date = data['payment_date']
            amount = round(data['amount'], 2)
            if ex_divided_date and payment_date and amount:
                existing_dividend = Dividend.objects.filter(company=company, ex_dividend_date=ex_divided_date,
                                                            payment_date=payment_date)
                if existing_dividend.exists():
                    existing_dividend.update(amount=amount)
                else:
                    data['company'] = company
                    data['payment_received'] = False
                    data['notes'] = ''
                    serializer = DividendSerializer(data=data)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
        return dividend_data
