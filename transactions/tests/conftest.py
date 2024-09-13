import pytest
from rest_framework.test import APIClient

from oauth.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_user(api_client):
    def do_authenticated_user(mock_user):
        return api_client.force_authenticate(user=mock_user)

    return do_authenticated_user
