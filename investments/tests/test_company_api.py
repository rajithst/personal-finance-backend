import pytest
from rest_framework import status


@pytest.fixture
def mock_company_service(mocker):
    return mocker.patch('investments.apis.company_api.CompanyService')


@pytest.mark.django_db
class TestCompanyValueUpdaterView:
    def test_get_success(self, api_client, mock_company_service):
        mock_company_service.return_value.fetch_company_info.return_value = (True, {'info': 'company data'})

        response = api_client.get('/investments/company/detail/fetch/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_failure(self, api_client, mock_company_service):
        mock_company_service.return_value.fetch_company_info.return_value = (False, 'error')
        response = api_client.get('/investments/company/detail/fetch/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

    def test_get_exception(self, api_client, mock_company_service):
        mock_company_service.return_value.fetch_company_info.side_effect = Exception('Error')
        response = api_client.get('/investments/company/detail/fetch/')
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False


class TestCompanyListView:
    def test_get_success(self, api_client, mock_company_service):
        mock_company_service.return_value.get_company_list.return_value = [{'company': 'data'}]

        response = api_client.get('/investments/company/list/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_get_exception(self, api_client, mock_company_service):
        mock_company_service.return_value.get_company_list.side_effect = Exception('Error')

        response = api_client.get('/investments/company/list/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is False
