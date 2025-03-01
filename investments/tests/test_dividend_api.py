import pytest
from rest_framework import status

@pytest.fixture
def mock_dividend_service(mocker):
    return mocker.patch('investments.apis.dividend_api.DividendService')

@pytest.fixture
def mock_dividend_daemon_service(mocker):
    return mocker.patch('investments.apis.dividend_api.DividendDaemonService')

@pytest.fixture
def mock_portfolio_validator(mocker):
    return mocker.patch('investments.apis.dividend_api.PortfolioValidator')

@pytest.mark.django_db
class TestDividendIncomeView:
    def test_get_success(self, api_client, mock_portfolio_validator, mock_dividend_service, authenticate):
        authenticate()
        mock_portfolio_validator.return_value.validate_request.return_value = None
        mock_dividend_service.return_value.get_dividend_income.return_value = {'income': 100}

        response = api_client.get('/investments/dividends/income/', {'portfolio_id': 1})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_failure(self, api_client, mock_portfolio_validator, mock_dividend_service, authenticate):
        authenticate()
        mock_portfolio_validator.return_value.validate_request.return_value = None
        mock_dividend_service.return_value.get_dividend_income.side_effect = Exception('Error')

        response = api_client.get('/investments/dividends/income/', {'portfolio_id': 1})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False

@pytest.mark.django_db
class TestDividendIncomeRefresherView:
    def test_get_success(self, api_client, mock_dividend_daemon_service):
        mock_dividend_daemon_service.return_value.calculate_dividend_incomes_for_all_portfolios.return_value = {'payments': 100}

        response = api_client.get('/investments/dividends/income/refresh/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_failure(self, api_client, mock_dividend_daemon_service):
        mock_dividend_daemon_service.return_value.calculate_dividend_incomes_for_all_portfolios.side_effect = Exception('Error')

        response = api_client.get('/investments/dividends/income/refresh/')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False

@pytest.mark.django_db
class TestDividendPaymentRefreshView:

    def test_update_dividend_history_success(self, api_client, mock_dividend_daemon_service):
        mock_dividend_daemon_service.return_value.update_dividend_history.return_value = 'Updated'

        response = api_client.get('/investments/dividends/payments/refresh/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_update_dividend_history_failure(self, api_client, mock_dividend_daemon_service):
        mock_dividend_daemon_service.return_value.update_dividend_history.side_effect = Exception('Error')

        response = api_client.get('/investments/dividends/payments/refresh/')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False


@pytest.mark.django_db
class TestDividendCronDaemonView:

    def test_refresh_dividend_payments_task_success(self, api_client, mock_dividend_daemon_service):
        mock_dividend_daemon_service.return_value.enqueue_dividend_payment_refresh_tasks.return_value = 'Enqueued'

        response = api_client.get('/investments/cron/dividends/payments/', {'task': 'refresh-dividend-payments'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert response.data['data'] == 'Enqueued'

    def test_refresh_dividend_payments_task_failure(self, api_client, mock_dividend_daemon_service):
        mock_dividend_daemon_service.return_value.enqueue_dividend_payment_refresh_tasks.side_effect = Exception('Error')

        response = api_client.get('/investments/cron/dividends/payments/', {'task': 'refresh-dividend-payments'})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False

    def test_invalid_task(self, api_client):
        response = api_client.get('/investments/cron/dividends/payments/', {'task': 'invalid-task'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert response.data['data'] == 'Invalid task'

