import pytest
from model_bakery import baker
from rest_framework.test import APIClient

from oauth.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticate(api_client):
    def do_authenticated_user(user=None):
        return api_client.force_authenticate(user=user if user else baker.make(User))

    return do_authenticated_user
