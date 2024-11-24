from polygon import RESTClient

class PolygonAPI:
    def __init__(self):
        self.API_KEY = '8dWkPLTjCVxRwKRJD_cUfzBsDr8l1v9B'
        if not self.API_KEY:
            raise EnvironmentError(f"MARKET_API_KEY not set: {self.API_KEY}")
        self.client = RESTClient(self.API_KEY)

    def get_dividend_calendar(self, ticker, from_date, to_date=None):
        if not ticker:
            raise Exception('Ticker is required')
        dividend_data, status = self.client.list_dividends(pay_date_gte=from_date, pay_date_lte=to_date)
        results = []
        if status == 'OK':
            for dv in dividend_data:
                obj = {
                    'symbol': dv['ticker'],
                    'amount': round(dv['cash_amount'], 2),
                    'ex_dividend_date': dv['ex_dividend_date'],
                    'payment_date': dv['pay_date'],
                }
                results.append(obj)
        return results
