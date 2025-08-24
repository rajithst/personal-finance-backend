import pytest
from rest_framework import status

ENDPOINT = "/accounts/credit/"


@pytest.fixture
def mock_category_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch("accounts.views.CreditAccountService", return_value=mock_service)
    return mock_service

@pytest.mark.django_db
class TestAccountsView:

    def test_create_account_success_returns_201(self, api_client, mock_category_service, authenticate):
        authenticate()
        mock_category_service.create_account.return_value = {'id': 1, 'name': 'Test Account'}

        payload = {"name": "Test Account"}
        response = api_client.post(ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] is True

    def test_create_account_failure_returns_500(self, api_client, mock_category_service, authenticate):
        authenticate()
        mock_category_service.create_account.side_effect = Exception("Creation error")

        payload = {"name": "Bad Account"}
        response = api_client.post(ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False

    def test_create_account_unauthenticated_returns_403(self, api_client, mock_category_service):
        payload = {"name": "Test Account"}
        response = api_client.post(ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_account_success_returns_200(self, api_client, mock_category_service, authenticate):
        authenticate()
        mock_category_service.update_account.return_value = {'id': 1, 'name': 'Updated Account'}

        payload = {"id": 1, "name": "Updated Account"}
        response = api_client.put(ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_update_account_failure_returns_500(self, api_client, mock_category_service, authenticate):
        authenticate()
        mock_category_service.update_account.side_effect = Exception("Update error")

        payload = {"id": 1, "name": "Bad Account"}
        response = api_client.put(ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False

    def test_update_account_unauthenticated_returns_403(self, api_client, mock_category_service):
        payload = {"id": 1, "name": "Updated Account"}
        response = api_client.put(ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED