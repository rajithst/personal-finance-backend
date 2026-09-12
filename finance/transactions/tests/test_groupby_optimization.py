import pandas as pd
import pytest

from finance.transactions.services.transaction_list_service import TransactionListService


class TestGroupByOptimization:
    def test_group_by_with_list_of_dicts(self):
        service = TransactionListService()
        data = [
            {'year': 2026, 'month': 1, 'month_text': 'January', 'amount': '100.50', 'desc': 'Grocery'},
            {'year': 2026, 'month': 1, 'month_text': 'January', 'amount': '49.50', 'desc': 'Coffee'},
            {'year': 2026, 'month': 2, 'month_text': 'February', 'amount': '200.00', 'desc': 'Internet'},
        ]
        result = service._group_by(data)

        # Output should be reversed chronological
        assert len(result) == 2
        # February first
        assert result[0]['year'] == 2026
        assert result[0]['month'] == 2
        assert result[0]['month_text'] == 'February'
        assert result[0]['total'] == 200.00
        assert len(result[0]['transactions']) == 1

        # January second
        assert result[1]['year'] == 2026
        assert result[1]['month'] == 1
        assert result[1]['month_text'] == 'January'
        assert result[1]['total'] == 150.00
        assert len(result[1]['transactions']) == 2
        assert result[1]['transactions'][0]['amount'] == 100.50

    def test_group_by_with_dataframe_backward_compatibility(self):
        service = TransactionListService()
        df = pd.DataFrame([
            {'year': 2026, 'month': 3, 'month_text': 'March', 'amount': 75.25, 'desc': 'Books'},
        ])
        result = service._group_by(df)

        assert len(result) == 1
        assert result[0]['month'] == 3
        assert result[0]['total'] == 75.25
        assert len(result[0]['transactions']) == 1

    def test_group_by_empty(self):
        service = TransactionListService()
        assert service._group_by([]) == []
        assert service._group_by(pd.DataFrame()) == []
        assert service._group_by(None) == []
