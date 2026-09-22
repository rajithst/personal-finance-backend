import pytest
from rest_framework import status
from finance.analytics.service.analytics_service import AnalyticsService

AUDIT_REPORTS_ENDPOINT = "/finance/analytics/audit-reports/"


@pytest.fixture
def mock_analytics_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch("finance.analytics.views.AnalyticsService", return_value=mock_service)
    return mock_service


@pytest.mark.django_db
class TestAuditReportsView:

    def test_get_audit_reports_success_return_200(self, api_client, mock_analytics_service, authenticate):
        authenticate()
        mock_data = {
            'available_years': [2026, 2025],
            'selected_year': 2026,
            'macro_comparison': [
                {
                    'label': 'Gross Income',
                    'key': 'income',
                    'description': 'Salary',
                    'is_rate': False,
                    'year_2025': 8000000.0,
                    'year_2026': 5000000.0,
                    'diff': -3000000.0,
                    'diff_pct': -37.5,
                }
            ],
            'monthly_breakdown': [
                {
                    'month_num': 1,
                    'month_key': '2026-01',
                    'month_name': 'Jan 2026',
                    'gross_income': 400000.0,
                    'living_expenses': 300000.0,
                    'operational_surplus': 100000.0,
                    'bank_debits': 350000.0,
                    'securities_savings': 0.0,
                    'total_mizuho_outflow': 350000.0,
                    'net_bank_movement': 50000.0,
                    'cc_spending': 200000.0,
                    'cc_bills_paid': 200000.0,
                    'atm_withdrawals': 10000.0,
                }
            ],
            'monthly_summary': {
                'total': {'gross_income': 400000.0},
                'monthly_avg': {'gross_income': 400000.0},
                'active_months_count': 1,
            },
            'bank_debit_payments': [
                {
                    'destination': 'Rakuten Card Payment',
                    'category_name': 'Cash Payments',
                    'subcategory_name': 'Credit Card Payments',
                    'count': 1,
                    'total_amount': 200000.0,
                    'percentage': 57.1,
                    'monthly_avg': 200000.0,
                }
            ],
            'living_expenses_by_category': [
                {
                    'category_id': 1,
                    'category_name': 'Housing',
                    'count': 1,
                    'total_amount': 150000.0,
                    'percentage': 50.0,
                    'monthly_avg': 150000.0,
                    'subcategories': [],
                }
            ],
        }
        mock_analytics_service.get_audit_reports.return_value = mock_data

        response = api_client.get(AUDIT_REPORTS_ENDPOINT, {'year': 2026})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert response.data['data']['selected_year'] == 2026
        assert len(response.data['data']['macro_comparison']) == 1
        assert len(response.data['data']['monthly_breakdown']) == 1
        assert len(response.data['data']['bank_debit_payments']) == 1
        assert len(response.data['data']['living_expenses_by_category']) == 1
        mock_analytics_service.get_audit_reports.assert_called_once()

    def test_get_audit_reports_exception_return_500(self, api_client, mock_analytics_service, authenticate):
        authenticate()
        mock_analytics_service.get_audit_reports.side_effect = Exception("Report error")

        response = api_client.get(AUDIT_REPORTS_ENDPOINT)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
        assert "Report error" in response.data['message']


@pytest.mark.django_db
class TestAuditReportsServiceDirect:

    def test_service_returns_audit_data_structure(self):
        service = AnalyticsService()
        result = service.get_audit_reports({'year': 2026})

        assert 'available_years' in result
        assert 'selected_year' in result
        assert 'macro_comparison' in result
        assert 'monthly_breakdown' in result
        assert 'monthly_summary' in result
        assert 'bank_debit_payments' in result
        assert 'living_expenses_by_category' in result
        assert 'cash_reconciliation' in result
        assert 'card_billing_audit' in result
        assert 'card_billing_summary' in result
        assert 'monthly_reconciliation' in result
        assert isinstance(result['macro_comparison'], list)
        assert isinstance(result['monthly_breakdown'], list)
        assert isinstance(result['bank_debit_payments'], list)
        assert isinstance(result['living_expenses_by_category'], list)
        assert isinstance(result['cash_reconciliation'], dict)
        assert isinstance(result['card_billing_audit'], list)
        assert isinstance(result['monthly_reconciliation'], list)

