import pytest
from unittest.mock import MagicMock
from django.core.exceptions import PermissionDenied
import datetime

def test_upload_payslip_document_constructs_correct_path(mocker):
    from finance.career.services.storage_service import upload_payslip_document
    
    mock_client = mocker.patch('finance.career.services.storage_service.storage.Client')
    mock_bucket = MagicMock()
    mock_client.return_value.bucket.return_value = mock_bucket
    mock_blob = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    
    file_obj = MagicMock()
    metadata = {'extracted_by': 'gemini'}
    
    uri = upload_payslip_document(file_obj, 1, 'acme-corp', 2023, 10, metadata)
    
    expected_path = "career_vault/users/user_1/companies/acme-corp/payslips/2023/2023-10_acme-corp_payslip.pdf"
    
    mock_bucket.blob.assert_called_once_with(expected_path)
    assert mock_blob.metadata == metadata
    file_obj.seek.assert_called_once_with(0)
    mock_blob.upload_from_file.assert_called_once_with(file_obj, content_type='application/pdf')
    
    # Assert URI starts with gs://
    assert expected_path in uri
    assert uri.startswith("gs://")

def test_generate_signed_url_enforces_user_ownership(mocker):
    from finance.career.services.storage_service import generate_signed_url
    
    mock_client = mocker.patch('finance.career.services.storage_service.storage.Client')
    mock_blob = MagicMock()
    mock_blob.generate_signed_url.return_value = "https://signed.url"
    mock_client.return_value.bucket.return_value.blob.return_value = mock_blob
    
    # Matching user
    class User:
        id = 1
        
    url = generate_signed_url("gs://bucket/path", 1, User())
    assert url == "https://signed.url"
    
    # Mismatch user
    class OtherUser:
        id = 2
        
    with pytest.raises(PermissionDenied):
        generate_signed_url("gs://bucket/path", 1, OtherUser())

def test_generate_signed_url_handles_local_scheme():
    from finance.career.services.storage_service import generate_signed_url

    class User:
        id = 1

    url = generate_signed_url("local://career_vault/test.pdf", 1, User())
    assert url == "/media/career_vault/test.pdf"

@pytest.mark.django_db
def test_career_document_and_payslip_file_url_resolution(mocker, settings):
    from django.contrib.auth import get_user_model
    from finance.career.models import CompanyProfile, Employment, CareerDocument, MonthlyPayslip
    from finance.career.serializers import MonthlyPayslipSerializer
    from finance.career.services.storage_service import verify_download_signature

    User = get_user_model()
    user = User.objects.create_user(username='docuser', email='doc@test.com', password='password')
    company = CompanyProfile.objects.create(name='Doc Co', user=user)
    employment = Employment.objects.create(user=user, company=company, job_title='Eng', start_date='2020-01-01')

    doc = CareerDocument.objects.create(
        user=user,
        employment=employment,
        title="2026-05 Payslip",
        file="local://career_vault/users/user_1/companies/DocCo/payslips/2026/2026-05_payslip.pdf"
    )

    # In production (DEBUG=False): file_url returns backend streaming URL with secure signature
    settings.DEBUG = False
    assert doc.file_url.startswith(f"/finance/career/documents/{doc.pk}/download/?sig=")
    sig = doc.file_url.split('?sig=')[1]
    assert verify_download_signature(sig, doc.pk, user.id) is True

    # In local development (DEBUG=True): file_url returns /media/... path
    settings.DEBUG = True
    assert doc.file_url == "/media/career_vault/users/user_1/companies/DocCo/payslips/2026/2026-05_payslip.pdf"

    payslip = MonthlyPayslip.objects.create(
        user=user,
        employment=employment,
        document=doc,
        year=2026,
        month=5,
        gross_pay=1000,
        net_pay=800
    )
    serializer = MonthlyPayslipSerializer(payslip)
    assert serializer.data['document_file_url'] == "/media/career_vault/users/user_1/companies/DocCo/payslips/2026/2026-05_payslip.pdf"


def test_upload_career_document_constructs_correct_path_in_prod(mocker, settings):
    from finance.career.services.storage_service import upload_career_document
    settings.DEBUG = False

    mock_client = mocker.patch('finance.career.services.storage_service.storage.Client')
    mock_bucket = MagicMock()
    mock_client.return_value.bucket.return_value = mock_bucket
    mock_blob = MagicMock()
    mock_bucket.blob.return_value = mock_blob

    file_obj = MagicMock()
    file_obj.name = "Employment_Conditions_Acme_Corp.pdf"
    file_obj.content_type = "application/pdf"

    uri = upload_career_document(
        file_obj=file_obj,
        user_id=1,
        company_slug="acme-corp",
        doc_type="employment_conditions",
        original_filename=file_obj.name,
        metadata_dict={"tag": "contract"}
    )

    assert uri.startswith("gs://")
    assert "career_vault/users/user_1/companies/acme-corp/documents/employment_conditions/" in uri
    assert "Employment_Conditions_Acme_Corp.pdf" in uri
    mock_blob.upload_from_file.assert_called_once_with(file_obj, content_type="application/pdf")


def test_upload_career_document_saves_locally_in_dev(tmp_path, settings):
    import io
    from finance.career.services.storage_service import upload_career_document
    settings.DEBUG = True
    settings.MEDIA_ROOT = str(tmp_path)

    file_obj = io.BytesIO(b"PDF-content-sample")
    file_obj.name = "Contract.pdf"

    uri = upload_career_document(
        file_obj=file_obj,
        user_id=42,
        company_slug="google",
        doc_type="offer_letter",
        original_filename=file_obj.name
    )

    assert uri.startswith("local://career_vault/users/user_42/companies/google/documents/offer_letter/")
    local_path = tmp_path / uri.replace("local://", "")
    assert local_path.exists()
    assert local_path.read_bytes() == b"PDF-content-sample"


def test_download_signature_verification_and_expiry():
    from finance.career.services.storage_service import generate_download_signature, verify_download_signature

    sig = generate_download_signature(doc_id=10, user_id=20)
    assert verify_download_signature(sig, doc_id=10, user_id=20) is True
    # Wrong doc_id
    assert verify_download_signature(sig, doc_id=99, user_id=20) is False
    # Wrong user_id
    assert verify_download_signature(sig, doc_id=10, user_id=99) is False
    # Tampered signature
    assert verify_download_signature(sig + "bad", doc_id=10, user_id=20) is False


