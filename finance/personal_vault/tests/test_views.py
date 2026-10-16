import pytest
from datetime import date
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from finance.personal_vault.models import (
    PersonalDocument,
    IdentityProfile,
    EducationRecord,
    VehicleRecord,
    ResidenceRecord,
)

User = get_user_model()

@pytest.mark.django_db
def test_personal_vault_overview_endpoint():
    user = User.objects.create_user(username="viewer_user", email="viewer@example.com", password="password")
    client = APIClient()
    client.force_authenticate(user=user)

    # Create dummy records
    VehicleRecord.objects.create(
        user=user, make="Honda", model="Fit", license_plate="11-22",
        status="active", shaken_expiry_date=date(2027, 1, 1)
    )
    ResidenceRecord.objects.create(
        user=user, property_name="Shibuya Apt", address_full="Tokyo",
        status="current", move_in_date=date(2023, 1, 1), lease_end_date=date(2026, 12, 1)
    )

    resp = client.get("/api/v1/personal-vault/overview/")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["metrics"]["active_vehicles"] == 1
    assert data["metrics"]["active_leases"] == 1
    assert "expiry_radar" in data

@pytest.mark.django_db
def test_identity_profile_get_and_put():
    user = User.objects.create_user(username="id_user", email="id@example.com", password="password")
    client = APIClient()
    client.force_authenticate(user=user)

    # Initially empty/auto-created
    get_resp = client.get("/api/v1/personal-vault/identity/")
    assert get_resp.status_code == 200

    put_resp = client.put("/api/v1/personal-vault/identity/", {
        "full_legal_name": "Taro Yamada",
        "nationality": "Japanese",
        "date_of_birth": "1992-08-20"
    }, format="json")
    assert put_resp.status_code == 200
    assert put_resp.json()["data"]["full_legal_name"] == "Taro Yamada"

@pytest.mark.django_db
def test_vehicle_crud():
    user = User.objects.create_user(username="veh_user", email="veh@example.com", password="password")
    client = APIClient()
    client.force_authenticate(user=user)

    post_resp = client.post("/api/v1/personal-vault/vehicles/", {
        "make": "Mazda",
        "model": "CX-5",
        "license_plate": "横浜 300 さ 99-88",
        "status": "active",
        "shaken_expiry_date": "2027-06-15"
    }, format="json")
    assert post_resp.status_code == 201
    veh_id = post_resp.json()["data"]["id"]

    list_resp = client.get("/api/v1/personal-vault/vehicles/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) == 1

@pytest.mark.django_db
def test_document_upload_and_list():
    user = User.objects.create_user(username="upload_user", email="upload@example.com", password="password")
    client = APIClient()
    client.force_authenticate(user=user)

    pdf_file = SimpleUploadedFile("cert.pdf", b"%PDF-1.4 sample content", content_type="application/pdf")
    upload_resp = client.post("/api/v1/personal-vault/documents/upload/", {
        "file": pdf_file,
        "title": "Degree Certificate",
        "category": "education",
        "doc_type": "degree_cert",
    }, format="multipart")
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["data"]["id"]

    # Filter by category
    filter_resp = client.get("/api/v1/personal-vault/documents/?category=education")
    assert filter_resp.status_code == 200
    assert len(filter_resp.json()["data"]) == 1
    assert filter_resp.json()["data"][0]["id"] == doc_id
