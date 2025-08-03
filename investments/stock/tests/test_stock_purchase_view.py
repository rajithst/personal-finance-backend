import pytest
from rest_framework import status


@pytest.fixture
def mock_holding_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch('investments.stock.api.stock_purchase_api.HoldingService', return_value=mock_service)
    return mock_service

@pytest.fixture
def mock_stock_purchase_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch('investments.stock.api.stock_purchase_api.StockPurchaseService', return_value=mock_service)
    return mock_service

@pytest.mark.django_db
class TestStockPurchaseImportApiView:
    def test_stock_purchase_import_success_return_200(self, mock_stock_purchase_service, mock_holding_service, api_client,
                                           authenticate):
        authenticate()
        mock_stock_purchase_service.upload_purchase_files.return_value = ['file1.csv']
        mock_stock_purchase_service.import_purchases.return_value = [{'trade': 'trade1'}]
        mock_stock_purchase_service.create_bulk_purchase.return_value = (True, None)
        mock_holding_service.merge_bulk_holdings.return_value = True

        response = api_client.post('/investments/stocks/purchases/upload/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == True

    def test_stock_purchase_import_file_upload_failure_return_400(self, mock_stock_purchase_service, api_client, authenticate):
        authenticate()
        mock_stock_purchase_service.upload_purchase_files.return_value = None

        response = api_client.post('/investments/stocks/purchases/upload/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == False

    def test_stock_purchase_import_no_trades_imported_return_400(self, mock_stock_purchase_service, api_client, authenticate):
        authenticate()
        mock_stock_purchase_service.upload_purchase_files.return_value = ['file1.csv']
        mock_stock_purchase_service.import_purchases.return_value = None

        response = api_client.post('/investments/stocks/purchases/upload/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == False

    def test_stock_purchase_import_create_bulk_purchase_failure_return_500(self, mock_stock_purchase_service, api_client,
                                                                authenticate):
        authenticate()
        mock_stock_purchase_service.upload_purchase_files.return_value = ['file1.csv']
        mock_stock_purchase_service.import_purchases.return_value = [{'trade': 'trade1'}]
        mock_stock_purchase_service.import_purchases.create_bulk_purchase.return_value = [False, None]

        response = api_client.post('/investments/stocks/purchases/upload/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] == False

    def test_stock_purchase_import_create_bulk_service_failure_return_500(self, mock_stock_purchase_service, api_client,
                                                                authenticate):
        authenticate()
        mock_stock_purchase_service.upload_purchase_files.return_value = ['file1.csv']
        mock_stock_purchase_service.import_purchases.return_value = [{'trade': 'trade1'}]
        mock_stock_purchase_service.import_purchases.create_bulk_purchase.side_effect = Exception('Error')

        response = api_client.post('/investments/stocks/purchases/upload/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] == False


@pytest.mark.django_db
class TestStockPurchaseHistoryApiView:
    def test_stock_purchase_history_retrieval_success_return_200(self, mock_stock_purchase_service,
                                                      api_client, authenticate):
        authenticate()
        mock_stock_purchase_service.get_purchase_history.return_value = [{'purchase': 'purchase1'}]

        response = api_client.get('/investments/stocks/purchase/history/', {'portfolio': 1})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == True

    def test_stock_purchase_history_retrieval_invalid_params_return_400(self, api_client, authenticate):
        authenticate()

        response = api_client.get('/investments/stocks/purchase/history/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == False

    def test_stock_purchase_history_retrieval_failure_return_500(self, mock_stock_purchase_service,
                                                      api_client, authenticate):
        authenticate()
        mock_stock_purchase_service.get_purchase_history.side_effect = Exception('Error')

        response = api_client.get('/investments/stocks/purchase/history/', {'portfolio': 1})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] == False

    def test_stock_purchase_creation_success_return_201(self, mock_holding_service, mock_stock_purchase_service, api_client,
                                             authenticate):
        authenticate()
        mock_stock_purchase_service.create_purchase.return_value = (True, {'purchase': 'purchase1'})
        mock_holding_service.merge_holding.return_value = {'holding': 'holding1'}

        response = api_client.post('/investments/stocks/purchase/history/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == True

    def test_stock_purchase_creation_failure_return_400(self, mock_stock_purchase_service, api_client, authenticate):
        authenticate()
        mock_stock_purchase_service.create_purchase.return_value = (False, None)

        response = api_client.post('/investments/stocks/purchase/history/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == False

    def test_stock_purchase_creation_merge_failure_return_400(self, mock_holding_service, mock_stock_purchase_service, api_client,
                                                   authenticate):
        authenticate()
        mock_stock_purchase_service.create_purchase.return_value = (True, {'purchase': 'purchase1'})
        mock_holding_service.merge_holding.return_value = None

        response = api_client.post('/investments/stocks/purchase/history/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == False

    def test_stock_purchase_creation_service_failure_return_500(self, mock_holding_service, mock_stock_purchase_service, api_client,
                                                   authenticate):
        authenticate()
        mock_stock_purchase_service.create_purchase.return_value = (True, {'purchase': 'purchase1'})
        mock_holding_service.merge_holding.side_effect = Exception('Error')

        response = api_client.post('/investments/stocks/purchase/history/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] == False