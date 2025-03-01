import pytest
from rest_framework import status

@pytest.fixture
def mock_forex_service(mocker):
    return mocker.patch('investments.apis.forex_api.ForexService')

@pytest.mark.django_db
class TestDailyForexValueDaemonView:
    def test_get_success(self, api_client, mock_forex_service):
        # Arrange
        mock_forex_service.return_value.update_daily_price.return_value = {'price': 1.2}

        # Act
        response = api_client.get('/investments/cron/forex/value/')

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_failure(self, api_client, mock_forex_service):
        # Arrange
        mock_forex_service.return_value.update_daily_price.side_effect = Exception('Error')

        # Act
        response = api_client.get('/investments/cron/forex/value/')

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False