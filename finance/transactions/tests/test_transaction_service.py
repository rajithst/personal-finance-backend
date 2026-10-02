from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

from finance.transactions.services.transaction_list_service import (
    TransactionBulkService,
    TransactionListService,
)


class TestTransactionServices:
    def test_extract_valid_fields_does_not_set_missing_fields_to_none(self):
        bulk_service = TransactionBulkService()
        data = {
            'amount': Decimal('1500.00'),
            'destination': 'Coffee Shop',
            'category': 3,
            'account': 1,
        }

        extracted = bulk_service.extract_valid_fields(data)

        assert extracted['amount'] == Decimal('1500.00')
        assert extracted['destination'] == 'Coffee Shop'
        assert extracted['category_id'] == 3
        assert extracted['account_id'] == 1

        # Crucial check: omitted fields must NOT be in extracted or set to None,
        # so that Django model defaults (e.g. is_deleted=False, is_expense=True) are not overwritten
        assert 'is_deleted' not in extracted
        assert 'is_income' not in extracted
        assert 'is_expense' not in extracted

    @patch("finance.transactions.services.transaction_list_service.ResponseTransactionSerializer")
    def test_handle_serializer_no_redundant_query(self, mock_resp_serializer_cls):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_instance = MagicMock()
        mock_instance.pk = 101
        mock_serializer.save.return_value = mock_instance

        mock_resp_serializer = MagicMock()
        mock_resp_serializer.data = {'id': 101, 'amount': '100.00'}
        mock_resp_serializer_cls.return_value = mock_resp_serializer

        service = TransactionListService()
        success, data, item = service.handle_serializer(mock_serializer)

        assert success is True
        assert data == {'id': 101, 'amount': '100.00'}
        assert item == mock_instance
        # Verified: ResponseTransactionSerializer is called directly with the saved item,
        # without making an extra Transaction.objects.get(pk=101) database query!
        mock_resp_serializer_cls.assert_called_once_with(mock_instance)

    def test_find_new_payees_deduplication_and_blank_filtering(self):
        import pandas as pd
        from finance.transactions.services.transaction_import_service import TransactionImportService

        service = TransactionImportService()
        existing_payees_df = pd.DataFrame({
            'destination': ['Known Store']
        })

        transactions_df = pd.DataFrame({
            'destination': ['New Merchant', 'New Merchant', '  ', None, 'Another Merchant'],
            'destination_original': ['New Merchant 1', 'New Merchant 2', '  ', None, 'Another Merchant Original'],
            'is_income': [0, 0, 0, 0, 1]
        })

        new_payees = service.find_new_payees(existing_payees_df, transactions_df)

        assert len(new_payees) == 2
        assert set(new_payees['destination']) == {'New Merchant', 'Another Merchant'}

    @pytest.mark.django_db
    def test_assign_category_ids_preserves_bank_payment_flags(self):
        import pandas as pd
        from finance.transactions.services.transaction_import_service import TransactionImportService
        from common.transaction_const import EXPENSE_CATEGORY_TYPE, PAYMENT_CATEGORY_TYPE

        service = TransactionImportService()
        payees_df = pd.DataFrame([
            {
                'category_id': 1,
                'subcategory_id': 1,
                'destination': 'Rent Payment',
                'alias_map': 'Rent Payment',
                'category_type': EXPENSE_CATEGORY_TYPE
            },
            {
                'category_id': 14,
                'subcategory_id': 58,
                'destination': 'Card Bill Payment',
                'alias_map': 'Card Bill Payment',
                'category_type': PAYMENT_CATEGORY_TYPE
            },
            {
                'category_id': 14,
                'subcategory_id': 59,
                'destination': 'ATM Withdrawal',
                'alias_map': 'ATM Withdrawal',
                'category_type': PAYMENT_CATEGORY_TYPE
            },
            {
                'category_id': 3,
                'subcategory_id': 13,
                'destination': 'Supermarket (Card)',
                'alias_map': 'Supermarket',
                'category_type': EXPENSE_CATEGORY_TYPE
            }
        ])

        transactions_df = pd.DataFrame([
            # Bank expense: already has is_payment=True
            {'destination': 'Rent Payment', 'alias': '', 'is_payment': True, 'is_income': False, 'is_expense': True, 'is_saving': False},
            # Bank payment: Card bill repayment
            {'destination': 'Card Bill Payment', 'alias': '', 'is_payment': True, 'is_income': False, 'is_expense': False, 'is_saving': False},
            # Bank payment: ATM withdrawal (living expense rule)
            {'destination': 'ATM Withdrawal', 'alias': '', 'is_payment': True, 'is_income': False, 'is_expense': False, 'is_saving': False},
            # Credit card expense: is_payment=False
            {'destination': 'Supermarket (Card)', 'alias': '', 'is_payment': False, 'is_income': False, 'is_expense': True, 'is_saving': False},
        ])

        result = service.assign_category_ids(payees_df, transactions_df)

        rent_row = result[result['destination'] == 'Rent Payment'].iloc[0]
        bill_row = result[result['destination'] == 'Card Bill Payment'].iloc[0]
        atm_row = result[result['destination'] == 'ATM Withdrawal'].iloc[0]
        card_row = result[result['destination'] == 'Supermarket (Card)'].iloc[0]

        # Bank debit with expense category keeps is_payment=True AND is_expense=True
        assert rent_row['is_payment'] == True
        assert rent_row['is_expense'] == True

        # Payment category (card bill repayment) has is_payment=True, is_expense=False
        assert bill_row['is_payment'] == True
        assert bill_row['is_expense'] == False

        # ATM cash withdrawal gets marked as is_payment=True, is_expense=True (living expense rule)
        assert atm_row['is_payment'] == True
        assert atm_row['is_expense'] == True

        # Card expense has is_payment=False, is_expense=True
        assert card_row['is_payment'] == False
        assert card_row['is_expense'] == True

