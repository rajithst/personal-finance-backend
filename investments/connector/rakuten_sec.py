import os

import pandas as pd
from django.conf import settings


class RakutenSecLoader:

    def __init__(self):
        self.data_path = os.path.join(settings.MEDIA_ROOT, 'investments')

    def import_trades(self):
        files = os.listdir(self.data_path)
        results = []
        for file in files:
            df = pd.read_csv(os.path.join(self.data_path, file))
            df.columns = ['Trade date', 'Delivery date', 'Ticker', 'Stock name', 'Account', 'Trade class',
                          'Buy/sell class', 'Credit class', 'Payment deadline',
                          'Settlement currency', 'Quantity [shares]', 'Unit price [US dollars]',
                          'Execution amount [US dollars]', 'Exchange rate', 'Fees [US dollars]',
                          'Tax [US dollar]', 'Delivery amount [US dollar]', 'Delivery amount [yen]']
            df = df[df['Buy/sell class'] == '買付']
            df.drop(columns=['Trade date', 'Stock name', 'Account', 'Trade class', 'Execution amount [US dollars]',
                             'Buy/sell class', 'Credit class', 'Payment deadline', 'Fees [US dollars]',
                             'Tax [US dollar]', 'Delivery amount [US dollar]', 'Delivery amount [yen]'], inplace=True)
            df.columns = ['purchase_date', 'company', 'settlement_currency', 'quantity', 'purchase_price',
                          'exchange_rate']
            df['purchase_date'] = pd.to_datetime(df['purchase_date'], format='%Y/%m/%d').dt.date
            companies = ['AAPL', 'AMZN', 'GOOGL', 'ABBV', 'JPM', 'KHC', 'MSFT', 'PG', 'TSM', 'TSLA', 'GASS']
            df = df[df['company'].apply(lambda x: x in companies)]
            df['exchange_rate'] = df['exchange_rate'].round(decimals=2)
            df['purchase_price'] = df['purchase_price'].round(decimals=2)
            results.append(df)
        trade_history = pd.concat(results)
        return trade_history


class BrokerDataLoader:

    def process(self):
        importer = BrokerLoaderFactory.create('rakuten')
        trade_history = importer.import_trades()
        return trade_history.to_dict('records')


class BrokerLoaderFactory:
    @staticmethod
    def create(broker, **kwargs):
        if broker == 'rakuten':
            return RakutenSecLoader()
        else:
            raise ValueError('Unknown broker')
