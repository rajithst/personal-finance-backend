import logging
import os
from collections import defaultdict

import numpy as np
from enum import Enum
import pandas as pd
from django.conf import settings

from transactions.models import DestinationMap, ImportRules
from utils.gcs import GCSHandler

NA_TRANSACTION_CATEGORY_ID = 1000
NA_TRANSACTION_SUB_CATEGORY_ID = 1000
OTHER_INCOME_CATEGORY_ID = 10
SAVINGS_CATEGORY_ID = 6
PAYMENT_CATEGORY_ID = 14


class PaymentMethod(Enum):
    RAKUTEN_CARD = 1
    EPOS_CARD = 2
    DOCOMO_CARD = 3
    CASH = 4


class CardTypes(Enum):
    RAKUTEN = 'Rakuten'
    EPOS = 'Epos'
    DOCOMO = 'Docomo'
    CASH = 'Cash'


class DataSource(Enum):
    IMPORT = 1
    MANUAL_ENTRY = 2


class BaseLoader:
    def __init__(self):
        self.bucket_name = settings.BUCKET_NAME
        self.is_dev_env = settings.ENV == 'dev'
        self.blob_handler = None
        if not self.is_dev_env:
            self.blob_handler = GCSHandler()

    def set_default_props(self, df):
        df[['notes', 'alias']] = len(df.index) * np.nan
        df[['is_payment', 'is_deleted', 'is_saving', 'is_income']] = len(df.index) * False
        df['source'] = DataSource.IMPORT.value
        df['is_expense'] = 1
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

    def get_last_import_date(self, payment_method):
        last_import_date = None
        import_rule = ImportRules.objects.filter(source=payment_method).first()
        if import_rule:
            last_import_date = import_rule.last_import_date
        return last_import_date

    def get_files(self, target_path: str):
        if self.is_dev_env:
            data_path = os.path.join(settings.MEDIA_ROOT, target_path)
            files = os.listdir(data_path)
        else:
            files = self.blob_handler.list_files(bucket_name=self.bucket_name, prefix=target_path)
        return files

    def get_concat_dataframe(self, results):
        if results:
            transactions = pd.concat(results)
            transactions = transactions.drop_duplicates()
            return transactions
        else:
            columns = ['date', 'destination_original', 'destination', 'amount', 'payment_method_id', 'notes', 'alias', 'is_payment',
                       'is_deleted', 'is_saving', 'is_income', 'source', 'is_expense']
            return pd.DataFrame(columns=columns)


class RakutenCardLoader(BaseLoader):
    def __init__(self):
        super().__init__()
        self.data_path = 'finance/rakuten/'
        self.cleanable_signatures = ['楽天ＳＰ', '/N']
        self.payment_method = PaymentMethod.RAKUTEN_CARD.value

    def import_data(self):
        last_import_date = self.get_last_import_date(self.payment_method)
        files = self.get_files(target_path=self.data_path)
        results = []
        for file in files:
            if self.is_dev_env:
                blob_data = os.path.join(settings.MEDIA_ROOT, self.data_path, file)
            else:
                blob_data = self.blob_handler.get_blob(bucket_name=self.bucket_name, file_name=file)
            df = pd.read_csv(blob_data)
            df = df[['利用日', '利用店名・商品名', '利用金額']]
            df.columns = ['date', 'destination', 'amount']
            df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d').dt.date
            if last_import_date:
                df = df[df['date'] > last_import_date]
            df['payment_method_id'] = self.payment_method
            df = self.set_default_props(df)
            df['destination'] = df['destination'].apply(
                lambda x: self.clean_electronic_signatures(x, self.cleanable_signatures))
            df.assign(destination_original=df.destination)
            results.append(df)
        return self.get_concat_dataframe(results)


class EposCardLoader(BaseLoader):
    def __init__(self):
        super().__init__()
        self.data_path = 'finance/epos/'
        self.cleanable_signatures = ['／Ｎ', '／ＮＦＣ', 'ＡＰ／', '／ＮＦＣ ()', '／ＮＦＣ', '	ＡＰ／']
        self.payment_method = PaymentMethod.EPOS_CARD.value

    def import_data(self):
        last_import_date = self.get_last_import_date(self.payment_method)
        files = self.get_files(target_path=self.data_path)
        results = []
        for file in files:
            if self.is_dev_env:
                blob_data = os.path.join(settings.MEDIA_ROOT, self.data_path, file)
            else:
                blob_data = self.blob_handler.get_blob(bucket_name=self.bucket_name, file_name=file)
            df = pd.read_csv(blob_data, encoding="cp932", skiprows=1, skipfooter=5, engine='python')
            df = df.iloc[:, 1:]
            df = df[['ご利用年月日', 'ご利用場所', 'ご利用金額（キャッシングでは元金になります）']]
            df.columns = ['date', 'destination', 'amount']
            df['date'] = pd.to_datetime(df['date'], format='%Y年%m月%d日').dt.date
            if last_import_date:
                df = df[df['date'] > last_import_date]
            df['payment_method_id'] = self.payment_method
            df = self.set_default_props(df)
            df['destination'] = df['destination'].apply(
                lambda x: self.clean_electronic_signatures(x, self.cleanable_signatures))
            df.assign(destination_original=df.destination)
            results.append(df)
        return self.get_concat_dataframe(results)


