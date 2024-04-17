import os
from pprint import pprint

import numpy as np
from django.conf import settings
from enum import Enum
import pandas as pd

from transactions.models import Transaction, DestinationMap

CONTAINS_CATEGORIES = {
    'Softbank': ['ソフトバンク'],
    'Spotify': ['SPOTIFY'],
    'SevenEleven': ['セブン－イレブン', 'セブンイレブン'],
    'Lawson': ['ロ―ソン', 'ローソン', 'ロ－ソン'],
    'Family Mart': ['フアミリ―マ―ト', 'ファミリーマート'],
    'Toyota Rent a Car': ['トヨタレンタリース', 'ﾄﾖﾀﾚﾝﾀﾘｰｽ'],
    'MEGA Donqui': ['ＭＥＧＡドン・キ', 'メガドンキ'],
    'Starbucks': ['ｽﾀ-ﾊﾞﾂｸｽ', 'スタ－バツクス'],
    'Daiso': ['ダイソー', 'ＤＡＩＳＯ', 'ダイソ－'],
    'Seria': ['セリア'],
    'Gyomu Super': ['ギヨウムス－パ－', '業務ス－パ－', 'ｷﾞﾖｳﾑｽ-ﾊﾟ-'],
    'HAC Drug Store': ['ハツクドラツグ', 'ハックドラッグ'],
    'Uber Eats': ['UBER *EATS HELP.UBER利用国NLD', 'ＵＢＥＲ　ＥＡＴＳ', 'UBER   *EATS', 'UBER *EATS (HELP.UBER.COM)',
                  'UBER   *EATS利用国NLD', 'UBER   *EATS利用国USA', 'UBER *EATS HELP.UBER利用国NLD', 'UBER   *EATS利用国NLD',
                  'UBER * EATS PENDING (HELP.UBER.COM)', 'UBER *EATS HELP.UBER.COM (HELP.UBER.COM)'],
    'Uber Pass': ['UBER *PASS HELP.UBER.COM (HELP.UBER.COM)', 'UBER *ONE HELP.UBER.COM (HELP.UBER.COM)'],
    'ATM Withdrawal': ['ＡＴＭ'],
    'Cash Payments': ['ＪＣＢデビット'],
    'Second Street': ['セカンドストリート'],
    'TOKYU SC': ['クトウキユウ　エスシ－'],
    'CREATE': ['クリエイト　エス・ディーアプリ', 'クリエイトエスデイ－', 'クリエイト', 'ｸﾘｴｲﾄ'],
    'Appolo Station': ['イデミツ（アポロステーション', 'アポロステ－シヨン', 'イデミツ（アポロ／シェル'],
    'PASMO': ['モバイルＰＡＳＭＯチャージ', 'モバイルパスモチヤ－ジ'],
    'CONAN': ['ホームセンターコーナン　アプリ', 'コ－ナン商事', 'コ－ナン　コウホクセンタ－ミナミテン'],
    'Netflix': ['ＮＥＴＦＬＩＸ．ＣＯＭ', 'ネツトフリツクス'],
    'ETC': ['ＥＴＣ'],
    'McDonald\'s': ['マクドナルド']
}

NA_TRANSACTION_CATEGORY_ID = 1000
NA_TRANSACTION_SUB_CATEGORY_ID = 1000
OTHER_INCOME_CATEGORY_ID = 10


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


def clean_electronic_signatures(value, signatures):
    if value:
        new_value = value.strip()
        for i in signatures:
            if value.endswith(i) or value.startswith(i):
                new_value = value.replace(i, '')
                new_value = new_value.strip()
        return new_value
    return value


def inverse_dict(d):
    inverted = {}
    for key, values in d.items():
        for value in values:
            inverted.setdefault(value, key)
    return inverted


