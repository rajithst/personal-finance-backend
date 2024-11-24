import logging
from collections import defaultdict
from datetime import datetime

import numpy as np
import pandas as pd

from oauth.middleware import get_current_user

from transactions.common.transaction_const import INCOME_CATEGORY_TYPE, EXPENSE_CATEGORY_TYPE, SAVINGS_CATEGORY_TYPE, \
    PAYMENT_CATEGORY_TYPE
from transactions.models import Transaction, Account, DestinationMap, TransactionCategory
from transactions.services.card_loaders import TransactionProcessFactory
from utils.import_service_worker import ImportServiceWorker


class TransactionImportService:
    def import_transactions(self, import_params):
        user = get_current_user()
        account_id = import_params['account_id']
        account = Account.objects.filter(id=account_id).first()
        account_processor = TransactionProcessFactory.get_processor(account.provider)
        file_names = import_params.get('files', None)
        import_params['last_import_date'] = account.last_import_date

        service = ImportServiceWorker(account, account_processor)
        transactions = service.load_transactions(file_names)
        transactions = self.get_applicable_transactions(transactions, import_params)
        if transactions.empty:
            return True

        payees = self.get_payee_map()
        rewrite_rules = self.get_rewrite_rules(payees)
        transactions = self.apply_rewrite_rules(transactions, rewrite_rules)
        new_payees = self.find_new_payees(payees, transactions)
        expenses = self.assign_category_ids(payees, transactions)

        if expenses is not None and not expenses.empty:
            last_import_date = expenses['date'].max()
            expense_records = expenses.to_dict('records')
            expense_objects = []
            payee_objects = []

            for new_payee in new_payees.to_dict('records'):
                payee_objects.append(DestinationMap(**new_payee))

            for expense in expense_records:
                expense['user_id'] = user.id
                expense_objects.append(Transaction(**expense))
            try:
                is_transactions_imported = Transaction.objects.bulk_create(expense_objects)
                if is_transactions_imported:
                    Account.objects.filter(id=account_id).update(last_import_date=last_import_date)
                    DestinationMap.objects.bulk_create(payee_objects)
                return is_transactions_imported
            except Exception as e:
                logging.exception('Error importing Expenses objects: %s', e)
                return False

    def get_applicable_transactions(self, transaction_data, import_params):
        import_from_last_date = import_params.get('import_from_last_date', None)
        drop_duplicates = import_params.get('drop_duplicates', None)
        start_date = import_params.get('start_date', None)
        end_date = import_params.get('end_date', None)
        last_import_date = import_params.get('last_import_date', None)
        if import_from_last_date and last_import_date:
            transaction_data = transaction_data[transaction_data['date'] > last_import_date.date()]
        else:
            if start_date:
                transaction_data = transaction_data[
                    transaction_data['date'] >= datetime.strptime(start_date, '%Y-%m-%d').date()]
            if end_date:
                transaction_data = transaction_data[
                    transaction_data['date'] <= datetime.strptime(end_date, '%Y-%m-%d').date()]
        if drop_duplicates:
            transaction_data = transaction_data.drop_duplicates()
        return transaction_data

    def get_payee_map(self):
        queryset = DestinationMap.objects.all()
        payee_maps = list(queryset.values())
        if payee_maps:
            payee_maps = pd.DataFrame(payee_maps)
            payee_maps = payee_maps[
                ['destination', 'destination_original', 'destination_eng', 'keywords', 'category_type', 'category_id',
                 'subcategory_id']]
            payee_maps.columns = ['destination', 'destination_original', 'alias_map', 'keywords', 'category_type',
                                  'category_id',
                                  'subcategory_id']
            payee_maps.keywords = payee_maps.keywords.fillna('')
            payee_maps.destination_original = payee_maps.destination_original.fillna('')
            payee_maps['keywords'] = payee_maps['keywords'].str.cat(payee_maps['destination_original'],
                                                                    sep=",").str.strip(',')
            return payee_maps
        return pd.DataFrame(
            columns=['destination', 'destination_original', 'alias_map', 'category_type', 'category_id',
                     'subcategory_id', 'keywords'])

    def get_rewrite_rules(self, payee_maps):

        def inverse_dict(d):
            inverted = {}
            for key, values in d.items():
                for value in values:
                    inverted.setdefault(value, key)
            return inverted

        rewrite_keywords = payee_maps[['destination', 'keywords']].values.tolist()
        contains_categories = defaultdict(list)

        for rule in rewrite_keywords:
            destination = rule[0]
            keywords = [keyword.strip() for keyword in rule[1].split(',') if keyword.strip()]
            contains_categories[destination].extend(keywords)
        contains_categories = dict(contains_categories)
        return inverse_dict(contains_categories)

    def apply_rewrite_rules(self, transactions, rewrite_rules):
        for field in rewrite_rules:
            transactions.loc[transactions['destination'].str.contains(field, regex=False), 'alias'] = \
                rewrite_rules[field]
            transactions.loc[transactions['destination'].str.contains(field, regex=False), 'destination'] = \
                rewrite_rules[field]
        return transactions

    def find_new_payees(self, payees, transactions):

        existing_payees = payees['destination'].unique()
        current_user = get_current_user()
        new_payees = transactions[~transactions['destination'].isin(existing_payees)]
        new_payees = new_payees.drop_duplicates(subset='destination_original', keep="first")
        new_payees = new_payees[['destination', 'destination_original', 'is_income']]
        income_payees = new_payees[new_payees['is_income'] == 1]
        expense_payees = new_payees[new_payees['is_income'] == 0]

        income_payees = income_payees.assign(
            **{'destination_eng': None, 'keywords': None, 'category_id': None,
               'subcategory_id': None, 'user_id': current_user.id,
               'category_type': INCOME_CATEGORY_TYPE})
        expense_payees = expense_payees.assign(
            **{'destination_eng': None, 'keywords': None, 'category_id': None,
               'subcategory_id': None, 'user_id': current_user.id,
               'category_type': EXPENSE_CATEGORY_TYPE})
        new_payees = pd.concat([income_payees, expense_payees]).drop(columns=['is_income'])
        return new_payees

    def assign_category_ids(self, payees, transactions):

        payee_maps = payees[['category_id', 'subcategory_id', 'destination', 'alias_map', 'category_type']]
        income_category_id = TransactionCategory.objects.filter(category_type=INCOME_CATEGORY_TYPE).first().id
        transactions = pd.merge(transactions, payee_maps, on=['destination'], how='left')
        transactions['category_type'] = pd.to_numeric(transactions['category_type'], errors='coerce')
        transactions.loc[
            transactions['category_type'] == EXPENSE_CATEGORY_TYPE, ['is_expense', 'is_income', 'is_payment',
                                                                     'is_saving']] = [True,
                                                                                      False,
                                                                                      False,
                                                                                      False]
        transactions.loc[
            transactions['category_type'] == INCOME_CATEGORY_TYPE, ['is_expense', 'is_income', 'is_payment',
                                                                    'is_saving']] = [False,
                                                                                     True,
                                                                                     False,
                                                                                     False]
        transactions.loc[
            transactions['category_type'] == SAVINGS_CATEGORY_TYPE, ['is_expense', 'is_income', 'is_payment',
                                                                     'is_saving']] = [True,
                                                                                      False,
                                                                                      False,
                                                                                      True]
        transactions.loc[
            transactions['category_type'] == PAYMENT_CATEGORY_TYPE, ['is_expense', 'is_income', 'is_payment',
                                                                     'is_saving']] = [True,
                                                                                      False,
                                                                                      True,
                                                                                      False]

        transactions.loc[transactions['alias_map'].isnull() & transactions['alias'].notnull(), 'alias_map'] = \
            transactions['alias']

        transactions = transactions.drop(columns=['alias', 'category_type'])
        transactions = transactions.rename(columns={'alias_map': 'alias'})
        transactions['alias'] = transactions['alias'].replace({np.nan: None})
        transactions.loc[transactions['is_income'], 'category_id'] = income_category_id
        transactions['category_id'] = transactions['category_id'].replace({np.nan: None})
        transactions['subcategory_id'] = transactions['subcategory_id'].replace({np.nan: None})
        return transactions
