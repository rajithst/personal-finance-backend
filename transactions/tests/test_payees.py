import pytest
from rest_framework import status
from model_bakery import baker

from oauth.models import User
from transactions.models import Transaction, TransactionCategory, TransactionSubCategory, Account, DestinationMap


@pytest.mark.django_db
class TestPayees:

    def get_mock_user(self):
        return baker.make(User)

    def test_if_returns_payees(self, api_client, authenticated_user):
        # Arrange
        mock_user = self.get_mock_user()
        authenticated_user(mock_user)
        baker.make(DestinationMap, _quantity=10)

        # Compare
        response = api_client.get('/finance/payee/')
        assert response.status_code == status.HTTP_200_OK
        assert 'payees' in response.data
        payload = response.data['payees']
        assert len(payload) == 10

    def test_if_returns_payee_by_id(self, api_client, authenticated_user):
        mock_user = self.get_mock_user()
        authenticated_user(mock_user)
        destination = baker.make(DestinationMap, destination='test_destination',
                                 destination_original='test_destination_original')
        response = api_client.get(f'/finance/payee/{destination.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert 'payee' in response.data
        payload = response.data['payee']
        assert payload['id'] == destination.id

    def test_if_returns_payee_details_by_id(self, api_client, authenticated_user):
        mock_user = self.get_mock_user()
        authenticated_user(mock_user)
        destination = baker.make(DestinationMap, user=mock_user, destination='test_destination',
                                 destination_original='test_destination_original')
        transaction = baker.make(Transaction, user=mock_user, destination='test_destination',
                                 destination_original='test_destination_original', _quantity=10)
        response = api_client.get(f'/finance/payee-detail/{destination.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert 'payee' in response.data and 'transactions' in response.data
        payee_data = response.data['payee']
        transaction_data = response.data['transactions']
        assert payee_data['destination'] == 'test_destination'
        assert len(transaction_data) == 10
