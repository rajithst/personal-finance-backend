import pytest
from rest_framework import status

DETAIL_ENDPOINT = '/investments/company/detail/fetch/'
LIST_ENDPOINT = "/investments/company/list/"

@pytest.fixture
def mock_company_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch("investments.company.views.CompanyService", return_value=mock_service)
    return mock_service

@pytest.mark.django_db
class TestCompanyValueUpdaterView:
    def test_fetch_company_info_success_return_200(self, api_client, mock_company_service):
        mock_company_service.fetch_company_info.return_value = (True, {'info': 'company data'})

        response = api_client.get(DETAIL_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_fetch_company_info_failure_return_500(self, api_client, mock_company_service):
        mock_company_service.fetch_company_info.return_value = (False, 'error')

        response = api_client.get(DETAIL_ENDPOINT)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False

    def test_fetch_company_info_exception_returns_500(self, api_client, mock_company_service):
        mock_company_service.fetch_company_info.side_effect = Exception('Error')

        response = api_client.get(DETAIL_ENDPOINT)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False


class TestCompanyListView:
    def test_fetch_company_list_success_return_200(self, api_client, mock_company_service):
        mock_company_service.get_company_list.return_value = [{'company': 'data'}]

        response = api_client.get(LIST_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_fetch_company_list_exception_returns_failure_return_500(self, api_client, mock_company_service):
        mock_company_service.get_company_list.side_effect = Exception('Error')

        response = api_client.get(LIST_ENDPOINT)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
