import pytest
from rest_framework import status

ENDPOINT = '/investments/portfolio/'

@pytest.fixture
def mock_portfolio_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch('investments.portfolio.views.PortfolioService', return_value=mock_service)
    return mock_service

@pytest.fixture
def mock_portfolio_growth_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch('investments.portfolio.views.PortfolioGrowthService', return_value=mock_service)
    return mock_service

@pytest.fixture
def mock_portfolio_growth_daemon_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch('investments.portfolio.views.PortfolioGrowthDaemonService', return_value=mock_service)
    return mock_service

@pytest.mark.django_db
class TestPortfolioSettingsView:
    def test_create_portfolio_settings_success_return_201(self, api_client, mock_portfolio_service, authenticate):
        # Arrange
        authenticate()
        mock_portfolio_service.create_portfolio.return_value = {'id': 1}

        # Act
        response = api_client.post(ENDPOINT, data={'name': 'Test Portfolio'})

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] is True

    def test_create_portfolio_settings_error_return_400(self, api_client, mock_portfolio_service, authenticate):
        # Arrange
        authenticate()
        mock_portfolio_service.create_portfolio.side_effect = Exception('Service Error')

        # Act
        response = api_client.post(ENDPOINT, data={'name': 'Test Portfolio'})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

    def test_create_portfolio_settings_unauthenticated_request_return_401(self, api_client, mock_portfolio_service):
        # Arrange
        mock_portfolio_service.create_portfolio.return_value = {'id': 1}

        # Act
        response = api_client.post(ENDPOINT, data={'name': 'Test Portfolio'})

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_portfolio_settings_success_return_200(self, api_client, mock_portfolio_service, authenticate):
        # Arrange
        authenticate()
        mock_portfolio_service.update_portfolio.return_value = {'id': 1}

        # Act
        response = api_client.put(ENDPOINT, data={'id': 1, 'name': 'Updated Portfolio'})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_update_portfolio_settings_error_return_400(self, api_client, mock_portfolio_service, authenticate):
        # Arrange
        authenticate()
        mock_portfolio_service.update_portfolio.side_effect = Exception('Service Error')

        # Act
        response = api_client.put(ENDPOINT, data={'id': 1, 'name': 'Updated Portfolio'})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

    def test_update_portfolio_settings_unauthenticated_request_return_401(self, api_client, mock_portfolio_service):
        # Arrange
        mock_portfolio_service.create_portfolio.return_value = {'id': 1}

        # Act
        response = api_client.put(ENDPOINT, data={'id': 1, 'name': 'Updated Portfolio'})

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
class TestPortfolioGrowthRefreshView:
    def test_update_portfolio_growth_success_return_200(self, api_client, mock_portfolio_growth_service, authenticate):
        # Arrange
        authenticate()
        mock_portfolio_growth_service.update_portfolio_growth.return_value = {'growth': 10}

        # Act
        response = api_client.get(f'{ENDPOINT}growth/refresh/', {'portfolio': 1})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_update_portfolio_growth_error_return_400(self, api_client, mock_portfolio_growth_service, authenticate):
        # Arrange
        authenticate()
        mock_portfolio_growth_service.update_portfolio_growth.side_effect = Exception('Service Error')

        # Act
        response = api_client.get(f'{ENDPOINT}growth/refresh/', {'portfolio': 1})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

@pytest.mark.django_db
class TestPortfolioGrowthDaemonView:
    def test_enqueue_portfolio_growth_refresh_tasks_success_return_200(self, api_client, mock_portfolio_growth_daemon_service, authenticate):
        # Arrange
        authenticate()
        mock_portfolio_growth_daemon_service.enqueue_portfolio_growth_refresh_tasks.return_value = {'tasks': 5}

        # Act
        response = api_client.get(f'{ENDPOINT}cron/growth/')

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_enqueue_portfolio_growth_refresh_tasks_error_return_400(self, api_client, mock_portfolio_growth_daemon_service, authenticate):
        # Arrange
        authenticate()
        mock_portfolio_growth_daemon_service.enqueue_portfolio_growth_refresh_tasks.side_effect = Exception('Service Error')

        # Act
        response = api_client.get(f'{ENDPOINT}cron/growth/')

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False