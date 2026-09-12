import logging
from collections import defaultdict
from datetime import datetime

import numpy as np
import pandas as pd
from django.db import transaction
from rest_framework.exceptions import ValidationError

from accounts.models import Account
from common.enums import WorkflowContextType
from common.transaction_const import INCOME_CATEGORY_TYPE, EXPENSE_CATEGORY_TYPE, SAVINGS_CATEGORY_TYPE, \
    PAYMENT_CATEGORY_TYPE
from finance.categories.models import TransactionCategory
from finance.payees.models import DestinationMap
from finance.transactions.models import Transaction
from finance.transactions.services.card_loaders import TransactionProcessFactory
from finance.transactions.validators.import_validator import ImportParamsValidator
from finance.transactions.validators.upload_validator import UploadParamsValidator
from oauth.middleware import get_current_user
from workflow.import_workflow import ImportCsvWorkflow
from workflow.providers.storage_backend_provider import StorageBackendProvider
from workflow.upload_workflow import UploadWorkflow

logger = logging.getLogger(__name__)


class TransactionImportService:
    def __init__(self, transaction_process_factory=None, storage_factory=None, import_workflow=None,
                 upload_workflow=None):
        self.transaction_process_factory = transaction_process_factory or TransactionProcessFactory
        self.storage_factory = storage_factory or StorageBackendProvider
        self.import_workflow = import_workflow or ImportCsvWorkflow
        self.upload_workflow = upload_workflow or UploadWorkflow

    def import_transactions(self, import_params):
        """
        Imports the transactions from the provided files.

        Args:
            import_params (dict): The import parameters.

        Returns:
            bool: The result of the import.
        """

        ImportParamsValidator.validate(import_params)
        account = self.get_account_from_id(import_params['account_id'])
        if not account:
            raise ValidationError({"account_id": "Invalid account ID."})
        import_params['last_import_date'] = account.last_import_date
        account_processor = self.transaction_process_factory.get_processor(account.provider)
        service = self.import_workflow(account, account_processor)
        transactions = service.import_data_from_files(WorkflowContextType.TRANSACTION_FILES,
                                                      import_params.get('files', None))
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

            user = get_current_user()
            user_id = getattr(user, 'id', None)
            for expense in expense_records:
                expense['user_id'] = user_id
                expense_objects.append(Transaction(**expense))
            try:
                with transaction.atomic():
                    is_transactions_imported = Transaction.objects.bulk_create(expense_objects)
                    if is_transactions_imported:
                        Account.objects.filter(id=account.id).update(last_import_date=last_import_date)
                        if payee_objects:
                            DestinationMap.objects.bulk_create(payee_objects)
                return is_transactions_imported
            except Exception as e:
                logger.exception('Error importing Expenses objects: %s', e)
                return False
        return None

    def upload_transaction_files(self, upload_params):
        """
        Uploads the transaction files.

        Args:
            upload_params (dict): The upload parameters.

        Returns:
            list: The uploaded files.
        """
        try:
            UploadParamsValidator.validate(upload_params)
            account = self.get_account_from_id(upload_params['account_id'])
            service = self.upload_workflow(account)
            uploaded_files = service.upload_files(WorkflowContextType.TRANSACTION_FILES, upload_params['upload_files'])
            return uploaded_files
        except Exception as e:
            logger.error(f"Error uploading purchase files: {e}")
            raise e

    def get_account_from_id(self, account_id):
        """
        Gets the account from the provided account ID.

        Args:
            account_id (int): The account ID.

        Returns:
            Account: The account.
        """
        account = Account.objects.filter(id=account_id).first()
        return account

    def get_applicable_transactions(self, transaction_data, import_params):
        """
        Gets the applicable transactions.

        Args:
            transaction_data (DataFrame): The transaction data.
            import_params (dict): The import parameters.

        Returns:
            DataFrame: The applicable transactions.
        """
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
        """
        Gets the payee map.

        Returns:
            DataFrame: The payee map.
        """
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
        """
        Gets the rewrite rules.

        Args:
            payee_maps (DataFrame): The payee maps.

        Returns:
            dict: The rewrite rules.
        """

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

        """
        Finds the new payees.

        Args:
            payees (DataFrame): The payees.
            transactions (DataFrame): The transactions.

        Returns:
            DataFrame: The new payees.
        """

        existing_payees = payees['destination'].dropna().unique()
        current_user = get_current_user()
        user_id = getattr(current_user, 'id', None)
        new_payees = transactions[~transactions['destination'].isin(existing_payees)].copy()
        new_payees = new_payees[new_payees['destination'].notna() & (new_payees['destination'].astype(str).str.strip() != '')]
        new_payees = new_payees.drop_duplicates(subset='destination', keep="first")
        new_payees = new_payees[['destination', 'destination_original', 'is_income']]
        income_payees = new_payees[new_payees['is_income'] == 1]
        expense_payees = new_payees[new_payees['is_income'] == 0]

        income_payees = income_payees.assign(
            **{'destination_eng': None, 'keywords': None, 'category_id': None,
               'subcategory_id': None, 'user_id': user_id,
               'category_type': INCOME_CATEGORY_TYPE})
        expense_payees = expense_payees.assign(
            **{'destination_eng': None, 'keywords': None, 'category_id': None,
               'subcategory_id': None, 'user_id': user_id,
               'category_type': EXPENSE_CATEGORY_TYPE})
        new_payees = pd.concat([income_payees, expense_payees]).drop(columns=['is_income'])
        return new_payees

    def assign_category_ids(self, payees, transactions):

        """
        Assigns the category IDs to the transactions.

        Args:
            payees (DataFrame): The payees.
            transactions (DataFrame): The transactions.

        Returns:
            DataFrame: The transactions with the category IDs
        """

        payee_maps = payees[['category_id', 'subcategory_id', 'destination', 'alias_map', 'category_type']]
        income_category = TransactionCategory.objects.filter(category_type=INCOME_CATEGORY_TYPE).first()
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
        if income_category:
            transactions.loc[transactions['is_income'], 'category_id'] = income_category.id
        transactions['category_id'] = transactions['category_id'].replace({np.nan: None})
        transactions['subcategory_id'] = transactions['subcategory_id'].replace({np.nan: None})
        return transactions
