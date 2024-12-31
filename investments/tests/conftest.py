import pytest
from rest_framework.test import APIClient
from model_bakery import baker

from oauth.models import User

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticate(api_client):
    def do_authenticated_user():
        return api_client.force_authenticate(user=baker.make(User))

    return do_authenticated_user










