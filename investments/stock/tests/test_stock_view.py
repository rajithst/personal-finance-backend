import pytest
from rest_framework import status

@pytest.fixture
def mock_stock_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch('investments.stock.api.stock_api.StockService', return_value=mock_service)
    return mock_service

@pytest.fixture
def mock_stock_daemon_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch('investments.stock.api.stock_api.StockDaemonService', return_value=mock_service)
    return mock_service

@pytest.mark.django_db
class TestStockValueRefreshView:
    def test_update_daily_price_success_return_200(self, api_client, mock_stock_service):
        mock_stock_service.update_daily_price.return_value = {'price': 100}

        response = api_client.get('/investments/stocks/value/refresh/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_update_daily_price_failure_return_400(self, api_client, mock_stock_service):
        mock_stock_service.update_daily_price.return_value = None

        response = api_client.get('/investments/stocks/value/refresh/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

    def test_update_daily_price_service_error_return_500(self, api_client, mock_stock_service):
        mock_stock_service.update_daily_price.side_effect = Exception('Service Error')

        response = api_client.get('/investments/stocks/value/refresh/')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False

@pytest.mark.django_db
class TestStockSplitRefreshView:
    def test_update_daily_stock_split_return_200(self, api_client, mock_stock_service):
        mock_stock_service.update_daily_stock_split.return_value = [
            {'symbol': 'AAPL', 'split_ratio': 2.0},
            {'symbol': 'GOOGL', 'split_ratio': 1.5}
        ]

        response = api_client.get('/investments/stocks/splits/refresh/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_update_daily_stock_split_failure_return_400(self, api_client, mock_stock_service):
        mock_stock_service.update_daily_stock_split.return_value = None

        response = api_client.get('/investments/stocks/splits/refresh/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

    def test_update_daily_stock_split_service_error_return_500(self, api_client, mock_stock_service):
        mock_stock_service.update_daily_stock_split.side_effect = Exception('Service Error')

        response = api_client.get('/investments/stocks/splits/refresh/')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False

@pytest.mark.django_db
class TestStockPriceHistoryView:
    def test_get_price_history_return_200(self, api_client, mock_stock_service, authenticate):
        authenticate()
        mock_stock_service.get_price_history.return_value = [{'price': 100}]

        response = api_client.get('/investments/stocks/price/history/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_price_history_failure_return_500(self, api_client, mock_stock_service, authenticate):
        authenticate()
        mock_stock_service.get_price_history.side_effect = Exception('Service Error')

        response = api_client.get('/investments/stocks/price/history/')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False

@pytest.mark.django_db
class TestBulkStockValueUpdaterView:
    def test_sync_historical_data_success_return_200(self, api_client, mock_stock_service):
        mock_stock_service.sync_historical_data.return_value = {'synced': True}

        response = api_client.get('/investments/stocks/historical-data/fetch/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_sync_historical_data_failure_return_500(self, api_client, mock_stock_service):
        mock_stock_service.sync_historical_data.side_effect = Exception('Service Error')

        response = api_client.get('/investments/stocks/historical-data/fetch/')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False

@pytest.mark.django_db
class TestStockValueDaemonView:
    def test_enqueue_stocks_value_refresh_task_success_return_200(self, api_client, mock_stock_daemon_service):
        mock_stock_daemon_service.enqueue_stocks_value_refresh_task.return_value = {'synced': True}

        response = api_client.get('/investments/stocks/cron/market-value/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_enqueue_stocks_value_refresh_task_failure_return_500(self, api_client, mock_stock_daemon_service):
        mock_stock_daemon_service.enqueue_stocks_value_refresh_task.side_effect = Exception('Service Error')

        response = api_client.get('/investments/stocks/cron/market-value/')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False

@pytest.mark.django_db
class TestStockSplitDaemonView:
    def test_enqueue_stocks_split_refresh_task_success_return_200(self, api_client, mock_stock_daemon_service):
        mock_stock_daemon_service.enqueue_stocks_split_refresh_task.return_value = {'synced': True}

        response = api_client.get('/investments/stocks/cron/splits/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_enqueue_stocks_split_refresh_task_failure_return_500(self, api_client, mock_stock_daemon_service):
        mock_stock_daemon_service.enqueue_stocks_split_refresh_task.side_effect = Exception('Service Error')

        response = api_client.get('/investments/stocks/cron/splits/')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
