import pytest
from rest_framework import status

@pytest.fixture
def mock_holding_service(mocker):
    return mocker.patch('investments.apis.stock_purchase_api.HoldingService')

@pytest.fixture
def mock_stock_purchase_service(mocker):
    return mocker.patch('investments.apis.stock_purchase_api.StockPurchaseService')

@pytest.fixture
def mock_portfolio_validator(mocker):
    return mocker.patch('investments.apis.stock_purchase_api.PortfolioValidator')

@pytest.mark.django_db
class TestStockPurchaseImportApiView:
    def test_stock_purchase_import_success(self, mock_stock_purchase_service, mock_holding_service, api_client,
                                           authenticate):
        authenticate()
        mock_stock_purchase_service.return_value.upload_purchase_files.return_value = ['file1.csv']
        mock_stock_purchase_service.return_value.import_purchases.return_value = [{'trade': 'trade1'}]
        mock_stock_purchase_service.return_value.create_bulk_purchase.return_value = (True, None)
        mock_holding_service.return_value.merge_bulk_holdings.return_value = True

        response = api_client.post('/investments/stocks/purchases/upload/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == True

    def test_stock_purchase_import_file_upload_failure(self, mock_stock_purchase_service, api_client, authenticate):
        authenticate()
        mock_stock_purchase_service.return_value.upload_purchase_files.return_value = None

        response = api_client.post('/investments/stocks/purchases/upload/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == False

    def test_stock_purchase_import_no_trades_imported(self, mock_stock_purchase_service, api_client, authenticate):
        authenticate()
        mock_stock_purchase_service.return_value.upload_purchase_files.return_value = ['file1.csv']
        mock_stock_purchase_service.return_value.import_purchases.return_value = None

        response = api_client.post('/investments/stocks/purchases/upload/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == False

    def test_stock_purchase_import_create_bulk_purchase_failure(self, mock_stock_purchase_service, api_client,
                                                                authenticate):
        authenticate()
        mock_stock_purchase_service.return_value.upload_purchase_files.return_value = ['file1.csv']
        mock_stock_purchase_service.return_value.import_purchases.return_value = [{'trade': 'trade1'}]
        mock_stock_purchase_service.return_value.import_purchases.create_bulk_purchase.return_value = [False, None]

        response = api_client.post('/investments/stocks/purchases/upload/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] == False


@pytest.mark.django_db
class TestStockPurchaseHistoryApiView:
    def test_stock_purchase_history_retrieval_success(self, mock_portfolio_validator, mock_stock_purchase_service, api_client, authenticate):
        authenticate()
        mock_portfolio_validator.return_value.validate_request.return_value = None
        mock_stock_purchase_service.return_value.get_purchase_history.return_value = [{'purchase': 'purchase1'}]

        response = api_client.get('/investments/stocks/purchase/history/', {'portfolio': 1})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == True

    def test_stock_purchase_history_retrieval_failure(self, mock_portfolio_validator, mock_stock_purchase_service, api_client, authenticate):
        authenticate()
        mock_portfolio_validator.return_value.validate_request.return_value = None
        mock_stock_purchase_service.return_value.get_purchase_history.side_effect = Exception('Error')

        response = api_client.get('/investments/stocks/purchase/history/', {'portfolio': 1})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] == False

    def test_stock_purchase_creation_success(self, mock_holding_service, mock_stock_purchase_service, api_client, authenticate):
        authenticate()
        mock_stock_purchase_service.return_value.create_purchase.return_value = (True, {'purchase': 'purchase1'})
        mock_holding_service.return_value.merge_holding.return_value = {'holding': 'holding1'}

        response = api_client.post('/investments/stocks/purchase/history/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == True

    def test_stock_purchase_creation_failure(self, mock_stock_purchase_service, api_client, authenticate):
        authenticate()
        mock_stock_purchase_service.return_value.create_purchase.return_value = (False, None)

        response = api_client.post('/investments/stocks/purchase/history/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == False

    def test_stock_purchase_creation_merge_failure(self, mock_holding_service, mock_stock_purchase_service, api_client, authenticate):
        authenticate()
        mock_stock_purchase_service.return_value.create_purchase.return_value = (True, {'purchase': 'purchase1'})
        mock_holding_service.return_value.merge_holding.return_value = None

        response = api_client.post('/investments/stocks/purchase/history/', data={'account': 1, 'portfolio': 1})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] == False
