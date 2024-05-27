import os
import logging

import fmpsdk
from datetime import datetime
from django.conf import settings

from investments.connector.connector_const import COMPANY_DATA_FIELDS, COMPANY_DATA_REMAP_FIELDS, DAILY_SNAPSHOT_FIELDS, \
    DAILY_SNAPSHOT_REMAP_FIELDS


class MarketApi:
    def __init__(self):

        self.API_KEY = os.getenv('MARKET_API_KEY', None)
        if not self.API_KEY:
            raise EnvironmentError(f"MARKET_API_KEY not set: {self.API_KEY}")


    def map_to_model(self, data, fields, remap_fields=None):
        result = {}
        for field in fields:
            if field in data:
                if field in remap_fields:
                    result[remap_fields[field]] = data[field]
                else:
                    result[field] = data[field]
        return result

    def get_company_data(self, tickers):
        logging.info('Getting company information.')
        if not tickers or len(tickers) == 0:
            raise Exception('Ticker is required')
        if not isinstance(tickers, list):
            raise Exception('Tickers must be a list of symbols')
        if len(tickers) > 50:
            raise Exception('Tickers must not be more than 15 symbols')
        company_data = []
        for ticker in tickers:
            data = fmpsdk.company_profile(self.API_KEY, ticker)
            if data:
                data = data[0]
            else:
                continue
            company_model = self.map_to_model(data, COMPANY_DATA_FIELDS, COMPANY_DATA_REMAP_FIELDS)
            company_data.append(company_model)
        return company_data

    def get_day_snapshot(self, tickers):
        if not tickers or len(tickers) == 0:
            raise Exception('Ticker is required')
        daily_data = []
        for ticker in tickers:
            snapshot = fmpsdk.quote(self.API_KEY, ticker)
            if snapshot:
                snapshot = snapshot[0]
            else:
                continue
            snapshot['timestamp'] = datetime.fromtimestamp(snapshot['timestamp']).date()
            day_data = self.map_to_model(snapshot, DAILY_SNAPSHOT_FIELDS, DAILY_SNAPSHOT_REMAP_FIELDS)
            daily_data.append(day_data)
        return daily_data

    def get_forex_snapshot(self, tickers):
        if not tickers or len(tickers) == 0:
            raise Exception('Tickers is required')
        forex_data = []
        for ticker in tickers:
            snapshot = fmpsdk.quote(self.API_KEY, ticker)
            if snapshot:
                snapshot = snapshot[0]
            else:
                continue
            forex_data.append({'name': snapshot['name'], 'symbol': snapshot['symbol'], 'price': snapshot['price']})
        return forex_data

    def get_dividend_calendar(self, tickers, from_date, to_date=None):
        if not tickers or len(tickers) == 0:
            raise Exception('Tickers is required')
        dividend_data = []
        dividend_info = fmpsdk.calendar.dividend_calendar(apikey=self.API_KEY, from_date=from_date, to_date=to_date)
        for dv in dividend_info:
            if dv['symbol'] in tickers:
                obj = {
                    'symbol': dv['symbol'],
                    'amount': round(dv['dividend'], 2),
                    'ex_dividend_date': dv['recordDate'],
                    'payment_date': dv['paymentDate'],
                }
                dividend_data.append(obj)
        return dividend_data
