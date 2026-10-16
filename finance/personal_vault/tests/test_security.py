import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from finance.personal_vault.models import PersonalDocument, VehicleRecord, ResidenceRecord

User = get_user_model()

@pytest.mark.django_db
def test_cross_user_document_isolation():
    user1 = User.objects.create_user(username="alice", email="alice@example.com", password="password")
    user2 = User.objects.create_user(username="bob", email="bob@example.com", password="password")
    doc = PersonalDocument.objects.create(
        user=user1, title="Alice Passport", category="identity",
        doc_type="passport", file_uri="local://test.pdf"
    )

    client = APIClient()
    client.force_authenticate(user=user2)
    response = client.get(f"/api/v1/personal-vault/documents/{doc.id}/")
    assert response.status_code == 404

    # Bob should not be able to delete Alice's doc
    del_resp = client.delete(f"/api/v1/personal-vault/documents/{doc.id}/")
    assert del_resp.status_code == 404

    # Alice's doc remains untouched
    assert PersonalDocument.objects.filter(id=doc.id).exists()

@pytest.mark.django_db
def test_unauthenticated_requests_rejected():
    client = APIClient()
    resp = client.get("/api/v1/personal-vault/overview/")
    assert resp.status_code in (401, 403)
