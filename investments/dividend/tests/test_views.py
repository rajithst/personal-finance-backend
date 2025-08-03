import pytest
from rest_framework import status
from rest_framework.exceptions import ValidationError

DIVIDEND_INCOME_ENDPOINT = '/investments/dividends/income/'
DIVIDEND_PAYMENTS_ENDPOINT = '/investments/dividends/cron/payments/'
DIVIDEND_INCOME_REFRESH_ENDPOINT = '/investments/dividends/income/refresh/'
DIVIDEND_PAYMENTS_REFRESH_ENDPOINT = '/investments/dividends/payments/refresh/'

@pytest.fixture
def mock_dividend_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch('investments.dividend.views.DividendService', return_value=mock_service)
    return mock_service


@pytest.fixture
def mock_dividend_daemon_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch('investments.dividend.views.DividendDaemonService', return_value=mock_service)
    return mock_service


@pytest.fixture
def mock_portfolio_validator(mocker):
    mock_service = mocker.Mock()
    mocker.patch('investments.dividend.views.PortfolioValidator', return_value=mock_service)
    return mock_service


@pytest.mark.django_db
class TestDividendIncomeView:
    def test_get_dividend_income_by_portfolio_id_success(self, api_client, mock_dividend_service, authenticate):
        authenticate()
        mock_dividend_service.get_dividend_income.return_value = {'income': 100}

        response = api_client.get(DIVIDEND_INCOME_ENDPOINT, {'portfolio': 1})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_dividend_income_unauthenticated_request_return_401(self, api_client):
        response = api_client.get(DIVIDEND_INCOME_ENDPOINT, {'portfolio': 1})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


    def test_get_dividend_income_invalid_params_return_400(self, api_client, authenticate):
        authenticate()

        response = api_client.get(DIVIDEND_INCOME_ENDPOINT)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_dividend_income_failure_return_500(self, api_client, mock_dividend_service, authenticate):
        authenticate()
        mock_dividend_service.get_dividend_income.side_effect = Exception('Error')

        response = api_client.get(DIVIDEND_INCOME_ENDPOINT, {'portfolio': 1})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False


@pytest.mark.django_db
class TestDividendIncomeRefresherView:
    def test_calculate_dividend_income_success_return_200(self, api_client, mock_dividend_daemon_service):
        mock_dividend_daemon_service.calculate_dividend_incomes_for_all_portfolios.return_value = {
            'payments': 100}

        response = api_client.get(DIVIDEND_INCOME_REFRESH_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_calculate_dividend_income_failure_return_500(self, api_client, mock_dividend_daemon_service):
        mock_dividend_daemon_service.calculate_dividend_incomes_for_all_portfolios.side_effect = Exception(
            'Error')

        response = api_client.get(DIVIDEND_INCOME_REFRESH_ENDPOINT)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False


@pytest.mark.django_db
class TestDividendPaymentRefreshView:

    def test_update_dividend_history_success_return_200(self, api_client, mock_dividend_daemon_service):
        mock_dividend_daemon_service.update_dividend_history.return_value = 'Updated'

        response = api_client.get(DIVIDEND_PAYMENTS_REFRESH_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_update_dividend_history_failure_return_500(self, api_client, mock_dividend_daemon_service):
        mock_dividend_daemon_service.update_dividend_history.side_effect = Exception('Error')

        response = api_client.get(DIVIDEND_PAYMENTS_REFRESH_ENDPOINT)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False


@pytest.mark.django_db
class TestDividendCronDaemonView:

    def test_refresh_dividend_payments_task_success_return_200(self, api_client, mock_dividend_daemon_service):
        mock_dividend_daemon_service.enqueue_dividend_payment_refresh_tasks.return_value = 'Enqueued'

        response = api_client.get(DIVIDEND_PAYMENTS_ENDPOINT, {'task': 'refresh-dividend-payments'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert response.data['data'] == 'Enqueued'

    def test_refresh_dividend_payments_task_failure_return_500(self, api_client, mock_dividend_daemon_service):
        mock_dividend_daemon_service.enqueue_dividend_payment_refresh_tasks.side_effect = Exception(
            'Error')

        response = api_client.get(DIVIDEND_PAYMENTS_ENDPOINT, {'task': 'refresh-dividend-payments'})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False

    def test_refresh_dividend_payments_invalid_task_return_400(self, api_client):
        response = api_client.get(DIVIDEND_PAYMENTS_ENDPOINT, {'task': 'invalid-task'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False
        assert response.data['message'] == 'Invalid task'
