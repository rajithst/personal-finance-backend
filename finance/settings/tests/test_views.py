import pytest
from rest_framework import status

CLIENT_SETTINGS_ENDPOINT = "/finance/settings/"


@pytest.fixture
def mock_settings_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch("finance.settings.views.SettingsService", return_value=mock_service)
    return mock_service


@pytest.mark.django_db
class TestClientSettings:
    def test_get_settings_success_return_200(self, api_client, mock_settings_service, authenticate):
        authenticate()
        mock_settings_service.get_credit_accounts.return_value = [{"id": 1, "name": "Credit Account"}]
        mock_settings_service.get_transaction_categories.return_value = [{"id": 10, "name": "Food"}]
        mock_settings_service.get_transaction_subcategories.return_value = [{"id": 101, "name": "Groceries"}]
        mock_settings_service.get_account_types.return_value = [{"id": 20, "name": "Savings"}]
        mock_settings_service.get_account_providers.return_value = [{"id": 30, "name": "Bank A"}]

        response = api_client.get(CLIENT_SETTINGS_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert response.data['data']['accounts'][0]['name'] == "Credit Account"
        assert response.data['data']['transaction_categories'][0]['name'] == "Food"
        assert response.data['data']['transaction_subcategories'][0]['name'] == "Groceries"
        assert response.data['data']['account_types'][0]['name'] == "Savings"
        assert response.data['data']['account_providers'][0]['name'] == "Bank A"

        mock_settings_service.get_credit_accounts.assert_called_once()
        mock_settings_service.get_transaction_categories.assert_called_once()
        mock_settings_service.get_transaction_subcategories.assert_called_once()
        mock_settings_service.get_account_types.assert_called_once()
        mock_settings_service.get_account_providers.assert_called_once()

    def test_get_settings_unauthenticated_request_return_403(self, api_client):
        response = api_client.get(CLIENT_SETTINGS_ENDPOINT)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


    def test_get_settings_exception_returns_500(self, api_client, mock_settings_service, authenticate):
        authenticate()
        mock_settings_service.get_credit_accounts.side_effect = Exception("Unexpected error")

        response = api_client.get(CLIENT_SETTINGS_ENDPOINT)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
        assert "Unexpected error" in response.data['message']
