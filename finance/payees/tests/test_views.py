import pytest
from rest_framework import status

PAYEE_ENDPOINT = "/finance/payees/list/"
PAYEE_DETAIL_ENDPOINT = "/finance/payees/item/{id}/"

@pytest.fixture
def mock_payee_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch("finance.payees.views.PayeeService", return_value=mock_service)
    return mock_service


@pytest.mark.django_db
class TestPayeeView:
    def test_get_all_payees_success_return_200(self, api_client, mock_payee_service, authenticate):
        authenticate()
        mock_payee_service.get_payees.return_value = [{"id": 1, "name": "Payee1"}]

        response = api_client.get(PAYEE_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert isinstance(response.data['data'], list)
        assert response.data['data'][0]['name'] == "Payee1"
        mock_payee_service.get_payees.assert_called_once()

    def test_get_payee_by_id_success_return_200(self, api_client, mock_payee_service, authenticate):
        authenticate()
        mock_payee_service.get_payee_by_id_or_name.return_value = {"payee": {"id": 1, "name": "Payee1"}}

        response = api_client.get(PAYEE_DETAIL_ENDPOINT.format(id=1))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert response.data['data']['payee']['name'] == "Payee1"
        mock_payee_service.get_payee_by_id_or_name.assert_called_once_with({"id": 1, "name": None})

    def test_get_payee_by_id_not_found_return_404(self, api_client, mock_payee_service, authenticate):
        authenticate()
        mock_payee_service.get_payee_by_id_or_name.return_value = {}

        response = api_client.get(PAYEE_DETAIL_ENDPOINT.format(id=999))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['status'] is False
        mock_payee_service.get_payee_by_id_or_name.assert_called_once_with({"id": 999, "name": None})

    def test_get_exception_returns_500(self, api_client, mock_payee_service, authenticate):
        authenticate()
        mock_payee_service.get_payees.side_effect = Exception("Unexpected error")

        response = api_client.get(PAYEE_ENDPOINT)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
        assert "Unexpected error" in response.data['message']

    def test_put_update_payee_success_return_200(self, api_client, mock_payee_service, authenticate):
        authenticate()
        mock_payee_service.update_payee.return_value = (True, {"id": 1, "name": "UpdatedPayee"})

        payload = {"id": 1, "name": "UpdatedPayee"}
        response = api_client.put(PAYEE_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert response.data['data']['name'] == "UpdatedPayee"
        mock_payee_service.update_payee.assert_called_once_with(payload)

    def test_put_update_payee_failure_return_400(self, api_client, mock_payee_service, authenticate):
        authenticate()
        mock_payee_service.update_payee.return_value = (False, {"error": "Invalid data"})

        payload = {"id": 1, "name": ""}
        response = api_client.put(PAYEE_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False
        assert "Failed to update payee" in response.data['message']
        mock_payee_service.update_payee.assert_called_once_with(payload)

    def test_put_update_payee_exception_return_500(self, api_client, mock_payee_service, authenticate):
        authenticate()
        mock_payee_service.update_payee.side_effect = Exception("Unexpected error")

        payload = {"id": 1, "name": "UpdatedPayee"}
        response = api_client.put(PAYEE_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
        assert "Unexpected error" in response.data['message']