class DocomoCardLoader(BaseLoader):
    def __init__(self):
        super().__init__()
        self.data_path = 'finance/docomo/'
        self.cleanable_signatures = ['／ｉＤ', 'ｉＤ／', '　／ｉＤ', 'ｉＤ／']
        self.payment_method = PaymentMethod.DOCOMO_CARD.value

    def import_data(self):
        last_import_date = self.get_last_import_date(self.payment_method)
        files = self.get_files(target_path=self.data_path)
        results = []
        for file in files:
            if self.is_dev_env:
                blob_data = os.path.join(settings.MEDIA_ROOT, self.data_path, file)
            else:
                blob_data = self.blob_handler.get_blob(bucket_name=self.bucket_name, file_name=file)
            df = pd.read_csv(blob_data, encoding="cp932", skiprows=1, skipfooter=3, engine='python')
            df = df.iloc[:, :3]
            df.columns = ['date', 'destination', 'amount']
            df = df.loc[df['date'] != 'ＲＡ　ＪＩＴＨ　様']
            df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d').dt.date
            if last_import_date:
                df = df[df['date'] > last_import_date]
            df['payment_method_id'] = self.payment_method
            df = self.set_default_props(df)
            df['destination'] = df['destination'].apply(
                lambda x: self.clean_electronic_signatures(x, self.cleanable_signatures))
            df.assign(destination_original=df.destination)
            results.append(df)
        return self.get_concat_dataframe(results)


class CashCardLoader(BaseLoader):
    def __init__(self):
        super().__init__()
        self.data_path = 'finance/mizuho/'
        self.cleanable_signatures = []
        self.payment_method = PaymentMethod.CASH.value

    def import_data(self):
        last_import_date = self.get_last_import_date(self.payment_method)
        files = self.get_files(target_path=self.data_path)
        results = []
        for file in files:
            if self.is_dev_env:
                blob_data = os.path.join(settings.MEDIA_ROOT, self.data_path, file)
            else:
                blob_data = self.blob_handler.get_blob(bucket_name=self.bucket_name, file_name=file)
            df = pd.read_csv(blob_data, encoding='shift-jis', skiprows=9, engine='python')
            df_income = df[['日付', 'お預入金額', 'お取引内容']]
            df_expense = df[['日付', 'お引出金額', 'お取引内容']]
            df_income.columns = ['date', 'amount', 'destination']
            df_expense.columns = ['date', 'amount', 'destination']
            df.assign(destination_original=df.destination)
            df_expense = self.set_default_props(df_expense)
            df_income = self.set_default_props(df_income)
            df_income['is_expense'] = 0
            df_income['is_income'] = 1
            df = pd.concat([df_income, df_expense])
            df['payment_method_id'] = self.payment_method
            df['date'] = pd.to_datetime(df['date'], format='%Y.%m.%d').dt.date
            if last_import_date:
                df = df[df['date'] > last_import_date]
            results.append(df)
        return self.get_concat_dataframe(results)


