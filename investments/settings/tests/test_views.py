import pytest
from rest_framework import status

ENDPOINT = '/investments/settings/'
@pytest.fixture
def mock_dashboard_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch('investments.settings.views.SettingsService', return_value=mock_service)
    return mock_service

@pytest.mark.django_db
class TestClientSettingsView:
    def test_get_client_settings_success_return_200(self, api_client, mock_dashboard_service, authenticate):
        # Arrange
        authenticate()
        mock_dashboard_service.get_broker_accounts.return_value = []
        mock_dashboard_service.get_portfolios.return_value = []

        # Act
        response = api_client.get(ENDPOINT)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_client_settings_unauthenticated_request_return_401(self, api_client):
        response = api_client.get(ENDPOINT)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_client_settings_service_failure_return_500(self, api_client, mock_dashboard_service, authenticate):
        # Arrange
        authenticate()
        mock_dashboard_service.get_broker_accounts.side_effect = Exception('Service Error')

        # Act
        response = api_client.get(ENDPOINT)

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False