import logging
import os
from collections import defaultdict

import numpy as np
import pandas as pd
from django.conf import settings

from transactions.common.enums import DataSource, AccountTypes, CardTypes
from transactions.common.transaction_const import SAVINGS_CATEGORY_TYPE, PAYMENT_CATEGORY_TYPE, INCOME_CATEGORY_TYPE
from transactions.models import DestinationMap, ImportRules, TransactionCategory, TransactionSubCategory
from utils.gcs import GCSHandler


class BaseLoader:
    def __init__(self):
        self.bucket_name = settings.BUCKET_NAME
        self.is_dev_env = settings.ENV == 'dev'
        self.blob_handler = None
        if not self.is_dev_env:
            self.blob_handler = GCSHandler()

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
            'account_id': account
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

    def get_last_import_date(self, account):
        last_import_date = None
        import_rule = ImportRules.objects.filter(source=account).first()
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
            columns = ['date', 'destination_original', 'destination', 'amount', 'account_id', 'notes', 'alias',
                       'is_payment',
                       'is_deleted', 'is_saving', 'is_income', 'source', 'is_expense']
            return pd.DataFrame(columns=columns)

    def clean_destinations(self, df, cleanable_signatures):
        df['destination'] = df['destination'].apply(
            lambda x: self.clean_electronic_signatures(x, cleanable_signatures))
        df.loc[:, 'destination_original'] = df.loc[:, 'destination']
        return df


class RakutenCardLoader(BaseLoader):
    def __init__(self):
        super().__init__()
        self.data_path = 'finance/rakuten/'
        self.cleanable_signatures = ['楽天ＳＰ', '/N']
        self.account = AccountTypes.RAKUTEN_CARD.value

    def import_data(self):
        last_import_date = self.get_last_import_date(self.account)
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
            df = self.set_default_props(df, self.account)
            df = self.clean_destinations(df, self.cleanable_signatures)
            results.append(df)
        return self.get_concat_dataframe(results)


class EposCardLoader(BaseLoader):
    def __init__(self):
        super().__init__()
        self.data_path = 'finance/epos/'
        self.cleanable_signatures = ['／Ｎ', '／ＮＦＣ', 'ＡＰ／', '／ＮＦＣ ()', '／ＮＦＣ', '	ＡＰ／']
        self.account = AccountTypes.EPOS_CARD.value

    def import_data(self):
        last_import_date = self.get_last_import_date(self.account)
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
            df = self.set_default_props(df, self.account)
            df = self.clean_destinations(df, self.cleanable_signatures)
            results.append(df)
        return self.get_concat_dataframe(results)


class DocomoCardLoader(BaseLoader):
    def __init__(self):
        super().__init__()
        self.data_path = 'finance/docomo/'
        self.cleanable_signatures = ['／ｉＤ', 'ｉＤ／', '　／ｉＤ', 'ｉＤ／', '　　　　　　　　　／ｉＤ', '　／ｉＤ']
        self.account = AccountTypes.DOCOMO_CARD.value

    def import_data(self):
        last_import_date = self.get_last_import_date(self.account)
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
            df = self.set_default_props(df, self.account)
            df = self.clean_destinations(df, self.cleanable_signatures)
            results.append(df)
        return self.get_concat_dataframe(results)


class CashCardLoader(BaseLoader):
    def __init__(self):
        super().__init__()
        self.data_path = 'finance/mizuho/'
        self.cleanable_signatures = []
        self.account = AccountTypes.CASH.value

    def import_data(self):
        last_import_date = self.get_last_import_date(self.account)
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
            df_expense = self.clean_destinations(df_expense, self.cleanable_signatures)
            df_income = self.clean_destinations(df_income, self.cleanable_signatures)
            df_expense = self.set_default_props(df_expense, self.account)
            df_income = self.set_default_props(df_income, self.account)
            df_income = df_income.assign(**{'is_expense': False, 'is_income': True})
            df = pd.concat([df_income, df_expense])
            df['date'] = pd.to_datetime(df['date'], format='%Y.%m.%d').dt.date
            if last_import_date:
                df = df[df['date'] > last_import_date]
            results.append(df)
        return self.get_concat_dataframe(results)


