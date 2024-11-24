import pandas as pd

from utils.import_service_worker import ServiceLoader


class BaseLoader(object):

    def validate_dataframe(self, dataframe):
        pass


class RakutenBrokerForeignStockLoader(BaseLoader, ServiceLoader):

    def __init__(self):
        super().__init__()
        self.cleanable_signatures = ['楽天ＳＰ', '/N']

    def get_read_config(self):
        return {
            'encoding': 'shift-jis'
        }

    def process_data(self, df, account):
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

        df['exchange_rate'] = df['exchange_rate'].astype(float).round(2)
        df['purchase_price'] = df['purchase_price'].apply(lambda x: x.replace(',', '')).astype(float).round(2)
        df['stock_currency'] = '$'
        return df

    def validate_dataframe(self, dataframe):
        super().validate_dataframe(dataframe)


class RakutenBrokerDomesticStockLoader(BaseLoader, ServiceLoader):
    def __init__(self):
        super().__init__()
        self.cleanable_signatures = ['楽天ＳＰ', '/N']

    def get_read_config(self):
        return {
            'encoding': 'shift-jis'
        }

    def process_data(self, df, account):
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
        df['stock_currency'] = '¥'
        df['settlement_currency'] = '円'
        df['purchase_price'] = df['purchase_price'].apply(lambda x: x.replace(',', '')).astype(float).round(2)
        return df

    def validate_dataframe(self, dataframe):
        super().validate_dataframe(dataframe)
