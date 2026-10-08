import io
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from finance.career.models import CompanyProfile, Employment, CareerDocument
from finance.career.services.storage_service import generate_download_signature

User = get_user_model()


@pytest.fixture
def auth_user():
    return User.objects.create_user(username='testcarrier', email='carrier@test.com', password='password123')


@pytest.fixture
def client_authenticated(auth_user):
    client = APIClient()
    client.force_authenticate(user=auth_user)
    return client


@pytest.fixture
def employment(auth_user):
    company = CompanyProfile.objects.create(name='Acme Corp', short_name='Acme', user=auth_user)
    return Employment.objects.create(user=auth_user, company=company, job_title='Manager', start_date='2022-01-01')


@pytest.mark.django_db
def test_career_document_upload_endpoint_saves_persistent_uri(client_authenticated, auth_user, employment, mocker, settings):
    settings.DEBUG = False
    mock_upload = mocker.patch(
        'finance.career.views.upload_career_document',
        return_value='gs://personal-finance-425009.appspot.com/career_vault/users/user_1/companies/Acme/documents/employment_conditions/test.pdf'
    )

    pdf_file = SimpleUploadedFile("Employment_Conditions_Acme_Corp.pdf", b"%PDF-1.4 test document content", content_type="application/pdf")

    response = client_authenticated.post(
        '/finance/career/documents/',
        {
            'employment': employment.id,
            'document_type': 'employment_contract',
            'title': 'Employment Conditions Acme',
            'file': pdf_file,
        },
        format='multipart'
    )

    assert response.status_code == 201
    mock_upload.assert_called_once()
    doc = CareerDocument.objects.get(id=response.data['data']['id'])
    assert doc.user == auth_user
    assert str(doc.file).startswith('gs://')
    assert doc.file_name_original == "Employment_Conditions_Acme_Corp.pdf"


@pytest.mark.django_db
def test_career_document_download_authenticated(client_authenticated, auth_user, employment, mocker):
    doc = CareerDocument.objects.create(
        user=auth_user,
        employment=employment,
        title="Sample Document",
        file="gs://bucket/sample.pdf",
        mime_type="application/pdf"
    )

    mock_stream = io.BytesIO(b"%PDF-1.4 stream content")
    mocker.patch(
        'finance.career.views.open_document_stream',
        return_value=(mock_stream, 'application/pdf', 'sample.pdf', 24)
    )

    response = client_authenticated.get(f'/finance/career/documents/{doc.id}/download/')
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert b"%PDF-1.4 stream content" in b"".join(response.streaming_content)


@pytest.mark.django_db
def test_career_document_download_with_signature_unauthenticated(auth_user, employment, mocker):
    client = APIClient()  # Unauthenticated
    doc = CareerDocument.objects.create(
        user=auth_user,
        employment=employment,
        title="Sample Document",
        file="gs://bucket/sample.pdf",
        mime_type="application/pdf"
    )

    sig = generate_download_signature(doc.id, auth_user.id)
    mock_stream = io.BytesIO(b"%PDF-1.4 signed stream content")
    mocker.patch(
        'finance.career.views.open_document_stream',
        return_value=(mock_stream, 'application/pdf', 'sample.pdf', 31)
    )

    response = client.get(f'/finance/career/documents/{doc.id}/download/?sig={sig}')
    assert response.status_code == 200
    assert b"%PDF-1.4 signed stream content" in b"".join(response.streaming_content)


@pytest.mark.django_db
def test_career_document_download_forbidden_without_auth_or_sig(auth_user, employment):
    client = APIClient()  # Unauthenticated
    doc = CareerDocument.objects.create(
        user=auth_user,
        employment=employment,
        title="Private Document",
        file="gs://bucket/private.pdf"
    )

    # No signature and no auth
    response = client.get(f'/finance/career/documents/{doc.id}/download/')
    assert response.status_code == 403

    # Invalid signature
    response = client.get(f'/finance/career/documents/{doc.id}/download/?sig=invalid-signature')
    assert response.status_code == 403


@pytest.mark.django_db
def test_media_career_docs_fallback_view_handles_missing_document(auth_user):
    client = APIClient()
    response = client.get('/media/career_docs/2026/10/NonExistent.pdf')
    assert response.status_code == 404
    assert response.json()['status'] is False
    assert 'not found on storage' in response.json()['message'].lower()
