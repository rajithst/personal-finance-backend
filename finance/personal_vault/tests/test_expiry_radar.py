from datetime import date, timedelta
import pytest
from django.contrib.auth import get_user_model
from finance.personal_vault.models import PersonalDocument, VehicleRecord, ResidenceRecord
from finance.personal_vault.services.expiry_service import get_user_expiry_radar

User = get_user_model()

@pytest.mark.django_db
def test_expiry_radar_classification():
    user = User.objects.create_user(username="test_radar_user", password="password")
    today = date(2026, 10, 16)
    
    # Critical: 10 days left
    PersonalDocument.objects.create(
        user=user, title="Passport", category="identity", doc_type="passport",
        expiry_date=today + timedelta(days=10), file_uri="local://test.pdf"
    )
    # Expired: 5 days ago
    VehicleRecord.objects.create(
        user=user, make="Toyota", model="Aqua", license_plate="12-34",
        status="active", shaken_expiry_date=today - timedelta(days=5)
    )
    # Upcoming: 45 days left
    ResidenceRecord.objects.create(
        user=user, property_name="Apt 101", address_full="Tokyo",
        status="current", move_in_date=today - timedelta(days=300),
        lease_end_date=today + timedelta(days=45)
    )
    # Healthy: 120 days left
    VehicleRecord.objects.create(
        user=user, make="Honda", model="Vezel", license_plate="56-78",
        status="active", insurance_expiry_date=today + timedelta(days=120)
    )

    radar = get_user_expiry_radar(user, reference_date=today)
    assert len(radar) == 4
    
    # Ordered chronologically by due date (expired first)
    assert radar[0]["severity"] == "expired"
    assert radar[0]["days_remaining"] == -5
    assert radar[0]["domain"] == "vehicle"

    assert radar[1]["severity"] == "critical"
    assert radar[1]["days_remaining"] == 10
    assert radar[1]["domain"] == "identity"

    assert radar[2]["severity"] == "upcoming"
    assert radar[2]["days_remaining"] == 45
    assert radar[2]["domain"] == "residence"

    assert radar[3]["severity"] == "healthy"
    assert radar[3]["days_remaining"] == 120