def remap_contains_destinations(df):
    CONTAINS_CATEGORIES_REV = inverse_dict(CONTAINS_CATEGORIES)
    for field in CONTAINS_CATEGORIES_REV:
        df.loc[df['destination'].str.contains(field), 'alias'] = CONTAINS_CATEGORIES_REV[field]
        df.loc[df['destination'].str.contains(field), 'destination'] = CONTAINS_CATEGORIES_REV[field]
        df.loc[df['destination'] == field, 'alias'] = CONTAINS_CATEGORIES_REV[field]
        df.loc[df['destination'] == field, 'destination'] = CONTAINS_CATEGORIES_REV[field]
    return df


def set_default_props(df):
    df[['notes', 'alias']] = len(df.index) * np.nan
    df[['is_payment', 'is_deleted', 'is_saving', 'is_income']] = len(df.index) * False
    df['source'] = DataSource.IMPORT.value
    df['is_expense'] = 1
    df = df[df.date.isnull() == False]
    df = df[df.amount.isnull() == False]
    return df


class RakutenCardLoader:
    def __init__(self):
        self.data_path = os.path.join(settings.MEDIA_ROOT, 'rakuten')
        self.cleanable_signatures = ['楽天ＳＰ', '/N']

    def import_data(self):
        files = os.listdir(self.data_path)
        # TODO change only load the latest file, for now load all files
        results = []
        for file in files:
            file_path = os.path.join(self.data_path, file)
            df = pd.read_csv(file_path)
            df = df[['利用日', '利用店名・商品名', '利用金額']]
            df.columns = ['date', 'destination', 'amount']
            df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d').dt.date
            df['payment_method'] = PaymentMethod.RAKUTEN_CARD.value
            df = set_default_props(df)
            df['destination'] = df['destination'].apply(
                lambda x: clean_electronic_signatures(x, self.cleanable_signatures))
            df = remap_contains_destinations(df)
            results.append(df)
        transactions = pd.concat(results)
        transactions = transactions.drop_duplicates()
        return transactions


class EposCardLoader:
    def __init__(self):
        self.data_path = os.path.join(settings.MEDIA_ROOT, 'epos')
        self.cleanable_signatures = ['／Ｎ', '／ＮＦＣ', 'ＡＰ／', '／ＮＦＣ ()', '／ＮＦＣ']

    def import_data(self):
        files = os.listdir(self.data_path)
        results = []
        for file in files:
            file_path = os.path.join(self.data_path, file)
            df = pd.read_csv(file_path, encoding="cp932", skiprows=1, skipfooter=5, engine='python')
            df = df.iloc[:, 1:]
            df = df[['ご利用年月日', 'ご利用場所', 'ご利用金額（キャッシングでは元金になります）']]
            df.columns = ['date', 'destination', 'amount']
            df['date'] = pd.to_datetime(df['date'], format='%Y年%m月%d日').dt.date
            df['payment_method'] = PaymentMethod.EPOS_CARD.value
            df = set_default_props(df)
            df['destination'] = df['destination'].apply(
                lambda x: clean_electronic_signatures(x, self.cleanable_signatures))
            df = remap_contains_destinations(df)
            results.append(df)
        transactions = pd.concat(results)
        transactions = transactions.drop_duplicates()
        return transactions


class DocomoCardLoader:
    def __init__(self):
        self.data_path = os.path.join(settings.MEDIA_ROOT, 'dcard')
        self.cleanable_signatures = ['／ｉＤ', 'ｉＤ／', '　／ｉＤ', 'ｉＤ／']

    def import_data(self):
        files = os.listdir(self.data_path)
        results = []
        for file in files:
            file_path = os.path.join(self.data_path, file)
            df = pd.read_csv(file_path, encoding="cp932", skiprows=1, skipfooter=3, engine='python')
            df = df.iloc[:, :3]
            df.columns = ['date', 'destination', 'amount']
            df = df.loc[df['date'] != 'ＲＡ　ＪＩＴＨ　様']
            df['date'] = pd.to_datetime(df['date'], format='%Y/%m/%d').dt.date
            df['payment_method'] = PaymentMethod.DOCOMO_CARD.value
            df = set_default_props(df)
            df['destination'] = df['destination'].apply(
                lambda x: clean_electronic_signatures(x, self.cleanable_signatures))
            df = remap_contains_destinations(df)
            results.append(df)
        transactions = pd.concat(results)
        transactions = transactions.drop_duplicates()
        return transactions


