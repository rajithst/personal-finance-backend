import logging
import os

import pandas as pd
from django.conf import settings

from investments.models import Company
from utils.gcs import GCSHandler


class RakutenSecLoader:

    def __init__(self):
        self.foreign_stock_data_path = 'investments/foreign/'
        self.domestic_stock_data_path = 'investments/domestic/'
        self.bucket_name = settings.BUCKET_NAME
        self.is_dev_env = settings.ENV == 'dev'
        self.blob_handler = None
        if not self.is_dev_env:
            self.blob_handler = GCSHandler()


    def get_files(self, target_path: str):
        if self.is_dev_env:
            data_path = os.path.join(settings.MEDIA_ROOT, target_path)
            files = os.listdir(data_path)
        else:
            files = self.blob_handler.list_files(bucket_name=self.bucket_name, prefix=target_path)
        return files

    def read_csv(self, file, target_path: str):
        if self.is_dev_env:
            data_path = os.path.join(settings.MEDIA_ROOT, target_path)
            df = pd.read_csv(os.path.join(data_path, file), encoding='shift_jis')
        else:
            blob_data = self.blob_handler.get_blob(bucket_name=self.bucket_name, file_name=file)
            df = pd.read_csv(blob_data, encoding='shift_jis')
        return df

    def import_foreign_trades(self):
        files = self.get_files(self.foreign_stock_data_path)
        results = []
        for file in files:
            if self.is_dev_env:
                blob_data = os.path.join(settings.MEDIA_ROOT, self.foreign_stock_data_path, file)
            else:
                blob_data = self.blob_handler.get_blob(bucket_name=self.bucket_name, file_name=file)
            df = pd.read_csv(blob_data, encoding='shift_jis')
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
            companies = Company.objects.values_list('symbol', flat=True).distinct()
            df = df[df['company'].apply(lambda x: x in companies)]
            df['exchange_rate'] = df['exchange_rate'].astype(float).round(2)
            df['purchase_price'] = df['purchase_price'].astype(float).round(2)
            df['stock_currency'] = '$'
            results.append(df)
        trade_history = pd.concat(results)
        return trade_history

    def import_domestic_trades(self):
        files = self.get_files(self.domestic_stock_data_path)
        results = []
        for file in files:
            df = self.read_csv(file, self.domestic_stock_data_path)
            df.columns = ['Trade date', 'Delivery date', 'Ticker', 'Stock name', 'Market name', 'Account',
                          'Trade class',
                          'Buy/sell class', 'Credit class', 'Payment deadline', 'Quantity [shares]', 'Unit price [Yen]',
                          'Fees [yen]', 'Taxes etc. [yen]', 'Miscellaneous expenses [yen]', 'Tax category',
                          'Delivery amount [yen]', 'Building contract date', 'unit price [yen]', 'building fee [yen]',
                          'building fee consumption tax [yen]', 'interest (payment) [yen]',
                          'Interest rate (receiving) [yen]',
                          'Reverse day rate/special short selling fee (payment) [yen]',
                          'Reverse day rate (receiving) [yen]', 'Stock lending fee',
                          'Administrative expenses [yen] 〕(Tax excluded)',
                          'Name transfer fee [yen] (excluding tax)']
            df = df[df['Buy/sell class'] == '買付']
            df.drop(columns=['Trade date', 'Stock name', 'Market name', 'Account', 'Trade class', 'Buy/sell class',
                             'Credit class', 'Payment deadline', 'Fees [yen]', 'Taxes etc. [yen]', 'Fees [yen]',
                             'Taxes etc. [yen]', 'Miscellaneous expenses [yen]', 'Tax category',
                             'Building contract date', 'unit price [yen]', 'building fee [yen]',
                             'building fee consumption tax [yen]', 'interest (payment) [yen]', 'Delivery amount [yen]',
                             'Interest rate (receiving) [yen]',
                             'Reverse day rate/special short selling fee (payment) [yen]',
                             'Reverse day rate (receiving) [yen]', 'Stock lending fee',
                             'Administrative expenses [yen] 〕(Tax excluded)',
                             'Name transfer fee [yen] (excluding tax)'], inplace=True)
            df.columns = ['purchase_date', 'company', 'quantity', 'purchase_price']
            df['purchase_date'] = pd.to_datetime(df['purchase_date'], format='%Y/%m/%d').dt.date
            df['company'] = df['company'].apply(lambda x: str(x) + '.T')
            companies = Company.objects.values_list('symbol', flat=True).distinct()
            df = df[df['company'].apply(lambda x: x in companies)]
            #TODO if new company found, add to companies
            df['stock_currency'] = '¥'
            df['settlement_currency'] = '円'
            df['purchase_price'] = df['purchase_price'].apply(lambda x: x.replace(',', '')).astype(float).round(2)
            results.append(df)
        trade_history = pd.concat(results)
        return trade_history


class BrokerDataLoader:

    def process(self):
        importer = BrokerLoaderFactory.create('rakuten')
        foreign_trade_history = importer.import_foreign_trades()
        domestic_trade_history = importer.import_domestic_trades()
        return foreign_trade_history.to_dict('records') + domestic_trade_history.to_dict('records')


class BrokerLoaderFactory:
    @staticmethod
    def create(broker, **kwargs):
        if broker == 'rakuten':
            return RakutenSecLoader()
        else:
            raise ValueError('Unknown broker')