class CardLoader:
    def get_payee_map(self):
        queryset = DestinationMap.objects.all()
        payee_maps = list(queryset.values())
        if payee_maps:
            payee_maps = pd.DataFrame(payee_maps)
            payee_maps = payee_maps[['destination', 'destination_original', 'destination_eng', 'keywords', 'category_id', 'subcategory_id']]
            payee_maps.columns = ['destination', 'destination_original', 'alias_map', 'category_id', 'subcategory_id', 'keywords']
            return payee_maps
        return pd.DataFrame(columns=['destination', 'destination_original', 'alias_map', 'category_id', 'subcategory_id', 'keywords'])

    def _inverse_dict(self, d):
        inverted = {}
        for key, values in d.items():
            for value in values:
                inverted.setdefault(value, key)
        return inverted

    def get_rewrite_rules(self, rewrite_keywords):
        contains_categories = defaultdict(list)

        for rule in rewrite_keywords:
            destination = rule[0]
            keywords = [keyword.strip() for keyword in rule[1].split(',') if keyword.strip()]
            contains_categories[destination].extend(keywords)
        contains_categories = dict(contains_categories)
        return self._inverse_dict(contains_categories)

    def process(self):
        rakuten_importer = CardLoaderFactory.create(CardTypes.RAKUTEN.value)
        rakuten_data = rakuten_importer.import_data()

        epos_importer = CardLoaderFactory.create(CardTypes.EPOS.value)
        epos_data = epos_importer.import_data()

        docomo_importer = CardLoaderFactory.create(CardTypes.DOCOMO.value)
        docomo_data = docomo_importer.import_data()

        cash_importer = CardLoaderFactory.create(CardTypes.CASH.value)
        cash_data = cash_importer.import_data()

        rakuten_new_import_date = None if rakuten_data.empty else rakuten_data['date'].max()
        epos_new_import_date = None if epos_data.empty else epos_data['date'].max()
        docomo_new_import_date = None if docomo_data.empty else docomo_data['date'].max()
        cash_new_import_date = None if cash_data.empty else cash_data['date'].max()
        import_rules = {
            PaymentMethod.RAKUTEN_CARD.value: rakuten_new_import_date,
            PaymentMethod.EPOS_CARD.value: epos_new_import_date,
            PaymentMethod.DOCOMO_CARD.value: docomo_new_import_date,
            PaymentMethod.CASH.value: cash_new_import_date
        }

        all_transactions = pd.concat([rakuten_data, epos_data, docomo_data, cash_data])
        if not all_transactions.empty:
            all_transactions.sort_values(by='date', ascending=True, inplace=True)
            all_transactions.reset_index(drop=True, inplace=True)
            all_transactions['notes'] = all_transactions['notes'].replace({np.nan: None})
            all_transactions['amount'] = all_transactions['amount'].round(2)
            all_transactions['payment_method_id'] = all_transactions['payment_method_id'].astype(int)
            payee_maps = self.get_payee_map()
            rewrite_keywords = payee_maps[['destination_original', 'keywords']].values.tolist()
            rewrite_rules = self.get_rewrite_rules(rewrite_keywords)
            for field in rewrite_rules:
                all_transactions.loc[all_transactions['destination'].str.contains(field, regex=False), 'alias'] = \
                    rewrite_rules[field]
                all_transactions.loc[all_transactions['destination'].str.contains(field, regex=False), 'destination'] = \
                    rewrite_rules[field]

            all_incomes = all_transactions[all_transactions['is_income'] == 1]
            all_incomes['category_id'] = OTHER_INCOME_CATEGORY_ID
            #TODO update import process according to destination_original field
            all_expenses = all_transactions[all_transactions['is_expense'] == 1]
            all_expenses = pd.merge(all_expenses, payee_maps, on=['destination'], how='left')
            all_expenses.loc[all_expenses['alias_map'].isnull() & all_expenses['alias'].notnull(), 'alias_map'] = \
                all_expenses['alias']
            all_expenses = all_expenses.drop(columns=['alias', 'is_income'])
            all_expenses = all_expenses.rename(columns={'alias_map': 'alias'})
            all_expenses['alias'] = all_expenses['alias'].replace({np.nan: None})

            all_expenses['category_id'] = all_expenses['category_id'].replace(
                {np.nan: NA_TRANSACTION_CATEGORY_ID}).astype(
                int)
            all_expenses['subcategory_id'] = all_expenses['subcategory_id'].replace(
                {np.nan: NA_TRANSACTION_SUB_CATEGORY_ID}).astype(int)
            all_expenses['is_saving'] = all_expenses['category_id'] == SAVINGS_CATEGORY_ID
            all_expenses['is_payment'] = all_expenses['category_id'] == PAYMENT_CATEGORY_ID
            logging.info('All expenses processed')
            return all_expenses.to_dict('records'), all_incomes.to_dict('records'), import_rules
        else:
            return None, None, None


class CardLoaderFactory(object):

    @staticmethod
    def create(card_type):
        if card_type == CardTypes.RAKUTEN.value:
            return RakutenCardLoader()
        elif card_type == CardTypes.EPOS.value:
            return EposCardLoader()
        elif card_type == CardTypes.DOCOMO.value:
            return DocomoCardLoader()
        elif card_type == CardTypes.CASH.value:
            return CashCardLoader()
        else:
            raise ValueError('Unknown card')
