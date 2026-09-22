import pytest
from rest_framework import status
from finance.analytics.service.analytics_service import AnalyticsService

ANALYTICS_ENDPOINT = "/finance/analytics/"


@pytest.fixture
def mock_analytics_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch("finance.analytics.views.AnalyticsService", return_value=mock_service)
    return mock_service


@pytest.mark.django_db
class TestAnalyticsView:

    def test_get_analytics_success_return_200(self, api_client, mock_analytics_service, authenticate):
        authenticate()
        mock_data = {
            'kpis': {'total_income': 500000, 'total_expense': 300000, 'net_savings': 200000},
            'time_series': [],
            'category_breakdown': [],
            'subcategory_breakdown': [],
            'behavior_day_of_week': [],
            'behavior_day_of_month': [],
            'account_breakdown': [],
            'top_payees': [],
            'yoy_comparison': [],
            'recent_transactions': [],
        }
        mock_analytics_service.get_analytics.return_value = mock_data

        response = api_client.get(ANALYTICS_ENDPOINT, {'start_date': '2024-01-01', 'end_date': '2024-12-31'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert response.data['data']['kpis']['total_income'] == 500000
        mock_analytics_service.get_analytics.assert_called_once()

    def test_get_analytics_exception_return_500(self, api_client, mock_analytics_service, authenticate):
        authenticate()
        mock_analytics_service.get_analytics.side_effect = Exception("Database error")

        response = api_client.get(ANALYTICS_ENDPOINT)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
        assert "Database error" in response.data['message']


@pytest.mark.django_db
class TestAnalyticsServiceDirect:

    def test_service_returns_all_expected_dimensions(self):
        service = AnalyticsService()
        result = service.get_analytics({
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'flow_type': 'all',
        })

        assert 'kpis' in result
        assert 'time_series' in result
        assert 'category_breakdown' in result
        assert 'subcategory_breakdown' in result
        assert 'behavior_day_of_week' in result
        assert 'behavior_day_of_month' in result
        assert 'account_breakdown' in result
        assert 'top_payees' in result
        assert 'yoy_comparison' in result
        assert 'recent_transactions' in result
        assert 'ticket_size_distribution' in result
        assert 'capital_allocation' in result
        assert 'fixed_vs_variable' in result
        assert 'cumulative_month_pacing' in result
        assert len(result['ticket_size_distribution']['brackets']) == 5
        assert 'benchmark' in result['capital_allocation']
        assert 'flexibility_score' in result['fixed_vs_variable']
        assert len(result['cumulative_month_pacing']['days']) == 31
        assert len(result['behavior_day_of_week']) == 7
        assert len(result['behavior_day_of_month']) == 31
        assert len(result['yoy_comparison']) == 12

    def test_service_parses_comma_separated_filters(self):
        service = AnalyticsService()
        ids = service.parse_id_list("1, 2, 3, abc, 4")
        assert ids == [1, 2, 3, 4]

        list_ids = service.parse_id_list([5, "6", "invalid"])
        assert list_ids == [5, 6]
