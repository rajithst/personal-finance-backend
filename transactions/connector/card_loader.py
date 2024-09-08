import logging
import os
from collections import defaultdict
from datetime import datetime
import numpy as np
import pandas as pd
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

from transactions.common.enums import DataSource, AccountTypes, AccountProviders
from transactions.common.transaction_const import SAVINGS_CATEGORY_TYPE, PAYMENT_CATEGORY_TYPE, INCOME_CATEGORY_TYPE, \
    EXPENSE_CATEGORY_TYPE
from transactions.models import DestinationMap, TransactionCategory, TransactionSubCategory, Account
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

    def get_files(self, target_path: str):
        if self.is_dev_env:
            data_path = os.path.join(settings.MEDIA_ROOT, target_path)
            files = os.listdir(data_path)
        else:
            files = self.blob_handler.list_files(bucket_name=self.bucket_name, prefix=target_path)
        return files

    def read_single_file(self, file_name, read_config):
        if self.is_dev_env:
            blob_data = os.path.join(settings.MEDIA_ROOT, file_name)
        else:
            blob_data = self.blob_handler.get_blob(bucket_name=self.bucket_name, file_name=file_name)
        df = pd.read_csv(blob_data, **read_config)
        return df

    def read_all_files(self, target_path, read_config):
        files = self.get_files(target_path=target_path)
        results = []
        for file in files:
            if self.is_dev_env:
                blob_data = file
            else:
                blob_data = self.blob_handler.get_blob(bucket_name=self.bucket_name, file_name=file)
            df = pd.read_csv(blob_data, **read_config)
            results.append(df)
        if results:
            return pd.concat(results)
        else:
            return None

    def validate_dataframe(self, transactions):
        if transactions:
            transactions = transactions.drop_duplicates()
            return transactions
        else:
            columns = ['date', 'destination_original', 'destination', 'amount', 'account_id', 'notes', 'alias',
                       'is_payment',
                       'is_deleted', 'is_saving', 'is_income', 'source', 'is_expense']
            return pd.DataFrame(columns=columns)

    def clean_destinations(self, df, cleanable_signatures):
        try:
            df['destination'] = df['destination'].apply(
                lambda x: self.clean_electronic_signatures(x, cleanable_signatures))
            df['destination_original'] = df.apply(lambda x: x['destination'].strip() if x['destination'] else x['destination'], axis=1)
            return df
        except Exception as e:
            logging.exception(e)


class RakutenCardLoader(BaseLoader):
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


class EposCardLoader(BaseLoader):
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


class DocomoCardLoader(BaseLoader):
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


class MizuhoBankLoader(BaseLoader):
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


class ProcessFactory:
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


class ServiceImporter(BaseLoader):

    def import_data(self, user, account, file_names=None):
        if not user:
            raise AuthenticationFailed('Unauthenticated import.')
        data_path = f'user_{user.id}/finance/acc_{account.id}/'
        target_path = data_path
        processor = ProcessFactory.get_processor(account.provider)
        if file_names:
            formatted_dfs = []
            for file_name in file_names:
                df = self.read_single_file(file_name, read_config=processor.get_read_config())
                formatted_data = processor.process_data(df, account)
                formatted_dfs.append(formatted_data)
            processed_data = pd.concat(formatted_dfs, ignore_index=True)
        else:
            processed_data = self.read_all_files(target_path, read_config=processor.get_read_config())
        if processed_data is not None and not processed_data.empty:
            return processed_data
        return self.validate_dataframe(processed_data)


