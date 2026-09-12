import logging

import numpy as np
import pandas as pd

from common.enums import DataSource, AccountProviders
from workflow.contracts.import_workflow_contract import ImportWorkflowContract


class BaseLoader:

    def set_default_props(self, df, account):
        params_dict = {
            'is_payment': False,
            'is_deleted': False,
            'is_saving': False,
            'is_income': False,
            'notes': '',
            'alias': '',
            'is_expense': True,
            'source': DataSource.IMPORT.value,
            'account_id': account.id
        }
        df = df.assign(**params_dict)
        df['amount'] = df['amount'].replace('', np.nan)
        df['amount'] = df['amount'].replace('-', np.nan)
        df['date'] = df['date'].replace('', np.nan)
        df = df.dropna(subset=['date', 'amount'], how='any')
        return df

    def clean_electronic_signatures(self, value, signatures):
        if isinstance(value, str) and value:
            new_value = value.strip()
            changed = True
            while changed:
                changed = False
                for sig in signatures:
                    if not sig:
                        continue
                    if new_value.startswith(sig):
                        new_value = new_value[len(sig):].strip()
                        changed = True
                    if new_value.endswith(sig):
                        new_value = new_value[:-len(sig)].strip()
                        changed = True
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
            if 'destination' in df.columns:
                df['destination'] = df['destination'].apply(
                    lambda x: self.clean_electronic_signatures(x, cleanable_signatures))
                df['destination_original'] = df['destination'].apply(
                    lambda x: x.strip() if isinstance(x, str) else x)
            return df
        except Exception as e:
            logging.exception("Error cleaning destinations: %s", e)
            return df


class RakutenCardLoader(BaseLoader, ImportWorkflowContract):
    def __init__(self):
        super().__init__()
        self.cleanable_signatures = ['楽天ＳＰ', '/N']

    def get_read_config(self):
        return {}

    def get_expected_columns(self):
        return ['利用日', '利用店名・商品名', '利用金額']

    def process_data(self, df, account):
        df = df[self.get_expected_columns()].copy()
        df.columns = ['date', 'destination', 'amount']
        df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d', errors='coerce').dt.date
        df = self.set_default_props(df, account)
        df = self.clean_destinations(df, self.cleanable_signatures)
        return df

    def validate_dataframe(self, transactions):
        return super().validate_dataframe(transactions)


class EposCardLoader(BaseLoader, ImportWorkflowContract):
    def __init__(self):
        super().__init__()
        self.cleanable_signatures = ['／Ｎ', '／ＮＦＣ', 'ＡＰ／', '／ＮＦＣ ()', '／ＮＦＣ', '	ＡＰ／']

    def get_read_config(self):
        return {
            'encoding': 'cp932',
            'engine': 'python'
        }

    def get_expected_columns(self):
        return ['ご利用年月日', 'ご利用場所', 'ご利用金額（キャッシングでは元金になります）']

    def process_data(self, df, account):
        df = df.iloc[:, 1:].copy()
        df = df[self.get_expected_columns()].copy()
        df.columns = ['date', 'destination', 'amount']
        df['date'] = pd.to_datetime(df['date'], format='%Y年%m月%d日', errors='coerce').dt.date
        df = self.set_default_props(df, account)
        df = self.clean_destinations(df, self.cleanable_signatures)
        return df

    def validate_dataframe(self, transactions):
        return super().validate_dataframe(transactions)


class DocomoCardLoader(BaseLoader, ImportWorkflowContract):
    def __init__(self):
        super().__init__()
        self.cleanable_signatures = ['／ｉＤ', 'ｉＤ／', '　／ｉＤ', 'ｉＤ／', '　　　　　　　　　／ｉＤ', '　／ｉＤ']

    def get_read_config(self):
        return {
            'encoding': 'cp932',
            'engine': 'python',
            'skiprows': 1,  # force loading by skipping rows without finding target columns
            'header': None
        }

    def get_expected_columns(self):
        return []

    def process_data(self, df, account):
        rows, columns = df.shape
        df.columns = ['col' + str(i) for i in range(columns)]
        df = df.iloc[:, :3].copy()
        df.columns = ['date', 'destination', 'amount']
        df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d', errors='coerce').dt.date
        df = self.set_default_props(df, account)
        df = self.clean_destinations(df, self.cleanable_signatures)
        return df

    def validate_dataframe(self, transactions):
        return super().validate_dataframe(transactions)


class MizuhoBankLoader(BaseLoader, ImportWorkflowContract):
    def __init__(self):
        super().__init__()
        self.cleanable_signatures = []

    def get_read_config(self):
        return {
            'encoding': 'shift-jis',
            'engine': 'python'
        }

    def _get_income_columns(self):
        return ['日付', 'お預入金額', 'お取引内容']

    def _get_expense_columns(self):
        return ['日付', 'お引出金額', 'お取引内容']

    def get_expected_columns(self):
        return list(set(self._get_income_columns() + self._get_expense_columns()))

    def process_data(self, df, account):
        df_income = df[self._get_income_columns()].copy()
        df_expense = df[self._get_expense_columns()].copy()
        df_income.columns = ['date', 'amount', 'destination']
        df_expense.columns = ['date', 'amount', 'destination']
        df_income['date'] = pd.to_datetime(df_income['date'], format='%Y.%m.%d', errors='coerce').dt.date
        df_expense['date'] = pd.to_datetime(df_expense['date'], format='%Y.%m.%d', errors='coerce').dt.date
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
