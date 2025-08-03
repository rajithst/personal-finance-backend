import pytest
from rest_framework import status

TRANSACTIONS_ENDPOINT = "/finance/transaction/list/"
TRANSACTION_DETAIL_ENDPOINT = "/finance/transaction/item/{id}/"
BULK_ENDPOINT = "/finance/transaction/bulk/"

@pytest.fixture
def mock_transaction_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch("finance.transactions.views.TransactionListService", return_value=mock_service)
    return mock_service

@pytest.fixture
def mock_bulk_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch("finance.transactions.views.TransactionBulkService", return_value=mock_service)
    return mock_service

@pytest.mark.django_db
class TestTransactionView:
    # ---------- GET ----------
    def test_get_all_transactions_success(self, api_client, mock_transaction_service, authenticate):
        authenticate()
        mock_transaction_service.get_transactions.return_value = [{"id": 1, "amount": 100}]

        response = api_client.get(TRANSACTIONS_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert isinstance(response.data['data'], list)
        assert response.data['data'][0]['amount'] == 100
        mock_transaction_service.get_transactions.assert_called_once()

    def test_get_transaction_by_id_success(self, api_client, mock_transaction_service, authenticate):
        authenticate()
        mock_transaction_service.get_transaction_by_id.return_value = {"id": 1, "amount": 200}

        response = api_client.get(TRANSACTION_DETAIL_ENDPOINT.format(id=1))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert response.data['data']['amount'] == 200
        mock_transaction_service.get_transaction_by_id.assert_called_once_with(1)

    def test_get_transaction_by_id_not_found(self, api_client, mock_transaction_service, authenticate):
        authenticate()
        mock_transaction_service.get_transaction_by_id.return_value = None

        response = api_client.get(TRANSACTION_DETAIL_ENDPOINT.format(id=999))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['status'] is False
        assert "not found" in response.data['message'].lower()

    def test_get_transactions_exception_returns_500(self, api_client, mock_transaction_service, authenticate):
        authenticate()
        mock_transaction_service.get_transactions.side_effect = Exception("Unexpected error")

        response = api_client.get(TRANSACTIONS_ENDPOINT)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
        assert "Unexpected error" in response.data['message']

    # ---------- POST ----------
    def test_post_create_transaction_success(self, api_client, mock_transaction_service, authenticate):
        authenticate()
        mock_transaction_service.create_transaction.return_value = (True, {"id": 1, "amount": 150})

        payload = {"amount": 150}
        response = api_client.post(TRANSACTIONS_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] is True
        assert response.data['data']['amount'] == 150
        mock_transaction_service.create_transaction.assert_called_once_with(payload)

    def test_post_with_update_similar_calls_both_methods(self, api_client, mock_transaction_service, authenticate):
        authenticate()
        mock_transaction_service.create_transaction.return_value = (True, {"id": 1, "amount": 150})

        payload = {"amount": 150, "update_similar": True}
        response = api_client.post(TRANSACTIONS_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        mock_transaction_service.update_similar_transactions.assert_called_once_with(payload)
        mock_transaction_service.create_transaction.assert_called_once_with(payload)

    def test_post_failure_returns_400(self, api_client, mock_transaction_service, authenticate):
        authenticate()
        mock_transaction_service.create_transaction.return_value = (False, {"error": "Invalid data"})

        payload = {"amount": 150}
        response = api_client.post(TRANSACTIONS_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False if response.data else True

    def test_post_exception_returns_500(self, api_client, mock_transaction_service, authenticate):
        authenticate()
        mock_transaction_service.create_transaction.side_effect = Exception("Unexpected error")

        payload = {"amount": 150}
        response = api_client.post(TRANSACTIONS_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
        assert "Unexpected error" in response.data['message']

    # ---------- PUT ----------
    def test_put_update_transaction_success(self, api_client, mock_transaction_service, authenticate):
        authenticate()
        mock_transaction_service.update_transaction.return_value = (True, {"id": 1, "amount": 175})

        payload = {"id": 1, "amount": 175}
        response = api_client.put(TRANSACTIONS_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert response.data['data']['amount'] == 175
        mock_transaction_service.update_transaction.assert_called_once_with(payload)

    def test_put_with_merge_and_update_similar(self, api_client, mock_transaction_service, authenticate):
        authenticate()
        mock_transaction_service.update_transaction.return_value = (True, {"id": 1, "amount": 175})

        payload = {"id": 1, "amount": 175, "merge_ids": [2, 3], "update_similar": True}
        response = api_client.put(TRANSACTIONS_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        mock_transaction_service.merge_transactions.assert_called_once_with(payload)
        mock_transaction_service.update_similar_transactions.assert_called_once_with(payload)
        mock_transaction_service.update_transaction.assert_called_once_with(payload)

    def test_put_failure_returns_400(self, api_client, mock_transaction_service, authenticate):
        authenticate()
        mock_transaction_service.update_transaction.return_value = (False, {"error": "Invalid data"})

        payload = {"id": 1, "amount": 175}
        response = api_client.put(TRANSACTIONS_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_exception_returns_500(self, api_client, mock_transaction_service, authenticate):
        authenticate()
        mock_transaction_service.update_transaction.side_effect = Exception("Unexpected error")

        payload = {"id": 1, "amount": 175}
        response = api_client.put(TRANSACTIONS_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
        assert "Unexpected error" in response.data['message']

@pytest.mark.django_db
class TestTransactionBulkView:
    # ---------- DELETE ----------
    def test_bulk_delete_success(self, api_client, mock_bulk_service, authenticate):
        authenticate()
        mock_bulk_service.bulk_delete.return_value = (True, {"deleted": [1, 2]})

        payload = {"task": "delete", "ids": [1, 2]}
        response = api_client.put(BULK_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert response.data['data']['deleted'] == [1, 2]
        mock_bulk_service.bulk_delete.assert_called_once_with(payload)

    def test_bulk_delete_failure(self, api_client, mock_bulk_service, authenticate):
        authenticate()
        mock_bulk_service.bulk_delete.return_value = (False, {"error": "Not found"})

        payload = {"task": "delete", "ids": [99]}
        response = api_client.put(BULK_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False
        assert "Failed" in response.data['message']
        mock_bulk_service.bulk_delete.assert_called_once_with(payload)

    # ---------- SPLIT ----------
    def test_bulk_split_success(self, api_client, mock_bulk_service, authenticate):
        authenticate()
        mock_bulk_service.split_transactions.return_value = (True, {"split": [1, 2]})

        payload = {"task": "split", "transactions": [{"id": 1}, {"id": 2}]}
        response = api_client.put(BULK_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert response.data['data']['split'] == [1, 2]
        mock_bulk_service.split_transactions.assert_called_once_with(payload)

    def test_bulk_split_failure(self, api_client, mock_bulk_service, authenticate):
        authenticate()
        mock_bulk_service.split_transactions.return_value = (False, {"error": "Invalid data"})

        payload = {"task": "split", "transactions": [{"id": 1}]}
        response = api_client.put(BULK_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False
        assert "Failed" in response.data['message']
        mock_bulk_service.split_transactions.assert_called_once_with(payload)

    # ---------- INVALID TASK ----------
    def test_invalid_task_returns_failed_response(self, api_client, mock_bulk_service, authenticate):
        authenticate()
        payload = {"task": "invalid_task"}
        response = api_client.put(BULK_ENDPOINT, payload, format="json")

        # No service method should be called
        mock_bulk_service.bulk_delete.assert_not_called()
        mock_bulk_service.split_transactions.assert_not_called()

        # Should still return 400 since status=False
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

    # ---------- EXCEPTION ----------
    def test_exception_returns_500(self, api_client, mock_bulk_service, authenticate):
        authenticate()
        mock_bulk_service.bulk_delete.side_effect = Exception("Unexpected error")

        payload = {"task": "delete", "ids": [1, 2]}
        response = api_client.put(BULK_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
        assert "Unexpected error" in response.data['message']