class CardLoader:
    def __init__(self, request_user, account, drop_duplicates=True, import_from_last_date=None, start_date=None, end_date=None, file_names=None):
        if not request_user or not account:
            raise ValueError('request_user must be set. Account  should be set.')
        self.file_names = file_names
        self.request_user = request_user
        self.account = account
        self.drop_duplicates = drop_duplicates
        self.import_from_last_date = import_from_last_date
        self.start_date = start_date
        self.end_date = end_date
        self.savings_category_id = None
        self.income_category_id = None
        self.payment_category_id = None
        self.expense_category_id = None
        self.na_category_id = None
        self.na_sub_category_id = None
        self.get_user_settings()

    def get_user_settings(self):
        category_queryset = TransactionCategory.objects.filter(user_id=self.request_user.id)
        subcategory_queryset = TransactionSubCategory.objects.filter(user_id=self.request_user.id)
        self.savings_category_id = category_queryset.filter(category_type=SAVINGS_CATEGORY_TYPE).first().id
        self.income_category_id = category_queryset.filter(category_type=INCOME_CATEGORY_TYPE).first().id
        self.payment_category_id = category_queryset.filter(category_type=PAYMENT_CATEGORY_TYPE).first().id
        self.na_category_id = category_queryset.filter(category='N/A').first().id
        self.na_sub_category_id = subcategory_queryset.filter(name='N/A').first().id

    def get_payee_map(self):
        queryset = DestinationMap.objects.filter(user_id=self.request_user.id).all()
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
        transaction_data = ServiceImporter().import_data(self.request_user, self.account, self.file_names)
        if int(self.import_from_last_date):
            last_import_date = self.account.last_import_date
            transaction_data = transaction_data[transaction_data['date'] > last_import_date.date()]
        else:
            if self.start_date:
                transaction_data = transaction_data[transaction_data['date'] >= datetime.strptime(self.start_date,'%Y-%m-%d').date()]
            if self.end_date:
                transaction_data = transaction_data[transaction_data['date'] <= datetime.strptime(self.end_date,'%Y-%m-%d').date()]
        if self.drop_duplicates:
            transaction_data = transaction_data.drop_duplicates()

        if not transaction_data.empty:
            transaction_data.sort_values(by='date', ascending=True, inplace=True)
            transaction_data.reset_index(drop=True, inplace=True)
            transaction_data['notes'] = transaction_data['notes'].replace({np.nan: None})
            transaction_data['amount'] = transaction_data['amount'].round(2)
            transaction_data['account_id'] = transaction_data['account_id'].astype(int)
            transaction_data['user_id'] = self.request_user.id
            payee_maps = self.get_payee_map()
            rewrite_keywords = payee_maps[['destination', 'keywords']].values.tolist()
            rewrite_rules = self.get_rewrite_rules(rewrite_keywords)
            for field in rewrite_rules:
                transaction_data.loc[transaction_data['destination'].str.contains(field, regex=False), 'alias'] = \
                    rewrite_rules[field]
                transaction_data.loc[transaction_data['destination'].str.contains(field, regex=False), 'destination'] = \
                    rewrite_rules[field]
            existing_payees = payee_maps['destination_original'].unique()
            new_payees = transaction_data[~transaction_data['destination_original'].isin(existing_payees)]
            new_payees = new_payees.drop_duplicates(subset='destination_original', keep="first")
            new_payees = new_payees[['destination', 'destination_original', 'is_income']]
            income_payees = new_payees[new_payees['is_income'] == 1]
            expense_payees = new_payees[new_payees['is_income'] == 0]

            income_payees = income_payees.assign(
                **{'destination_eng': None, 'keywords': None, 'category_id': self.na_category_id,
                   'subcategory_id': self.na_sub_category_id, 'user_id': self.request_user.id,
                   'category_type': INCOME_CATEGORY_TYPE})
            expense_payees = expense_payees.assign(
                **{'destination_eng': None, 'keywords': None, 'category_id': self.na_category_id,
                   'subcategory_id': self.na_sub_category_id, 'user_id': self.request_user.id,
                   'category_type': EXPENSE_CATEGORY_TYPE})
            new_payees = pd.concat([income_payees, expense_payees]).drop(columns=['is_income'])
            try:
                payee_objects = []
                for new_payee in new_payees.to_dict('records'):
                    payee_objects.append(DestinationMap(**new_payee))
                DestinationMap.objects.bulk_create(payee_objects)
                logging.info('new payees imported')
            except Exception as e:
                logging.exception('Error saving new payees')
            payee_maps = payee_maps[['category_id', 'subcategory_id', 'destination', 'alias_map']]

            all_expenses = transaction_data
            all_expenses = pd.merge(all_expenses, payee_maps, on=['destination'], how='left')
            all_expenses.loc[all_expenses['alias_map'].isnull() & all_expenses['alias'].notnull(), 'alias_map'] = \
                all_expenses['alias']
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
            return all_expenses
        else:
            return None

