import random
from random import randrange


import pytest
from rest_framework import status
from model_bakery import baker

from oauth.models import User
from transactions.models import Transaction, TransactionCategory, TransactionSubCategory, Account, DestinationMap


@pytest.mark.django_db
class TestCategorySettings:

    def get_mock_user(self):
        return baker.make(User)

    def test_if_returns_settings(self, api_client, authenticated_user):
        # Arrange
        mock_user = self.get_mock_user()
        authenticated_user(mock_user)
        category = baker.make(TransactionCategory)
        baker.make(TransactionSubCategory, category=category, _quantity=10)
        baker.make(Account, _quantity=5)

        # Compare
        response = api_client.get('/finance/settings/')
        assert response.status_code == status.HTTP_200_OK


