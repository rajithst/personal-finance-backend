import pytest
from rest_framework import status

@pytest.fixture
def mock_stock_service(mocker):
    return mocker.patch('investments.apis.stock_api.StockService')
@pytest.mark.django_db
class TestDailyStockValueDaemonView:
    def test_get_success(self, api_client, mock_stock_service):
        mock_stock_service.return_value.update_daily_price.return_value = {'price': 100}

        response = api_client.get('/investments/stocks/value/refresh/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_failure(self, api_client, mock_stock_service):
        mock_stock_service.return_value.update_daily_price.return_value = None

        response = api_client.get('/investments/stocks/value/refresh/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

@pytest.mark.django_db
class TestStockPriceHistoryView:
    def test_get_success(self, api_client, mock_stock_service, authenticate):
        authenticate()
        mock_stock_service.return_value.get_price_history.return_value = [{'price': 100}]

        response = api_client.get('/investments/stocks/price/history/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_failure(self, api_client, mock_stock_service, authenticate):
        authenticate()
        mock_stock_service.return_value.get_price_history.return_value = None
        response = api_client.get('/investments/stocks/price/history/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert response.data['data'] == []

@pytest.mark.django_db
class TestBulkStockValueUpdaterView:
    def test_get_success(self, api_client, mock_stock_service):
        mock_stock_service.return_value.sync_historical_data.return_value = {'synced': True}

        response = api_client.get('/investments/stocks/historical-data/fetch/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_failure(self, api_client, mock_stock_service):
        mock_stock_service.return_value.sync_historical_data.return_value = None

        response = api_client.get('/investments/stocks/historical-data/fetch/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False