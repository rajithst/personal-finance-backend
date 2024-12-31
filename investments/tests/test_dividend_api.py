import pytest
from rest_framework import status

@pytest.fixture
def mock_dividend_service(mocker):
    return mocker.patch('investments.apis.dividend_api.DividendService')
@pytest.mark.django_db
class TestDividendIncomeView:
    def test_get_success(self, api_client, mock_dividend_service, authenticate):
        authenticate()
        mock_dividend_service.return_value.get_dividend_income.return_value = {'income': 100}

        response = api_client.get('/investments/dividends/income/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_failure(self, api_client, mock_dividend_service, authenticate):
        authenticate()
        mock_dividend_service.return_value.get_dividend_income.side_effect = Exception('Error')

        response = api_client.get('/investments/dividends/income/')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False

@pytest.mark.django_db
class TestDividendIncomeDaemonView:
    def test_get_success(self, api_client, mock_dividend_service):
        mock_dividend_service.return_value.calculate_dividend_payments.return_value = {'payments': 100}

        response = api_client.get('/investments/dividends/cron/income/daily/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_failure(self, api_client, mock_dividend_service):
        mock_dividend_service.return_value.calculate_dividend_payments.side_effect = Exception('Error')

        response = api_client.get('/investments/dividends/cron/income/daily/')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False

@pytest.mark.django_db
class TestDividendPaymentDaemonView:
    def test_get_success(self, api_client, mock_dividend_service):
        mock_dividend_service.return_value.enqueue_dividend_refresh_tasks.return_value = {'payments': 100}
        response = api_client.get('/investments/dividends/cron/payments/daily/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_failure(self, api_client, mock_dividend_service):
        mock_dividend_service.return_value.enqueue_dividend_refresh_tasks.side_effect = Exception('Error')
        response = api_client.get('/investments/dividends/cron/payments/daily/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False
