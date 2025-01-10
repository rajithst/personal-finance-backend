import pytest
from rest_framework import status

@pytest.fixture
def mock_dashboard_service(mocker):
    return mocker.patch('investments.apis.views.DashboardService')

@pytest.fixture
def mock_settings_service(mocker):
    return mocker.patch('investments.apis.views.SettingsService')



@pytest.fixture
def mock_dashboard_validator(mocker):
    return mocker.patch('investments.apis.views.DashboardValidator')

@pytest.mark.django_db
class TestInvestmentPerformanceView:
    def test_get_investment_performance_success(self, api_client, mock_dashboard_service, mock_dashboard_validator, authenticate):
        # Arrange
        authenticate()
        mock_dashboard_validator.validate_request.return_value = None
        mock_dashboard_service.return_value.get_monthly_invested_amount.return_value = 1000
        mock_dashboard_service.return_value.get_portfolio_allocation.return_value = {'sector_allocation': [], 'industry_allocation': []}
        mock_dashboard_service.return_value.get_performance.return_value = {'total_investment': 10000, 'current_portfolio_value': 15000, 'total_profit': 5000}
        mock_dashboard_service.return_value.get_portfolio_growth_daily.return_value = []
        mock_dashboard_service.return_value.get_sector_wise_performance.return_value = []

        # Act
        response = api_client.get('/investments/dashboard/')

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_investment_performance_validation_error(self, api_client, mock_dashboard_validator, authenticate):
        # Arrange
        authenticate()
        mock_dashboard_validator.validate_request.side_effect = Exception('Validation Error')

        # Act
        response = api_client.get('/investments/dashboard/')

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

    def test_get_investment_performance_service_error(self, api_client, mock_dashboard_service, mock_dashboard_validator, authenticate):
        # Arrange
        authenticate()
        mock_dashboard_validator.validate_request.return_value = None
        mock_dashboard_service.return_value.get_monthly_invested_amount.side_effect = Exception('Service Error')

        # Act
        response = api_client.get('/investments/dashboard/')

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

@pytest.mark.django_db
class TestClientSettingsView:
    def test_get_client_settings_success(self, api_client, mock_settings_service, authenticate):
        # Arrange
        authenticate()
        mock_settings_service.return_value.get_broker_accounts.return_value = []
        mock_settings_service.return_value.get_portfolios.return_value = []

        # Act
        response = api_client.get('/investments/settings/')

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_client_settings_service_error(self, api_client, mock_settings_service, authenticate):
        # Arrange
        authenticate()
        mock_settings_service.return_value.get_broker_accounts.side_effect = Exception('Service Error')

        # Act
        response = api_client.get('/investments/settings/')

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

