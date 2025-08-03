import pytest
from rest_framework import status

@pytest.fixture
def mock_dashboard_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch('investments.dashboard.views.DashboardService', return_value=mock_service)
    return mock_service

@pytest.mark.django_db
class TestInvestmentDashboardView:
    def test_get_investment_dashboard_success_return_200(self, api_client, mock_dashboard_service, authenticate):
        # Arrange
        authenticate()
        mock_dashboard_service.get_monthly_invested_amount.return_value = 1000
        mock_dashboard_service.get_portfolio_allocation.return_value = {'sector_allocation': [],
                                                                                     'industry_allocation': []}
        mock_dashboard_service.get_performance.return_value = {'total_investment': 10000,
                                                                            'current_portfolio_value': 15000,
                                                                            'total_profit': 5000}
        mock_dashboard_service.get_portfolio_growth_daily.return_value = []
        mock_dashboard_service.get_sector_wise_performance.return_value = []
        mock_dashboard_service.get_passive_income.return_value = 500

        # Act
        response = api_client.get('/investments/dashboard/', {'portfolio': 1})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_investment_dashboard_invalid_param_return_400(self, api_client, authenticate):
        authenticate()

        response = api_client.get('/investments/dashboard/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

    def test_get_investment_dashboard_failure_return_400(self, api_client, mock_dashboard_service, authenticate):
        # Arrange
        authenticate()
        mock_dashboard_service.get_monthly_invested_amount.side_effect = Exception('Service Error')

        # Act
        response = api_client.get('/investments/dashboard/', {'portfolio': 1})

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False

    def test_get_investment_dashboard_unauthenticated_request_return_401(self, api_client):
        # Act
        response = api_client.get('/investments/dashboard/', {'portfolio': 1})

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED