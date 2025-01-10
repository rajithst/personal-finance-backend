import pytest
from rest_framework import status


@pytest.fixture
def mock_portfolio_service(mocker):
    return mocker.patch('investments.apis.portfolio_api.PortfolioService')
@pytest.mark.django_db
class TestPortfolioSettingsView:
    def test_post_portfolio_settings_success(self, api_client, mock_portfolio_service, authenticate):
        # Arrange
        authenticate()
        mock_portfolio_service.return_value.create_portfolio.return_value = {'id': 1}

        # Act
        response = api_client.post('/investments/portfolio/', data={'name': 'Test Portfolio'})

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] is True

    def test_post_portfolio_settings_service_error(self, api_client, mock_portfolio_service, authenticate):
        # Arrange
        authenticate()
        mock_portfolio_service.return_value.create_portfolio.side_effect = Exception('Service Error')

        # Act
        response = api_client.post('/investments/portfolio/', data={'name': 'Test Portfolio'})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

    def test_put_portfolio_settings_success(self, api_client, mock_portfolio_service, authenticate):
        # Arrange
        authenticate()
        mock_portfolio_service.return_value.update_portfolio.return_value = {'id': 1}

        # Act
        response = api_client.put('/investments/portfolio/', data={'id': 1, 'name': 'Updated Portfolio'})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_put_portfolio_settings_service_error(self, api_client, mock_portfolio_service, authenticate):
        # Arrange
        authenticate()
        mock_portfolio_service.return_value.update_portfolio.side_effect = Exception('Service Error')

        # Act
        response = api_client.put('/investments/portfolio/', data={'id': 1, 'name': 'Updated Portfolio'})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False