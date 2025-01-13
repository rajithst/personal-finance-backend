import os
from typing import Iterator
from django.conf import settings
from polygon import RESTClient


class PolygonAPI:
    def __init__(self):
        
        self.API_KEY = None
        self.config()
        if not self.API_KEY:
            raise EnvironmentError(f"POLYGON_API_KEY not set: {self.API_KEY}")
        self.client = RESTClient(self.API_KEY)
        
    def config(self):
        if settings.ENV == 'dev':
            from dev_config import POLYGON_API_KEY
            self.API_KEY = POLYGON_API_KEY
        else:
            self.API_KEY = os.environ.get('POLYGON_API_KEY')

    def get_dividend_calendar(self, ticker, from_date, to_date=None):
        if not ticker:
            raise ValueError('Ticker is required')
        results = []
        dividend_response = self.client.list_dividends(ticker=ticker, pay_date_gte=from_date, pay_date_lte=to_date)
        if isinstance(dividend_response, Iterator):
            for dv in dividend_response:
                obj = {
                    'symbol': dv.ticker,
                    'amount': round(dv.cash_amount, 2),
                    'ex_dividend_date': dv.ex_dividend_date,
                    'payment_date': dv.pay_date,
                }
                results.append(obj)
        return results
