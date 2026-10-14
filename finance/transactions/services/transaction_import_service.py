import logging
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

import numpy as np
import pandas as pd
from django.db import transaction
from django.utils import timezone
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
        res = self.get_applicable_transactions(transactions, import_params, account=account)
        if isinstance(res, tuple):
            transactions, skipped_duplicates_count = res
        else:
            transactions, skipped_duplicates_count = res, 0

        if transactions.empty:
            return {
                'imported_count': 0,
                'skipped_duplicates_count': skipped_duplicates_count,
                'new_payees_count': 0,
            }

        payees = self.get_payee_map()
        rewrite_rules = self.get_rewrite_rules(payees)
        transactions = self.apply_rewrite_rules(transactions, rewrite_rules)
        user = get_current_user()
        user_id = import_params.get('user_id') or getattr(user, 'id', None)
        new_payees = self.find_new_payees(payees, transactions, user_id=user_id)
        expenses = self.assign_category_ids(payees, transactions, user_id=user_id)

        if expenses is not None and not expenses.empty:
            last_import_date = expenses['date'].max()
            expense_records = expenses.to_dict('records')
            expense_objects = []
            payee_objects = []

            for new_payee in new_payees.to_dict('records'):
                payee_objects.append(DestinationMap(**new_payee))

            user = get_current_user()
            user_id = import_params.get('user_id') or getattr(user, 'id', None)
            
            # Dynamically resolve counterparty account IDs
            rak_sec_id = Account.objects.filter(account_name__icontains='Rakuten Securities').values_list('id', flat=True).first()
            jp_post_id = Account.objects.filter(account_name__icontains='JP Post').values_list('id', flat=True).first()
            wise_id = Account.objects.filter(account_name__icontains='Wise').values_list('id', flat=True).first()
            rak_card_id = Account.objects.filter(account_name__icontains='Rakuten Card').values_list('id', flat=True).first()
            epos_card_id = Account.objects.filter(account_name__icontains='EPOS').values_list('id', flat=True).first()
            docomo_card_id = Account.objects.filter(account_name__icontains='Docomo').values_list('id', flat=True).first()
            tokyu_card_id = Account.objects.filter(account_name__icontains='Tokyu').values_list('id', flat=True).first()

            for expense in expense_records:
                expense['user_id'] = user_id
                dest = str(expense.get('destination') or '') + ' ' + str(expense.get('destination_original') or '')
                if ('Rakuten Securities' in dest or 'ラクテンシヨウケン' in dest or '楽天証券' in dest) and rak_sec_id and rak_sec_id != account.id:
                    expense['counterparty_account_id'] = rak_sec_id
                elif ('JP Post' in dest or 'ユウチヨ' in dest or 'ゆうちょ' in dest or 'テンナコン' in dest) and jp_post_id and jp_post_id != account.id:
                    expense['counterparty_account_id'] = jp_post_id
                elif ('Wise' in dest or 'ワイズ' in dest or 'トランスファーワイズ' in dest or 'ヒチナイドウ' in dest) and wise_id and wise_id != account.id:
                    expense['counterparty_account_id'] = wise_id
                elif ('Rakuten Card' in dest or 'ラクテンカード' in dest) and rak_card_id and rak_card_id != account.id:
                    expense['counterparty_account_id'] = rak_card_id
                elif ('EPOS Card' in dest or 'エポス' in dest) and epos_card_id and epos_card_id != account.id:
                    expense['counterparty_account_id'] = epos_card_id
                elif ('Docomo Card' in dest or 'ドコモ' in dest) and docomo_card_id and docomo_card_id != account.id:
                    expense['counterparty_account_id'] = docomo_card_id
                elif ('Tokyu Card' in dest or 'トウキユウ' in dest or '東急' in dest) and tokyu_card_id and tokyu_card_id != account.id:
                    expense['counterparty_account_id'] = tokyu_card_id
                expense_objects.append(Transaction(**expense))
            try:
                with transaction.atomic():
                    is_transactions_imported = Transaction.objects.bulk_create(expense_objects)
                    if is_transactions_imported:
                        if hasattr(last_import_date, 'strftime'):
                            last_dt = datetime.combine(last_import_date, datetime.min.time())
                            if timezone.is_naive(last_dt):
                                last_dt = timezone.make_aware(last_dt)
                        else:
                            last_dt = last_import_date
                        Account.objects.filter(id=account.id).update(last_import_date=last_dt)
                        if payee_objects:
                            DestinationMap.objects.bulk_create(payee_objects)
                return {
                    'imported_count': len(is_transactions_imported),
                    'skipped_duplicates_count': skipped_duplicates_count,
                    'new_payees_count': len(payee_objects),
                }
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

    def get_applicable_transactions(self, transaction_data, import_params, account=None):
        """
        Gets the applicable transactions.

        Args:
            transaction_data (DataFrame): The transaction data.
            import_params (dict): The import parameters.
            account (Account, optional): Target account.

        Returns:
            tuple: (DataFrame of applicable transactions, int count of skipped duplicates)
        """
        if transaction_data is None or transaction_data.empty:
            return transaction_data, 0

        import_from_last_date = import_params.get('import_from_last_date', None)
        drop_duplicates = import_params.get('drop_duplicates', None)
        start_date = import_params.get('start_date', None)
        end_date = import_params.get('end_date', None)
        last_import_date = import_params.get('last_import_date', None)

        if import_from_last_date and last_import_date:
            last_date_val = last_import_date.date() if hasattr(last_import_date, 'date') else last_import_date
            transaction_data = transaction_data[transaction_data['date'] > last_date_val]
        else:
            if start_date:
                start_d = datetime.strptime(start_date, '%Y-%m-%d').date() if isinstance(start_date, str) else start_date
                transaction_data = transaction_data[transaction_data['date'] >= start_d]
            if end_date:
                end_d = datetime.strptime(end_date, '%Y-%m-%d').date() if isinstance(end_date, str) else end_date
                transaction_data = transaction_data[transaction_data['date'] <= end_d]

        skipped_duplicates = 0
        if drop_duplicates and not transaction_data.empty:
            # 1. Drop duplicates within incoming batch
            before_batch = len(transaction_data)
            transaction_data = transaction_data.drop_duplicates(subset=['date', 'destination_original', 'amount'])
            skipped_duplicates += (before_batch - len(transaction_data))

            # 2. Drop duplicates already present in database for this account
            target_account = account or self.get_account_from_id(import_params.get('account_id'))
            if target_account and not transaction_data.empty:
                min_date = transaction_data['date'].min()
                max_date = transaction_data['date'].max()
                existing_txns = Transaction.objects.filter(
                    account_id=target_account.id,
                    date__gte=min_date,
                    date__lte=max_date,
                    is_deleted=False
                ).values_list('date', 'amount', 'destination_original', 'destination')

                existing_keys = set()
                for d_date, d_amt, d_orig, d_dest in existing_txns:
                    amt_str = f"{Decimal(str(d_amt)):.2f}"
                    if d_orig:
                        existing_keys.add((d_date, amt_str, str(d_orig).strip()))
                    if d_dest:
                        existing_keys.add((d_date, amt_str, str(d_dest).strip()))

                if existing_keys:
                    def is_existing(row):
                        amt_str = f"{Decimal(str(row['amount'])):.2f}"
                        row_date = row['date']
                        orig = str(row.get('destination_original') or '').strip()
                        dest = str(row.get('destination') or '').strip()
                        return (row_date, amt_str, orig) in existing_keys or (row_date, amt_str, dest) in existing_keys

                    mask = ~transaction_data.apply(is_existing, axis=1)
                    before_db = len(transaction_data)
                    transaction_data = transaction_data[mask]
                    skipped_duplicates += (before_db - len(transaction_data))

        return transaction_data, skipped_duplicates

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

            # Group by destination to prevent duplicate payee joins from inflating rows
            grouped = payee_maps.groupby('destination', as_index=False).agg({
                'destination_original': 'first',
                'alias_map': 'first',
                'keywords': lambda s: ','.join(set(filter(None, ','.join(s).split(',')))),
                'category_type': 'first',
                'category_id': 'first',
                'subcategory_id': 'first'
            })
            return grouped
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
        inverted = inverse_dict(contains_categories)
        # Sort by keyword length descending so longer/more specific rules match first
        return dict(sorted(inverted.items(), key=lambda item: len(item[0]), reverse=True))

    def apply_rewrite_rules(self, transactions, rewrite_rules):
        for field in rewrite_rules:
            mask = transactions['destination'].astype(str).str.contains(field, regex=False, na=False)
            if 'destination_original' in transactions.columns:
                mask = mask | transactions['destination_original'].astype(str).str.contains(field, regex=False, na=False)
            transactions.loc[mask, 'alias'] = rewrite_rules[field]
            transactions.loc[mask, 'destination'] = rewrite_rules[field]
        return transactions

    def find_new_payees(self, payees, transactions, user_id=None):
        """
        Finds the new payees.

        Args:
            payees (DataFrame): The payees.
            transactions (DataFrame): The transactions.
            user_id (int, optional): The user ID.

        Returns:
            DataFrame: The new payees.
        """
        existing_payees = payees['destination'].dropna().unique()
        if user_id is None:
            current_user = get_current_user()
            user_id = getattr(current_user, 'id', None)
        new_payees = transactions[~transactions['destination'].isin(existing_payees)].copy()
        new_payees = new_payees[new_payees['destination'].notna() & (new_payees['destination'].astype(str).str.strip() != '')]
        new_payees = new_payees.drop_duplicates(subset='destination', keep="first")
        new_payees = new_payees[['destination', 'destination_original', 'is_income']]
        income_payees = new_payees[new_payees['is_income'] == 1]
        expense_payees = new_payees[new_payees['is_income'] == 0]

        income_payees = income_payees.assign(
            **{'destination_eng': income_payees['destination'],
               'keywords': income_payees['destination_original'].fillna(income_payees['destination']),
               'category_id': None,
               'subcategory_id': None, 'user_id': user_id,
               'category_type': INCOME_CATEGORY_TYPE})
        expense_payees = expense_payees.assign(
            **{'destination_eng': expense_payees['destination'],
               'keywords': expense_payees['destination_original'].fillna(expense_payees['destination']),
               'category_id': None,
               'subcategory_id': None, 'user_id': user_id,
               'category_type': EXPENSE_CATEGORY_TYPE})
        new_payees = pd.concat([income_payees, expense_payees]).drop(columns=['is_income'])
        return new_payees

    def assign_category_ids(self, payees, transactions, user_id=None):

        """
        Assigns the category IDs to the transactions.

        Args:
            payees (DataFrame): The payees.
            transactions (DataFrame): The transactions.

        Returns:
            DataFrame: The transactions with the category IDs
        """

        payee_maps = payees[['category_id', 'subcategory_id', 'destination', 'alias_map', 'category_type']]
        try:
            income_category = TransactionCategory.objects.filter(category_type=INCOME_CATEGORY_TYPE).first()
        except Exception:
            income_category = None
        transactions = pd.merge(transactions, payee_maps, on=['destination'], how='left')
        transactions['category_type'] = pd.to_numeric(transactions['category_type'], errors='coerce')
        is_payment_existing = transactions['is_payment'].fillna(False).astype(bool)
        is_income_existing = transactions['is_income'].fillna(False).astype(bool)
        transactions.loc[
            (transactions['category_type'] == EXPENSE_CATEGORY_TYPE) & (~is_income_existing),
            ['is_expense', 'is_income', 'is_saving']
        ] = [True, False, False]
        transactions.loc[
            (transactions['category_type'] == EXPENSE_CATEGORY_TYPE) & (~is_income_existing) & (~is_payment_existing),
            'is_payment'
        ] = False
        transactions.loc[
            transactions['category_type'] == INCOME_CATEGORY_TYPE, ['is_expense', 'is_income', 'is_payment',
                                                                    'is_saving']] = [False,
                                                                                     True,
                                                                                     False,
                                                                                     False]
        # Savings category type:
        # Outgoing investments/savings (is_income is False) -> is_saving=True, is_payment=True, is_expense=False
        transactions.loc[
            (transactions['category_type'] == SAVINGS_CATEGORY_TYPE) & (~is_income_existing),
            ['is_expense', 'is_income', 'is_saving', 'is_payment']
        ] = [False, False, True, True]
        # Inbound returns/transfers from savings/brokerage to bank (is_income is True) -> is_income=True, is_saving=False, is_expense=False, is_payment=False
        transactions.loc[
            (transactions['category_type'] == SAVINGS_CATEGORY_TYPE) & is_income_existing,
            ['is_expense', 'is_income', 'is_saving', 'is_payment']
        ] = [False, True, False, False]

        # Payment / Internal Transfers (Category Type 4):
        # Outgoing payments/transfers (is_income is False) -> is_expense=False, is_income=False, is_payment=True, is_saving=False
        transactions.loc[
            (transactions['category_type'] == PAYMENT_CATEGORY_TYPE) & (~is_income_existing),
            ['is_expense', 'is_income', 'is_payment', 'is_saving']
        ] = [False, False, True, False]
        # Inbound transfers/refunds received into bank (is_income is True) -> is_expense=False, is_income=True, is_payment=False, is_saving=False
        transactions.loc[
            (transactions['category_type'] == PAYMENT_CATEGORY_TYPE) & is_income_existing,
            ['is_expense', 'is_income', 'is_payment', 'is_saving']
        ] = [False, True, False, False]

        # Knowledge Section Rule 1: Credit Card Bill Settlements (transfers paying credit card bills)
        # Must have is_expense=False to prevent double-counting because individual purchases are on card statements.
        cc_settlement_mask = (
            transactions['destination'].astype(str).str.contains(
                'Card Payment|クレジットカード|カード利用代金', case=False, na=False
            ) |
            transactions['destination'].isin([
                'Rakuten Card Payment', 'EPOS Card Payment', 'Tokyu Card Payment', 'Docomo Card Payment'
            ]) |
            (transactions['subcategory_id'] == 60)
        )
        transactions.loc[cc_settlement_mask, ['is_expense', 'is_payment', 'is_saving', 'is_income']] = [False, True, False, False]

        # Loan & Cashing Repayments (Personal Loan Payments, Tokyu Card Cashing Installment Fee)
        # These are living expense obligations that must be marked as is_expense=True and is_payment=True
        loan_mask = (
            (transactions['subcategory_id'] == 56) |
            transactions['destination'].astype(str).str.contains('Cashing Installment|Personal Loan|キャッシングリボ', case=False, na=False)
        ) & (~transactions['is_income'])
        transactions.loc[loan_mask, ['is_expense', 'is_payment', 'is_saving', 'is_income']] = [True, True, False, False]

        # Knowledge Section Rule 2: ATM Cash Withdrawals are living expenses spent outside tracked card statements (Payment + Expense)
        dest_orig_match = (
            transactions['destination_original'].astype(str).str.contains('ＡＴＭ|７ＢＫ|ATM', case=False, na=False)
            if 'destination_original' in transactions.columns
            else False
        )
        atm_mask = (
            transactions['destination'].astype(str).str.contains('ATM|ゆうちょ銀行ATM提携', case=False, na=False) |
            dest_orig_match
        ) & (
            ~transactions['destination'].astype(str).str.contains('手数料|Cash Advance', case=False, na=False)
        )
        transactions.loc[atm_mask, ['is_expense', 'is_payment', 'is_saving', 'is_income']] = [True, True, False, False]

        # Knowledge Section Rule 3: Bank Direct Living Expenses (Rent, Car Loans, Housing, Fees, and bank debits with Expense categories)
        # These are living expenses paid directly from the bank account, NOT via credit cards.
        exp_cat_ids = []
        try:
            exp_cat_ids = list(TransactionCategory.objects.filter(category_type=EXPENSE_CATEGORY_TYPE).values_list('id', flat=True))
        except Exception:
            if 'category_type' in payees.columns and 'category_id' in payees.columns:
                exp_cat_ids = list(payees[payees['category_type'] == EXPENSE_CATEGORY_TYPE]['category_id'].dropna().unique())
        bank_living_dests = [
            'Rent Payment', 'BMW Car Payment', 'SUV Land', 'Housing Center', 'Transfer Fee', '振込手数料', '手数料', 'Wise Remittance', 'Direct Debit'
        ]
        bank_living_mask = (
            transactions['destination'].isin(bank_living_dests) |
            transactions['category_id'].isin(exp_cat_ids)
        ) & (~cc_settlement_mask) & (~transactions['is_saving']) & (~transactions['is_income'])
        transactions.loc[bank_living_mask & is_payment_existing, ['is_expense', 'is_payment']] = [True, True]

        # Knowledge Section Rule 4: Dynamic Employer Mapping from Career Timeline Data
        # Queries Employment records dynamically to resolve payroll inflows (給与 / 賞与)
        dest_orig_series = transactions['destination_original'] if 'destination_original' in transactions.columns else transactions['destination']
        payroll_mask = transactions['is_income'] & (
            dest_orig_series.astype(str).str.contains('給与|賞与', case=False, na=False) |
            transactions['destination'].astype(str).str.contains('給与|賞与|Salary|Bonus', case=False, na=False)
        )
        if payroll_mask.any():
            employments = []
            try:
                from finance.career.models import Employment
                emp_qs = Employment.objects.select_related('company')
                if user_id:
                    emp_qs = emp_qs.filter(user_id=user_id)
                employments = list(emp_qs.order_by('start_date'))
            except Exception as e:
                logger.warning(f"Could not load career employments for dynamic mapping: {e}")

            def resolve_employer_payroll(row):
                d = row['date']
                if hasattr(d, 'date'):
                    row_dt = d.date()
                elif hasattr(d, 'strftime'):
                    row_dt = d
                else:
                    try:
                        row_dt = datetime.strptime(str(d)[:10], '%Y-%m-%d').date()
                    except Exception:
                        row_dt = None

                is_bonus_kw = (
                    '賞与' in str(row.get('destination_original') or '') or
                    '賞与' in str(row.get('destination') or '') or
                    'Bonus' in str(row.get('destination') or '')
                )
                subcat = 71 if is_bonus_kw else 65

                matched_emp = None
                if employments and row_dt:
                    # 1. Exact tenure containment: start_date <= row_dt <= (end_date or today)
                    for emp in employments:
                        start = emp.start_date
                        end = emp.end_date
                        if start <= row_dt and (end is None or row_dt <= end):
                            matched_emp = emp
                            break

                    # 2. Nearest tenure fallback if transaction date falls slightly outside start/end
                    if not matched_emp:
                        def dist_to_emp(emp):
                            start = emp.start_date
                            end = emp.end_date
                            if row_dt < start:
                                return (start - row_dt).days
                            elif end and row_dt > end:
                                return (row_dt - end).days
                            return 0
                        matched_emp = min(employments, key=dist_to_emp)

                company_name = matched_emp.company.name if matched_emp else 'Salary Income'
                dest = f"{company_name} (Bonus)" if is_bonus_kw else company_name
                return pd.Series([dest, 17, subcat, True, False, False, False])

            cols = ['destination', 'category_id', 'subcategory_id', 'is_income', 'is_payment', 'is_expense', 'is_saving']
            transactions.loc[payroll_mask, cols] = transactions[payroll_mask].apply(resolve_employer_payroll, axis=1).values

        # Knowledge Section Rule 5: Internal Transfers between Accounts (Rakuten Securities, JP Post, Wise)
        # Inbound transfers into bank accounts:
        # Must be Category 19 (Internal Transfer), is_income=True, is_payment=False, is_expense=False, is_saving=False.
        # This keeps the bank ledger balance 100% reconciled while completely isolating internal transfers from
        # Net Take-Home (Income tab & Analytics) and Payments tabs.
        try:
            from finance.categories.models import TransactionCategory, TransactionSubCategory
            int_cat = TransactionCategory.objects.filter(Q(category='Internal Transfer') | Q(id=19)).first()
            int_cat_id = int_cat.id if int_cat else 19
            sub_wise = TransactionSubCategory.objects.filter(category_id=int_cat_id, name__icontains='Wise').values_list('id', flat=True).first() or 80
            sub_jp = TransactionSubCategory.objects.filter(category_id=int_cat_id, name__icontains='JP Post').values_list('id', flat=True).first() or 81
            sub_gen = TransactionSubCategory.objects.filter(category_id=int_cat_id, name__icontains='General').values_list('id', flat=True).first() or 82
        except Exception:
            int_cat_id, sub_wise, sub_jp, sub_gen = 19, 80, 81, 82

        # 5a. Inbound Rakuten Securities return into Bank
        rak_inflow_mask = is_income_existing & (
            dest_orig_series.astype(str).str.contains('ラクテンシヨウケン|Rakuten Securities|楽天証券', case=False, na=False) |
            transactions['destination'].astype(str).str.contains('ラクテンシヨウケン|Rakuten Securities|楽天証券', case=False, na=False)
        )
        if rak_inflow_mask.any():
            transactions.loc[rak_inflow_mask, ['destination', 'category_id', 'subcategory_id', 'is_income', 'is_payment', 'is_expense', 'is_saving']] = [
                'Rakuten Securities Transfer (Internal)', int_cat_id, sub_gen, True, False, False, True
            ]

        # 5b. Inbound JP Post transfer into Bank
        jp_inflow_mask = is_income_existing & (
            dest_orig_series.astype(str).str.contains('ユウチヨ|ゆうちょ|JP Post|テンナコン', case=False, na=False) |
            transactions['destination'].astype(str).str.contains('ユウチヨ|ゆうちょ|JP Post|テンナコン', case=False, na=False)
        )
        if jp_inflow_mask.any():
            transactions.loc[jp_inflow_mask, ['destination', 'category_id', 'subcategory_id', 'is_income', 'is_payment', 'is_expense', 'is_saving']] = [
                'JP Post Bank Transfer', int_cat_id, sub_jp, True, False, False, False
            ]

        # 5c. Inbound Wise funds returning to Bank
        wise_inflow_mask = is_income_existing & (
            dest_orig_series.astype(str).str.contains('ワイズ|Wise|トランスファーワイズ|ヒチナイドウ', case=False, na=False) |
            transactions['destination'].astype(str).str.contains('ワイズ|Wise|トランスファーワイズ|ヒチナイドウ', case=False, na=False)
        )
        if wise_inflow_mask.any():
            transactions.loc[wise_inflow_mask, ['destination', 'category_id', 'subcategory_id', 'is_income', 'is_payment', 'is_expense', 'is_saving']] = [
                'Wise Return (Internal)', int_cat_id, sub_wise, True, False, False, False
            ]

        # 5d. Outbound transfers leaving Bank to JP Post (debit from bank, Internal Transfer)
        jp_outflow_mask = (~is_income_existing) & (
            dest_orig_series.astype(str).str.contains('ユウチヨ|ゆうちょ|JP Post|テンナコン', case=False, na=False) |
            transactions['destination'].astype(str).str.contains('ユウチヨ|ゆうちょ|JP Post|テンナコン', case=False, na=False)
        )
        if jp_outflow_mask.any():
            transactions.loc[jp_outflow_mask, ['destination', 'category_id', 'subcategory_id', 'is_income', 'is_payment', 'is_expense', 'is_saving']] = [
                'JP Post Bank Transfer', int_cat_id, sub_jp, False, True, False, False
            ]

        # 5e. Outbound transfers leaving Bank to Wise wallet
        wise_outflow_mask = (~is_income_existing) & (
            transactions['destination'] == 'Wise Transfer (Internal)'
        )
        if wise_outflow_mask.any():
            transactions.loc[wise_outflow_mask, ['category_id', 'subcategory_id', 'is_income', 'is_payment', 'is_expense', 'is_saving']] = [
                int_cat_id, sub_wise, False, True, False, False
            ]

        # 5f. Outbound transfers leaving Bank to Rakuten Securities (genuine savings debit into investment account)
        rak_outflow_mask = (~is_income_existing) & (
            dest_orig_series.astype(str).str.contains('ラクテンシヨウケン|Rakuten Securities|楽天証券', case=False, na=False) |
            transactions['destination'].astype(str).str.contains('ラクテンシヨウケン|Rakuten Securities|楽天証券', case=False, na=False)
        )
        if rak_outflow_mask.any():
            transactions.loc[rak_outflow_mask, ['destination', 'is_saving', 'is_payment', 'is_expense', 'is_income']] = [
                'Rakuten Securities', True, True, False, False
            ]

        transactions.loc[transactions['alias_map'].isnull() & transactions['alias'].notnull(), 'alias_map'] = \
            transactions['alias']

        transactions = transactions.drop(columns=['alias', 'category_type'])
        transactions = transactions.rename(columns={'alias_map': 'alias'})
        transactions['alias'] = transactions['alias'].replace({np.nan: None})
        if income_category:
            transactions.loc[transactions['is_income'] & transactions['category_id'].isna(), 'category_id'] = income_category.id
        transactions['category_id'] = transactions['category_id'].replace({np.nan: None})
        transactions['subcategory_id'] = transactions['subcategory_id'].replace({np.nan: None})
        return transactions