class CashCardLoader:
    def __init__(self):
        self.data_path = os.path.join(settings.MEDIA_ROOT, 'mizuho')
        self.cleanable_signatures = []

    def import_data(self):
        files = os.listdir(self.data_path)
        results = []
        for file in files:
            file_path = os.path.join(self.data_path, file)
            df = pd.read_csv(file_path, encoding='shift-jis', skiprows=9, engine='python')
            df_income = df[['日付', 'お預入金額', 'お取引内容']]
            df_expense = df[['日付', 'お引出金額', 'お取引内容']]
            df_income.columns = ['date', 'amount', 'destination']
            df_expense.columns = ['date', 'amount', 'destination']
            df_expense = set_default_props(df_expense)
            df_income = set_default_props(df_income)
            df_income['is_expense'] = 0
            df_income['is_income'] = 1
            df = pd.concat([df_income, df_expense])
            df['payment_method'] = PaymentMethod.CASH.value
            df['date'] = pd.to_datetime(df['date'], format='%Y.%m.%d').dt.date
            df = remap_contains_destinations(df)
            results.append(df)
        transactions = pd.concat(results)
        transactions = transactions.drop_duplicates()
        return transactions


class CardLoader:
    def get_payee_map(self):
        queryset = DestinationMap.objects.all()
        payee_maps = list(queryset.values())
        if payee_maps:
            payee_maps = pd.DataFrame(payee_maps)
            payee_maps = payee_maps[['destination', 'destination_eng', 'category_id', 'subcategory_id']]
            payee_maps.columns = ['destination', 'alias_map', 'category', 'subcategory']
            return payee_maps
        return pd.DataFrame(columns=['destination', 'alias_map', 'category', 'subcategory'])

    def process(self):
        rakuten_importer = CardLoaderFactory.create(CardTypes.RAKUTEN.value)
        rakuten_data = rakuten_importer.import_data()

        epos_importer = CardLoaderFactory.create(CardTypes.EPOS.value)
        epos_data = epos_importer.import_data()

        docomo_importer = CardLoaderFactory.create(CardTypes.DOCOMO.value)
        docomo_data = docomo_importer.import_data()

        cash_importer = CardLoaderFactory.create(CardTypes.CASH.value)
        cash_data = cash_importer.import_data()

        all_transactions = pd.concat([rakuten_data, epos_data, docomo_data, cash_data])
        all_transactions.sort_values(by='date', ascending=True, inplace=True)
        all_transactions.reset_index(drop=True, inplace=True)
        all_transactions['notes'] = all_transactions['notes'].replace({np.nan: None})
        all_transactions['amount'] = all_transactions['amount'].round(2)
        all_transactions['payment_method'] = all_transactions['payment_method'].astype(int)

        all_incomes = all_transactions[all_transactions['is_income'] == 1]
        all_incomes['category'] = OTHER_INCOME_CATEGORY_ID

        payee_maps = self.get_payee_map()
        all_expenses = all_transactions[all_transactions['is_expense'] == 1]
        all_expenses = pd.merge(all_expenses, payee_maps, on=['destination'], how='left')
        all_expenses.loc[all_expenses['alias_map'].isnull() & all_expenses['alias'].notnull(), 'alias_map'] = all_expenses['alias']
        all_expenses = all_expenses.drop(columns=['alias', 'is_income'])
        all_expenses = all_expenses.rename(columns={'alias_map': 'alias'})
        all_expenses['alias'] = all_expenses['alias'].replace({np.nan: None})

        all_expenses['category'] = all_expenses['category'].replace({np.nan: NA_TRANSACTION_CATEGORY_ID}).astype(
            int)
        all_expenses['subcategory'] = all_expenses['subcategory'].replace(
            {np.nan: NA_TRANSACTION_SUB_CATEGORY_ID}).astype(int)
        return all_expenses, all_incomes


class CardLoaderFactory(object):

    @staticmethod
    def create(card_type, **kwargs):
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