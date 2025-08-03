import pytest
from rest_framework import status

CATEGORY_ENDPOINT = "/finance/category/settings/"
CATEGORY_DELETE_ENDPOINT = "/finance/category/settings/{id}/"


@pytest.fixture
def mock_category_service(mocker):
    mock_service = mocker.Mock()
    mocker.patch("finance.categories.views.CategoryService", return_value=mock_service)
    return mock_service


@pytest.mark.django_db
class TestCategorySettingsView:
    def test_put_success_updates_category_and_subcategories_return_200(self, api_client, mock_category_service, authenticate):
        authenticate()
        mock_category_service.update_category.return_value = (True, {'id': 1, 'name': 'Updated Category'})
        mock_category_service.update_subcategories.return_value = (True, {'id': 1, 'name': 'Sub1'})
        mock_category_service.get_all_subcategories.return_value = [{'id': 10, 'name': 'Sub1'}]

        payload = {
            "category": {"id": 1, "name": "Updated Category"},
            "subcategories": [{"id": 10, "name": "Sub1"}],
            "deleted_sub_categories": []
        }

        response = api_client.put(CATEGORY_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True

    def test_put_failure_returns_400(self, api_client, mock_category_service, authenticate):
        authenticate()
        mock_category_service.update_category.return_value = (False, None)

        payload = {"category": {"id": 1, "name": "Bad Category"}}
        response = api_client.put(CATEGORY_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

    def test_put_exception_returns_500(self, api_client, mock_category_service, authenticate):
        authenticate()
        mock_category_service.update_category.side_effect = Exception("Unexpected error")

        payload = {"category": {"id": 1, "name": "Bad Category"}}
        response = api_client.put(CATEGORY_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
        assert "Unexpected error" in response.data['message']

    def test_delete_success_returns_200(self, api_client, mock_category_service, authenticate):
        authenticate()
        mock_category_service.delete_category.return_value = True

        response = api_client.delete(CATEGORY_DELETE_ENDPOINT.format(id=1))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        mock_category_service.delete_category.assert_called_once_with(1)

    def test_delete_failure_returns_400(self, api_client, mock_category_service, authenticate):
        authenticate()
        mock_category_service.delete_category.return_value = False

        response = api_client.delete(CATEGORY_DELETE_ENDPOINT.format(id=1))

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

    def test_delete_exception_returns_500(self, api_client, mock_category_service, authenticate):
        authenticate()
        mock_category_service.delete_category.side_effect = Exception("Unexpected error")

        response = api_client.delete(CATEGORY_DELETE_ENDPOINT.format(id=1))

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
        assert "Unexpected error" in response.data['message']

    def test_post_success_creates_category_and_subcategories(self, api_client, mock_category_service, authenticate):
        authenticate()
        mock_category_service.create_category.return_value = (
            {"id": 1, "name": "New Category"},
            [{"id": 10, "name": "Sub1"}]
        )

        payload = {"name": "New Category", "subcategories": [{"name": "Sub1"}]}
        response = api_client.post(CATEGORY_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] is True
        assert response.data['data']['category']['name'] == "New Category"

    def test_post_failure_returns_400(self, api_client, mock_category_service, authenticate):
        authenticate()
        mock_category_service.create_category.return_value = (None, None)

        payload = {"name": "Bad Category"}
        response = api_client.post(CATEGORY_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['status'] is False

    def test_post_exception_returns_500(self, api_client, mock_category_service, authenticate):
        authenticate()
        mock_category_service.create_category.side_effect = Exception("Unexpected error")

        payload = {"name": "Bad Category"}
        response = api_client.post(CATEGORY_ENDPOINT, payload, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['status'] is False
        assert "Unexpected error" in response.data['message']
