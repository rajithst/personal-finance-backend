import pytest
from rest_framework import status
from rest_framework.permissions import AllowAny

ENDPOINT = '/investments/stocks/holdings/'
DAEMON_ENDPOINT = '/investments/stocks/cron/holding/value/'

@pytest.fixture
def mock_holding_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch('investments.stock.api.holding_api.HoldingService', return_value=mock_service)
    return mock_service

@pytest.fixture
def mock_holding_daemon_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch('investments.stock.api.holding_api.HoldingDaemonService', return_value=mock_service)
    return mock_service

@pytest.mark.django_db
class TestHoldingView:

    def test_get_holdings_success_return_200(self, mock_holding_service, api_client, authenticate):
        authenticate()
        mock_holding_service.get_current_holdings.return_value = [{'id': 1, 'company': 'Test Company'}]
        # Act
        response = api_client.get(ENDPOINT, data={'portfolio': 1})
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'data': [{'id': 1, 'company': 'Test Company'}], 'status': True, 'message': 'success'}

    def test_get_holdings_success_invalid_params_return_400(self, mock_holding_service, api_client, authenticate):
        authenticate()
        mock_holding_service.get_current_holdings.return_value = [{'id': 1, 'company': 'Test Company'}]
        # Act
        response = api_client.get(ENDPOINT)
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_holdings_failure_return_500(self, mock_holding_service, api_client, authenticate):
        authenticate()
        mock_holding_service.get_current_holdings.side_effect = Exception('Error')

        response = api_client.get(ENDPOINT, data={'portfolio': 1})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_holdings_unauthenticated_request_return_401(self, api_client):
        response = api_client.get(ENDPOINT, data={'portfolio': 1})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestHoldingValueRefresherView:
    permission_classes = [AllowAny]

    def test_refresh_holdings_success_return_200(self, mock_holding_service, api_client):
        mock_holding_service.refresh_holdings_with_current_price.return_value = True

        response = api_client.get(ENDPOINT + 'refresh/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_refresh_holdings_failure_return_500(self, mock_holding_service, api_client):
        mock_holding_service.refresh_holdings_with_current_price.side_effect = Exception('Error')

        response = api_client.get(ENDPOINT + 'refresh/')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False


class TestHoldingDaemonView:
    permission_classes = [AllowAny]

    def test_enqueue_holdings_refresh_task_success_return_200(self, mock_holding_daemon_service, api_client):
        mock_holding_daemon_service.enqueue_holding_values_refresh_tasks.return_value = True

        response = api_client.get(DAEMON_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_enqueue_holdings_refresh_task_failure_return_500(self, mock_holding_daemon_service, api_client):
        mock_holding_daemon_service.enqueue_holding_values_refresh_tasks.side_effect = Exception('Error')

        response = api_client.get(DAEMON_ENDPOINT)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False