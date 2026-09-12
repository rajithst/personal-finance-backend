import datetime
from unittest.mock import MagicMock, patch
import pytest

from finance.dashboard.service.dashboard_service import DashboardService


class TestDashboardService:
    @patch("finance.dashboard.service.dashboard_service.timezone")
    @patch.object(DashboardService, "get_queryset")
    def test_get_top_ten_expenses_date_math_march_to_feb(self, mock_get_qs, mock_tz):
        # Mock "today" as March 15, 2026 (non-leap year, Feb has 28 days)
        mock_now = MagicMock()
        mock_now.date.return_value = datetime.date(2026, 3, 15)
        mock_tz.now.return_value = mock_now

        mock_filter = MagicMock()
        mock_filter.values.return_value.order_by.return_value.__getitem__.return_value = []
        mock_get_qs.return_value.filter.return_value = mock_filter

        service = DashboardService()
        service.get_top_ten_expenses()

        # Check call arguments on filter
        call_kwargs = mock_get_qs.return_value.filter.call_args.kwargs
        assert call_kwargs['date__gte'] == datetime.date(2026, 2, 1)
        assert call_kwargs['date__lte'] == datetime.date(2026, 2, 28)

    @patch("finance.dashboard.service.dashboard_service.timezone")
    @patch.object(DashboardService, "get_queryset")
    def test_get_top_ten_expenses_date_math_january_to_dec(self, mock_get_qs, mock_tz):
        # Mock "today" as January 5, 2026 -> last month should be December 2025
        mock_now = MagicMock()
        mock_now.date.return_value = datetime.date(2026, 1, 5)
        mock_tz.now.return_value = mock_now

        mock_filter = MagicMock()
        mock_filter.values.return_value.order_by.return_value.__getitem__.return_value = []
        mock_get_qs.return_value.filter.return_value = mock_filter

        service = DashboardService()
        service.get_top_ten_expenses()

        call_kwargs = mock_get_qs.return_value.filter.call_args.kwargs
        assert call_kwargs['date__gte'] == datetime.date(2025, 12, 1)
        assert call_kwargs['date__lte'] == datetime.date(2025, 12, 31)

    @patch.object(DashboardService, "get_queryset")
    def test_get_monthly_kpi_summary(self, mock_get_qs):
        mock_item = {
            'month': datetime.date(2026, 5, 1),
            'income': 500000,
            'expense': 150000,
            'payment': 50000,
            'saving': 100000,
        }
        mock_qs_chain = MagicMock()
        mock_qs_chain.annotate.return_value.values.return_value.annotate.return_value.order_by.return_value = [mock_item]
        mock_get_qs.return_value.filter.return_value = mock_qs_chain

        service = DashboardService()
        kpis = service.get_monthly_kpi_summary(2026)

        assert 'income' in kpis
        assert 'expense' in kpis
        assert 'payment' in kpis
        assert 'saving' in kpis

        assert kpis['income'][0] == {'year': 2026, 'month': 5, 'amount': 500000}
        assert kpis['expense'][0] == {'year': 2026, 'month': 5, 'amount': 150000}
        assert kpis['payment'][0] == {'year': 2026, 'month': 5, 'amount': 50000}
        assert kpis['saving'][0] == {'year': 2026, 'month': 5, 'amount': 100000}

    def test_get_monthly_kpi_summary_missing_year(self):
        service = DashboardService()
        with pytest.raises(ValueError, match="Required filter year"):
            service.get_monthly_kpi_summary(None)
