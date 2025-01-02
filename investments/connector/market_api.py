import os
import logging

import fmpsdk
from datetime import datetime
from django.conf import settings

from investments.connector.connector_const import COMPANY_DATA_FIELDS, COMPANY_DATA_REMAP_FIELDS, DAILY_SNAPSHOT_FIELDS, \
    DAILY_SNAPSHOT_REMAP_FIELDS, HISTORICAL_DATA_FIELDS, HISTORICAL_DATA_REMAP_FIELDS


class ListTickerValidator:

    @staticmethod
    def validate(tickers):
        if not tickers:
            raise ValueError('Tickers is required')
        if not isinstance(tickers, list):
            raise ValueError('Tickers must be a list of symbols')
        if len(tickers) > 50:
            raise ValueError('Tickers must not be more than 15 symbols')

class MarketApi:
    def __init__(self):

        self.API_KEY = None
        self.config()
        if not self.API_KEY:
            raise EnvironmentError(f"MARKET_API_KEY not set: {self.API_KEY}")

    def config(self):
        if settings.ENV == 'dev':
            from dev_config import MARKET_API_KEY
            self.API_KEY = MARKET_API_KEY
        else:
            self.API_KEY = settings.env('MARKET_API_KEY')
        
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
        ListTickerValidator.validate(tickers)
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

    def get_stock_splits(self, tickers, from_date=None, to_date=None):
        fmpsdk.stock_split_calendar(self.API_KEY, tickers)

    def get_historical_stock_splits(self, tickers):
        ListTickerValidator.validate(tickers)
        split_results = []
        for ticker in tickers:
            historical_split = fmpsdk.historical_stock_split(self.API_KEY, ticker)
            if historical_split:
                historical_split = historical_split['historical']
            else:
                continue
            for split in historical_split:
                split['symbol'] = ticker
                split_results.append(split)
        return split_results

    def get_day_snapshot(self, tickers):
        ListTickerValidator.validate(tickers)
        daily_data = []
        for ticker in tickers:
            snapshot = fmpsdk.quote(self.API_KEY, ticker)
            if snapshot:
                snapshot = snapshot[0]
            else:
                continue
            snapshot['timestamp'] = datetime.fromtimestamp(snapshot['timestamp']).date()
            day_data = self.map_to_model(snapshot, DAILY_SNAPSHOT_FIELDS, DAILY_SNAPSHOT_REMAP_FIELDS)
            day_data['company_id'] = ticker
            daily_data.append(day_data)
        return daily_data

    def get_forex_snapshot(self, tickers):
        ListTickerValidator.validate(tickers)
        forex_data = []
        for ticker in tickers:
            snapshot = fmpsdk.quote(self.API_KEY, ticker)
            if snapshot:
                snapshot = snapshot[0]
            else:
                continue
            forex_data.append({'name': snapshot['name'], 'symbol': snapshot['symbol'], 'price': round(snapshot['price'],4)})
        return forex_data

    def get_dividend_calendar(self, tickers, from_date, to_date=None):
        ListTickerValidator.validate(tickers)
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

    def get_historical_data(self, tickers, from_date=None, to_date=None):
        ListTickerValidator.validate(tickers)
        historical_data = []
        for ticker in tickers:
            data = fmpsdk.historical_price_full(self.API_KEY, ticker, from_date, to_date)
            if not data:
                continue
            for d in data:
                daily_prices = self.map_to_model(d, HISTORICAL_DATA_FIELDS, HISTORICAL_DATA_REMAP_FIELDS)
                daily_prices['change_percentage'] = round(daily_prices['change_percentage'], 2)
                daily_prices['current_price'] = round(daily_prices['current_price'], 2)
                daily_prices['day_high_price'] = round(daily_prices['day_high_price'], 2)
                daily_prices['day_low_price'] = round(daily_prices['day_low_price'], 2)
                daily_prices['company_id'] = ticker
                historical_data.append(daily_prices)
        return historical_data
