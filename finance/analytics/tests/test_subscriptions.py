import pytest
from rest_framework import status
from finance.analytics.service.analytics_service import AnalyticsService

SUBSCRIPTIONS_ENDPOINT = "/finance/analytics/subscriptions/"


@pytest.fixture
def mock_analytics_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch("finance.analytics.views.AnalyticsService", return_value=mock_service)
    return mock_service


@pytest.mark.django_db
class TestSubscriptionRadarView:

    def test_get_subscriptions_success_return_200(self, api_client, mock_analytics_service, authenticate):
        authenticate()
        mock_data = {
            'summary': {
                'total_active_count': 5,
                'monthly_recurring_burn': 35000.0,
                'annual_projected_burn': 420000.0,
                'price_hike_count': 1,
                'total_monthly_hike_creep': 500.0,
                'upcoming_7_days_count': 2,
                'upcoming_7_days_amount': 4500.0,
            },
            'subscriptions': [
                {
                    'id': 'Netflix',
                    'name': 'Netflix',
                    'cadence': 'monthly',
                    'sub_type': 'digital',
                    'monthly_equivalent': 1590.0,
                    'price_hiked': False,
                    'status': 'active',
                }
            ],
            'upcoming_renewals': [],
            'category_breakdown': [],
        }
        mock_analytics_service.get_subscriptions_radar.return_value = mock_data

        response = api_client.get(SUBSCRIPTIONS_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert response.data['data']['summary']['total_active_count'] == 5
        assert len(response.data['data']['subscriptions']) == 1
        assert response.data['data']['subscriptions'][0]['name'] == 'Netflix'
        mock_analytics_service.get_subscriptions_radar.assert_called_once()

    def test_get_subscriptions_exception_return_500(self, api_client, mock_analytics_service, authenticate):
        authenticate()
        mock_analytics_service.get_subscriptions_radar.side_effect = Exception("Calculation error")

        response = api_client.get(SUBSCRIPTIONS_ENDPOINT)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
        assert response.data['data'] is None


@pytest.mark.django_db
class TestSubscriptionRadarService:

    def test_service_returns_valid_structure(self):
        service = AnalyticsService()
        result = service.get_subscriptions_radar()

        assert 'summary' in result
        assert 'subscriptions' in result
        assert 'upcoming_renewals' in result
        assert 'category_breakdown' in result

        assert isinstance(result['summary']['total_active_count'], int)
        assert isinstance(result['subscriptions'], list)
        assert isinstance(result['upcoming_renewals'], list)
        assert isinstance(result['category_breakdown'], list)
