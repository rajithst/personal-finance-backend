import pytest
from rest_framework import status
from rest_framework.exceptions import ValidationError

DASHBOARD_ENDPOINT = "/finance/dashboard/"

@pytest.fixture
def mock_dashboard_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch("finance.dashboard.views.DashboardService", return_value=mock_service)
    return mock_service

@pytest.mark.django_db
class TestDashboardView:
    def test_get_success_return_200(self, api_client, mock_dashboard_service, authenticate):
        authenticate()
        # Mock all DashboardService methods
        mock_dashboard_service.get_income.return_value = 1000
        mock_dashboard_service.get_expense.return_value = 500
        mock_dashboard_service.get_payment.return_value = 200
        mock_dashboard_service.get_saving.return_value = 300
        mock_dashboard_service.get_monthly_expense_category_summary.return_value = []
        mock_dashboard_service.get_monthly_payment_account_summary.return_value = []
        mock_dashboard_service.get_monthly_payment_payee_summary.return_value = []
        mock_dashboard_service.get_top_ten_expenses.return_value = []

        params = {"year": "2024"}
        response = api_client.get(DASHBOARD_ENDPOINT, params)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert response.data['data']['income'] == 1000
        assert response.data['data']['expense'] == 500
        mock_dashboard_service.get_income.assert_called_once_with("2024")

    def test_get_missing_year_returns_400(self, api_client, authenticate):
        authenticate()

        response = api_client.get(DASHBOARD_ENDPOINT)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False
        assert "year" in str(response.data['message'])

    def test_get_service_exception_returns_500(self, api_client, mock_dashboard_service, authenticate):
        authenticate()
        mock_dashboard_service.get_income.side_effect = Exception("Unexpected error")

        params = {"year": "2024"}
        response = api_client.get(DASHBOARD_ENDPOINT, params)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
        assert "Unexpected error" in response.data['message']
