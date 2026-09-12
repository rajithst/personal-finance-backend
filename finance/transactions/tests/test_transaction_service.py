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
