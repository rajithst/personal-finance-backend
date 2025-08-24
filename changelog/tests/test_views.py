import pytest
from django.contrib.contenttypes.models import ContentType
from rest_framework import status

from changelog.models import ChangeLog, SectionEnum, ActionEnum
from finance.transactions.models import Transaction
from oauth.models import User

ENDPOINT = "/logs/activity/"


@pytest.mark.django_db
class TestActivityView:

    def test_activity_view_returns_logs_for_user(self, authenticate, api_client):
        current_user = User.objects.create(username='user', password='pass@123', email='t@google.com')
        other_user = User.objects.create(username='other', password='pass@123', email='f@google.com')
        authenticate(user=current_user)
        content_type = ContentType.objects.get_for_model(Transaction)
        ChangeLog.objects.create(
            user=current_user,
            content_type=content_type,
            object_id="1",
            section=SectionEnum.TRANSACTION,
            action=ActionEnum.CREATE,
            changelog={"field": "value"}
        )
        ChangeLog.objects.create(
            user=other_user,
            content_type=content_type,
            object_id="2",
            section=SectionEnum.TRANSACTION,
            action=ActionEnum.CREATE,
            changelog={"other": "value"}
        )

        response = api_client.get(ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] is True
        assert len(response.data['data']) == 1
        log_data = response.data['data'][0]
        assert log_data['id'] == 1
        assert log_data['section'] == SectionEnum.TRANSACTION
        assert log_data['action'] == ActionEnum.CREATE
        assert log_data['changelog'] == {"field": "value"}

    def test_activity_view_unauthenticated(self, api_client):
        response = api_client.get(ENDPOINT)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['detail'] == 'Authentication credentials were not provided.'