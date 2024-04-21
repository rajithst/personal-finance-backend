import os

import fmpsdk

from investments.models import Company


class MarketApi:
    def __init__(self):
        self.api_key = '0Hs8qYwmaIcR2YITC5RIwPdwnLarAt0f'

    def get_company_data(self, tickers):
        if not tickers or len(tickers) == 0:
            raise Exception('Ticker is required')
        if not isinstance(tickers, list):
            raise Exception('Tickers must be a list of symbols')
        if len(tickers) > 15:
            raise Exception('Tickers must not be more than 15 symbols')
        company_data = []
        for ticker in tickers:
            data = fmpsdk.company_profile(self.api_key, ticker)
            if data:
                data = data[0]
            else:
                continue
            fields = Company.get_market_api_fields()
            remap = Company.get_field_remap()
            result = {}
            for field in fields:
                if field in data:
                    if field in remap:
                        result[remap[field]] = data[field]
                    else:
                        result[field] = data[field]
            company_data.append(result)
        return company_data

    def get_day_snapshot(self, ticker):
        if not ticker:
            raise Exception('Ticker is required')
        snapshot = fmpsdk.quote(self.api_key, ticker)