class CardLoader:
    def __init__(self, request_user_id):
        if not request_user_id:
            raise ValueError('request_user_id must be set. Abort import.')
        self.request_user_id = request_user_id
        self.savings_category_id = None
        self.income_category_id = None
        self.payment_category_id = None
        self.na_category_id = None
        self.na_sub_category_id = None
        self.get_user_settings()

    def get_user_settings(self):
        category_queryset = TransactionCategory.objects.filter(user_id=self.request_user_id)
        subcategory_queryset = TransactionSubCategory.objects.filter(user_id=self.request_user_id)
        self.savings_category_id = category_queryset.filter(category_type=SAVINGS_CATEGORY_TYPE).first().id
        self.income_category_id = category_queryset.filter(category_type=INCOME_CATEGORY_TYPE).first().id
        self.payment_category_id = category_queryset.filter(category_type=PAYMENT_CATEGORY_TYPE).first().id
        self.na_category_id = category_queryset.filter(category='N/A').first().id
        self.na_sub_category_id = subcategory_queryset.filter(name='N/A').first().id

    def get_payee_map(self):
        queryset = DestinationMap.objects.filter(user_id=self.request_user_id).all()
        payee_maps = list(queryset.values())
        if payee_maps:
            payee_maps = pd.DataFrame(payee_maps)
            payee_maps = payee_maps[
                ['destination', 'destination_original', 'destination_eng', 'keywords', 'category_id', 'subcategory_id']]
            payee_maps.columns = ['destination', 'destination_original', 'alias_map', 'keywords', 'category_id',
                                  'subcategory_id']
            payee_maps.keywords = payee_maps.keywords.fillna('')
            payee_maps.destination_original = payee_maps.destination_original.fillna('')
            payee_maps['keywords'] = payee_maps['keywords'].str.cat(payee_maps['destination_original'],
                                                                    sep=",").str.strip(',')
            return payee_maps
        return pd.DataFrame(
            columns=['destination', 'destination_original', 'alias_map', 'category_id', 'subcategory_id', 'keywords'])

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
            AccountTypes.RAKUTEN_CARD.value: rakuten_new_import_date,
            AccountTypes.EPOS_CARD.value: epos_new_import_date,
            AccountTypes.DOCOMO_CARD.value: docomo_new_import_date,
            AccountTypes.CASH.value: cash_new_import_date
        }

        all_transactions = pd.concat([rakuten_data, epos_data, docomo_data, cash_data])
        if not all_transactions.empty:
            all_transactions.sort_values(by='date', ascending=True, inplace=True)
            all_transactions.reset_index(drop=True, inplace=True)
            all_transactions['notes'] = all_transactions['notes'].replace({np.nan: None})
            all_transactions['amount'] = all_transactions['amount'].round(2)
            all_transactions['account_id'] = all_transactions['account_id'].astype(int)
            all_transactions['user_id'] = self.request_user_id
            payee_maps = self.get_payee_map()
            rewrite_keywords = payee_maps[['destination', 'keywords']].values.tolist()
            rewrite_rules = self.get_rewrite_rules(rewrite_keywords)
            for field in rewrite_rules:
                all_transactions.loc[all_transactions['destination'].str.contains(field, regex=False), 'alias'] = \
                    rewrite_rules[field]
                all_transactions.loc[all_transactions['destination'].str.contains(field, regex=False), 'destination'] = \
                    rewrite_rules[field]
            existing_payees = payee_maps['destination_original'].unique()
            new_payees = all_transactions[~all_transactions['destination_original'].isin(existing_payees)]
            new_payees = new_payees.drop_duplicates(subset='destination_original', keep="first")
            new_payees = new_payees[['destination', 'destination_original']]
            new_payees = new_payees.assign(
                **{'destination_eng': None, 'keywords': None, 'category_id': self.na_category_id,
                   'subcategory_id': self.na_sub_category_id, 'user_id': self.request_user_id})

            try:
                payee_objects = []
                for new_payee in new_payees.to_dict('records'):
                    payee_objects.append(DestinationMap(**new_payee))
                DestinationMap.objects.bulk_create(payee_objects)
                logging.info('new payees imported')
            except Exception as e:
                logging.exception('Error saving new payees')
            payee_maps = payee_maps[['category_id', 'subcategory_id', 'destination', 'alias_map']]

            #all_incomes = all_transactions[all_transactions['is_income'] == 1]
            #all_incomes['category_id'] = OTHER_INCOME_CATEGORY_ID

            #all_expenses = all_transactions[all_transactions['is_expense'] == 1]
            all_expenses = all_transactions
            all_expenses = pd.merge(all_expenses, payee_maps, on=['destination'], how='left')
            all_expenses.loc[all_expenses['alias_map'].isnull() & all_expenses['alias'].notnull(), 'alias_map'] = \
                all_expenses['alias']
            #all_expenses = all_expenses.drop(columns=['alias', 'is_income'])
            all_expenses = all_expenses.drop(columns=['alias'])
            all_expenses = all_expenses.rename(columns={'alias_map': 'alias'})
            all_expenses['alias'] = all_expenses['alias'].replace({np.nan: None})
            all_expenses.loc[all_expenses['is_income'], 'category_id'] = self.income_category_id
            all_expenses['category_id'] = all_expenses['category_id'].replace(
                {np.nan: self.na_category_id}).astype(
                int)
            all_expenses['subcategory_id'] = all_expenses['subcategory_id'].replace(
                {np.nan: self.na_sub_category_id}).astype(int)
            all_expenses['is_saving'] = all_expenses['category_id'] == self.savings_category_id
            all_expenses['is_payment'] = all_expenses['category_id'] == self.payment_category_id
            logging.info('All expenses processed')
            return all_expenses.to_dict('records'), import_rules
        else:
            return None, None


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
