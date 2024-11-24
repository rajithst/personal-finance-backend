import logging
import os
import numpy as np
import pandas as pd
from django.conf import settings

from common.enums import DataSource, AccountProviders
from utils.import_service_worker import ServiceLoader


class BaseLoader:

    def set_default_props(self, df, account):
        params_dict = {
            'is_payment': False,
            'is_deleted': False,
            'is_saving': False,
            'is_income': False,
            'notes': np.nan,
            'alias': np.nan,
            'is_expense': True,
            'source': DataSource.IMPORT.value,
            'account_id': account.id
        }
        df = df.assign(**params_dict)
        df = df[df.date.isnull() == False]
        df = df[df.amount.isnull() == False]

        return df

    def clean_electronic_signatures(self, value, signatures):
        if value:
            new_value = value.strip()
            for i in signatures:
                if value.endswith(i) or value.startswith(i):
                    new_value = value.replace(i, '')
                    new_value = new_value.strip()
            return new_value
        return value


    def validate_dataframe(self, transactions):
        if isinstance(transactions, pd.DataFrame):
            return transactions.drop_duplicates()
        else:
            columns = ['date', 'destination_original', 'destination', 'amount', 'account_id', 'notes', 'alias',
                       'is_payment',
                       'is_deleted', 'is_saving', 'is_income', 'source', 'is_expense']
            return pd.DataFrame(columns=columns)

    def clean_destinations(self, df, cleanable_signatures):
        try:
            df['destination'] = df['destination'].apply(
                lambda x: self.clean_electronic_signatures(x, cleanable_signatures))
            df['destination_original'] = df.apply(
                lambda x: x['destination'].strip() if x['destination'] else x['destination'], axis=1)
            return df
        except Exception as e:
            logging.exception(e)


class RakutenCardLoader(BaseLoader, ServiceLoader):
    def __init__(self):
        super().__init__()
        self.cleanable_signatures = ['楽天ＳＰ', '/N']

    def get_read_config(self):
        return {}

    def process_data(self, df, account):
        df = df[['利用日', '利用店名・商品名', '利用金額']]
        df.columns = ['date', 'destination', 'amount']
        df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d').dt.date
        df = self.set_default_props(df, account)
        df = self.clean_destinations(df, self.cleanable_signatures)
        return df

    def validate_dataframe(self, transactions):
        return super().validate_dataframe(transactions)


class EposCardLoader(BaseLoader, ServiceLoader):
    def __init__(self):
        super().__init__()
        self.cleanable_signatures = ['／Ｎ', '／ＮＦＣ', 'ＡＰ／', '／ＮＦＣ ()', '／ＮＦＣ', '	ＡＰ／']

    def get_read_config(self):
        return {
            'encoding': 'cp932',
            'skiprows': 1,
            'skipfooter': 5,
            'engine': 'python'
        }

    def process_data(self, df, account):
        df = df.iloc[:, 1:]
        df = df[['ご利用年月日', 'ご利用場所', 'ご利用金額（キャッシングでは元金になります）']]
        df.columns = ['date', 'destination', 'amount']
        df['date'] = pd.to_datetime(df['date'], format='%Y年%m月%d日').dt.date
        df = self.set_default_props(df, account)
        df = self.clean_destinations(df, self.cleanable_signatures)
        return df

    def validate_dataframe(self, transactions):
        return super().validate_dataframe(transactions)


class DocomoCardLoader(BaseLoader, ServiceLoader):
    def __init__(self):
        super().__init__()
        self.cleanable_signatures = ['／ｉＤ', 'ｉＤ／', '　／ｉＤ', 'ｉＤ／', '　　　　　　　　　／ｉＤ', '　／ｉＤ']

    def get_read_config(self):
        return {
            'encoding': 'cp932',
            'skiprows': 1,
            'skipfooter': 3,
            'engine': 'python'
        }

    def process_data(self, df, account):
        df = df.iloc[:, :3]
        df.columns = ['date', 'destination', 'amount']
        df = df.loc[df['date'] != 'ＲＡ　ＪＩＴＨ　様']
        df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d').dt.date
        df = self.set_default_props(df, account)
        df = self.clean_destinations(df, self.cleanable_signatures)
        return df

    def validate_dataframe(self, transactions):
        return super().validate_dataframe(transactions)


class MizuhoBankLoader(BaseLoader, ServiceLoader):
    def __init__(self):
        super().__init__()
        self.cleanable_signatures = []

    def get_read_config(self):
        return {
            'encoding': 'shift-jis',
            'skiprows': 9,
            'engine': 'python'
        }

    def process_data(self, df, account):
        df_income = df[['日付', 'お預入金額', 'お取引内容']]
        df_expense = df[['日付', 'お引出金額', 'お取引内容']]
        df_income.columns = ['date', 'amount', 'destination']
        df_expense.columns = ['date', 'amount', 'destination']
        df_income['date'] = pd.to_datetime(df_income['date'], format='%Y.%m.%d').dt.date
        df_expense['date'] = pd.to_datetime(df_expense['date'], format='%Y.%m.%d').dt.date
        df_expense = self.set_default_props(df_expense, account)
        df_income = self.set_default_props(df_income, account)
        df_expense = self.clean_destinations(df_expense, self.cleanable_signatures)
        df_income = self.clean_destinations(df_income, self.cleanable_signatures)
        df_income = df_income.assign(**{'is_expense': False, 'is_income': True})
        df = pd.concat([df_income, df_expense])
        return df

    def validate_dataframe(self, transactions):
        return super().validate_dataframe(transactions)


class TransactionProcessFactory:
    @staticmethod
    def get_processor(provider):
        if provider == AccountProviders.RAKUTEN.value:
            return RakutenCardLoader()
        elif provider == AccountProviders.EPOS.value:
            return EposCardLoader()
        elif provider == AccountProviders.DOCOMO.value:
            return DocomoCardLoader()
        elif provider == AccountProviders.MIZUHO.value:
            return MizuhoBankLoader()
        else:
            raise ValueError('Unknown source')
