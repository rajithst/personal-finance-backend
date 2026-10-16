import pytest
from datetime import date
from django.contrib.auth import get_user_model
from finance.personal_vault.models import (
    PersonalDocument,
    IdentityProfile,
    EducationRecord,
    VehicleRecord,
    ResidenceRecord,
)

User = get_user_model()

@pytest.mark.django_db
def test_create_identity_profile_and_documents():
    user = User.objects.create_user(username="vault_user", password="password123")
    profile = IdentityProfile.objects.create(
        user=user,
        full_legal_name="Jane Doe",
        nationality="Japanese",
        date_of_birth=date(1990, 5, 15)
    )
    assert profile.full_legal_name == "Jane Doe"
    assert "Jane Doe" in str(profile)

    doc = PersonalDocument.objects.create(
        user=user,
        title="Passport",
        category="identity",
        doc_type="passport",
        document_number="MZ123456",
        file_uri="local://personal_vault/users/user_1/passport.pdf",
        original_filename="passport.pdf"
    )
    assert doc.category == "identity"
    assert doc.user == user
    assert "Passport" in str(doc)

@pytest.mark.django_db
def test_education_vehicle_residence_records():
    user = User.objects.create_user(username="vault_user2", password="password123")
    
    edu = EducationRecord.objects.create(
        user=user,
        institution_name="Tokyo University",
        qualification_type="bachelor",
        field_of_study="Computer Science",
        start_date=date(2012, 4, 1),
        end_date=date(2016, 3, 25)
    )
    assert "Tokyo University" in str(edu)

    veh = VehicleRecord.objects.create(
        user=user,
        make="Toyota",
        model="Prius",
        license_plate="品川 300 あ 12-34",
        status="active",
        shaken_expiry_date=date(2027, 4, 1)
    )
    assert "Toyota Prius" in str(veh)

    res = ResidenceRecord.objects.create(
        user=user,
        property_name="Park Tower",
        address_full="Tokyo Minato-ku",
        status="current",
        move_in_date=date(2020, 1, 1),
        lease_end_date=date(2026, 12, 31)
    )
    assert "Park Tower" in str(res)
