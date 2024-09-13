import random
from datetime import datetime, timedelta

import pytest
from rest_framework import status
from model_bakery import baker

from oauth.models import User
from transactions.models import Transaction, TransactionCategory, TransactionSubCategory, Account


@pytest.fixture
def get_transactions(api_client):
    def do_get_transactions(query_params):
        url = '/finance/transaction/'
        url += '?year=' + str(query_params['year'])
        url += '&target=' + str(query_params['target'])
        url += '&cat=' + str(query_params['cat'])
        url += '&subcat=' + str(query_params['subcat'])
        return api_client.get(url)

    return do_get_transactions


@pytest.mark.django_db
class TestTransactions:

    def get_random_date(self):
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        delta = end_date - start_date
        random_days = random.randint(0, delta.days)
        random_date = start_date + timedelta(days=random_days)
        return random_date.date().strftime('%Y-%m-%d')

    def get_mock_user(self):
        return baker.make(User)

    def test_if_returns_transactions(self, get_transactions, authenticated_user):
        # Arrange
        mock_user = self.get_mock_user()
        authenticated_user(mock_user)
        baker.make(Transaction, date=self.get_random_date, user=mock_user, is_expense=1, _quantity=10)

        # Act
        queryparams = {
            'year': 2024,
            'target': 'expense',
            'cat': '',
            'subcat': ''
        }

        # Compare
        response = get_transactions(queryparams)
        assert response.status_code == status.HTTP_200_OK
        assert 'payload' in response.data
        payload = response.data['payload']
        assert payload[0]['total'] > 0
        payload_transactions = payload[0]['transactions']
        assert len(payload_transactions) > 0
        assert payload_transactions[0]['year'] == 2024
        assert payload_transactions[0]['is_expense'] == 1

    def test_if_save_transactions(self, api_client, authenticated_user):
        mock_user = self.get_mock_user()
        authenticated_user(mock_user)
        account = baker.make(Account)
        category = baker.make(TransactionCategory, user=mock_user)
        subcategory = baker.make(TransactionSubCategory, category=category, user=mock_user)

        payload = {
            'date': self.get_random_date(),
            'amount': 200.00,
            'account_id': account.id,
            'category_id': category.id,
            'subcategory_id': subcategory.id,
            'user_id': mock_user.id,
            'update_similar': True
        }
        response = api_client.post('/finance/transaction/', data=payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
