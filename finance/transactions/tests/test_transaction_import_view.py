import pytest
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

IMPORT_ENDPOINT = "/finance/transaction/import/"


@pytest.fixture
def mock_import_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch("finance.transactions.views.TransactionImportService", return_value=mock_service)
    return mock_service


@pytest.mark.django_db
class TestTransactionImportView:
    def test_post_missing_account_id_returns_400(self, api_client, authenticate):
        authenticate()
        file = SimpleUploadedFile("test.csv", b"dummy data", content_type="text/csv")

        response = api_client.post(
            IMPORT_ENDPOINT,
            {"files": [file]},  # account_id is missing
            format="multipart"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False
        assert "Account must be selected" in response.data['message']

    def test_post_missing_files_returns_400(self, api_client, authenticate):
        authenticate()

        response = api_client.post(
            IMPORT_ENDPOINT,
            {"account_id": 1},  # no files
            format="multipart"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False
        assert "No files uploaded" in response.data['message']

    def test_post_failed_file_upload_returns_400(self, api_client, mock_import_service, authenticate):
        authenticate()
        file = SimpleUploadedFile("test.csv", b"dummy data", content_type="text/csv")
        mock_import_service.upload_transaction_files.return_value = []  # no files uploaded

        response = api_client.post(
            IMPORT_ENDPOINT,
            {"account_id": 1, "files": [file]},
            format="multipart"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False
        assert "Failed to upload files" in response.data['message']
        mock_import_service.upload_transaction_files.assert_called_once()

    def test_post_success_upload_failed_import_returns_500(self, api_client, mock_import_service, authenticate):
        authenticate()
        file = SimpleUploadedFile("test.csv", b"dummy data", content_type="text/csv")
        mock_import_service.upload_transaction_files.return_value = [file]
        mock_import_service.import_transactions.return_value = False

        response = api_client.post(
            IMPORT_ENDPOINT,
            {"account_id": 1, "files": [file]},
            format="multipart"
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
        assert "Failed to import" in response.data['message']
        mock_import_service.upload_transaction_files.assert_called_once()
        mock_import_service.import_transactions.assert_called_once()

    def test_post_success_upload_and_import_returns_200(self, api_client, mock_import_service, authenticate):
        authenticate()
        file = SimpleUploadedFile("test.csv", b"dummy data", content_type="text/csv")
        mock_import_service.upload_transaction_files.return_value = [file]
        mock_import_service.import_transactions.return_value = True

        response = api_client.post(
            IMPORT_ENDPOINT,
            {"account_id": 1, "files": [file]},
            format="multipart"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert "Imported Successfully" in response.data['message']
        mock_import_service.upload_transaction_files.assert_called_once()
        mock_import_service.import_transactions.assert_called_once()

    def test_post_with_drop_duplicates_and_import_from_last_date(self, api_client, mock_import_service, authenticate):
        authenticate()
        file = SimpleUploadedFile("test.csv", b"dummy data", content_type="text/csv")
        mock_import_service.upload_transaction_files.return_value = [file]
        mock_import_service.import_transactions.return_value = True

        response = api_client.post(
            IMPORT_ENDPOINT,
            {
                "account_id": 1,
                "files": [file],
                "drop_duplicates": "1",
                "import_from_last_date": "1"
            },
            format="multipart"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        args, kwargs = mock_import_service.import_transactions.call_args
        import_params = args[0]
        assert import_params['drop_duplicates'] is True
        assert import_params['import_from_last_date'] is True
