import pytest
from rest_framework import status

@pytest.fixture
def mock_holding_service(mocker):
    return mocker.patch('investments.apis.holding_api.HoldingService')

@pytest.fixture
def mock_portfolio_validator(mocker):
    return mocker.patch('investments.apis.holding_api.PortfolioValidator')

@pytest.mark.django_db
class TestHoldingView:

    def test_get_holdings_success(self, mock_holding_service, mock_portfolio_validator, api_client, authenticate):
        # AAA (Arrange, Act, Assert)
        # Arrange
        authenticate()
        mock_portfolio_validator.validate_request.return_value = None
        mock_holding_service.return_value.get_current_holdings.return_value = [{'id': 1, 'company': 'Test Company'}]
        # Act
        response = api_client.get('/investments/holdings/')
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'data': [{'id': 1, 'company': 'Test Company'}], 'status': True, 'message': 'success'}

    def test_get_holdings_failure(self, mock_holding_service, mock_portfolio_validator, api_client, authenticate):
        authenticate()
        mock_portfolio_validator.validate_request.side_effect = Exception('Error')
        mock_holding_service.return_value.get_current_holdings.side_effect = Exception('Error')

        response = api_client.get('/investments/holdings/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'data': None, 'status': False, 'message': 'success'}