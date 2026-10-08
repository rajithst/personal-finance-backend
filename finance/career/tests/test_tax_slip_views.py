import pytest
import json
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from finance.career.models import CompanyProfile, Employment, CareerDocument, TaxWithholdingSlip

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_tax_slip_extract_rejects_non_pdf(api_client):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='taxuser1', email='tax1@test.com', password='password')
    api_client.force_authenticate(user=user)
    
    url = '/finance/career/tax-slips/extract/'
    file = SimpleUploadedFile("test.txt", b"file_content", content_type="text/plain")
    response = api_client.post(url, {'file': file})
    
    assert response.status_code == 400
    assert response.json() == {"error": "Invalid file type. Only PDF is supported."}

@pytest.mark.django_db
def test_tax_slip_extract_returns_extracted_json(api_client, mocker):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='taxuser2', email='tax2@test.com', password='password')
    api_client.force_authenticate(user=user)
    
    mock_extract = mocker.patch('finance.career.views.extract_tax_slip_data')
    mock_extract.return_value = {
        'company_name': 'Global Tech Solutions',
        'tax_year': 2023,
        'total_payment': 6000000.0,
        'income_after_deduction': 4500000.0,
        'total_income_deductions': 1280000.0,
        'withholding_tax': 300000.0,
        'social_insurance_deduction': 800000.0,
        'basic_deduction': 480000.0,
    }
    
    url = '/finance/career/tax-slips/extract/'
    file = SimpleUploadedFile("gensen.pdf", b"pdf_content", content_type="application/pdf")
    
    response = api_client.post(url, {'file': file})
    
    assert response.status_code == 200
    assert response.json() == mock_extract.return_value
    mock_extract.assert_called_once_with(b"pdf_content")

@pytest.mark.django_db
def test_tax_slip_save_creates_document_and_slip(api_client, mocker):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='taxuser3', email='tax3@test.com', password='password')
    api_client.force_authenticate(user=user)
    
    company = CompanyProfile.objects.create(name='Global Tech Solutions K.K.', user=user)
    employment = Employment.objects.create(
        user=user,
        company=company,
        job_title='Contractor',
        start_date='2022-01-01'
    )
    
    mock_upload = mocker.patch('finance.career.views.upload_career_document')
    mock_upload.return_value = 'gs://bucket/career_vault/users/user_1/companies/global_tech/documents/tax_withholding_slip/2023_gensen.pdf'
    
    url = '/finance/career/tax-slips/save/'
    pdf_content = b"pdf_bytes"
    file = SimpleUploadedFile("gensen.pdf", pdf_content, content_type="application/pdf")
    
    tax_slip_data = {
        'employment': employment.id,
        'tax_year': 2023,
        'issue_date': '2023-12-11',
        'total_payment': 6000000.0,
        'income_after_deduction': 4500000.0,
        'total_income_deductions': 1280000.0,
        'withholding_tax': 300000.0,
        'social_insurance_deduction': 800000.0,
        'basic_deduction': 480000.0,
        'notes': '年調済み',
    }
    
    response = api_client.post(url, {
        'file': file,
        'data': json.dumps(tax_slip_data)
    })
    
    assert response.status_code in [200, 201]
    
    # Assert Document was created in Career Vault
    assert CareerDocument.objects.count() == 1
    doc = CareerDocument.objects.first()
    assert doc.document_type == 'tax_withholding_slip'
    assert doc.employment == employment
    assert doc.file.name == 'gs://bucket/career_vault/users/user_1/companies/global_tech/documents/tax_withholding_slip/2023_gensen.pdf'
    
    # Assert TaxWithholdingSlip was created and linked to document
    assert TaxWithholdingSlip.objects.count() == 1
    slip = TaxWithholdingSlip.objects.first()
    assert slip.employment == employment
    assert slip.tax_year == 2023
    assert float(slip.total_payment) == 6000000.0
    assert float(slip.withholding_tax) == 300000.0
    assert slip.document == doc
    
    mock_upload.assert_called_once()

@pytest.mark.django_db
def test_tax_slip_save_updates_existing_slip(api_client, mocker):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='taxuser4', email='tax4@test.com', password='password')
    api_client.force_authenticate(user=user)
    
    company = CompanyProfile.objects.create(name='Global Tech Solutions K.K.', user=user)
    employment = Employment.objects.create(
        user=user,
        company=company,
        job_title='Contractor',
        start_date='2022-01-01'
    )
    
    # Create initial slip
    TaxWithholdingSlip.objects.create(
        user=user,
        employment=employment,
        tax_year=2023,
        total_payment=5000000.0,
        withholding_tax=250000.0,
    )
    
    mock_upload = mocker.patch('finance.career.views.upload_career_document')
    mock_upload.return_value = 'gs://bucket/new_gensen.pdf'
    
    url = '/finance/career/tax-slips/save/'
    file = SimpleUploadedFile("gensen_v2.pdf", b"pdf_v2", content_type="application/pdf")
    
    tax_slip_data = {
        'employment': employment.id,
        'tax_year': 2023,
        'total_payment': 6000000.0,
        'withholding_tax': 300000.0,
    }
    
    response = api_client.post(url, {
        'file': file,
        'data': json.dumps(tax_slip_data)
    })
    
    assert response.status_code in [200, 201]
    
    # Verify count remains 1 and values updated
    assert TaxWithholdingSlip.objects.count() == 1
    updated_slip = TaxWithholdingSlip.objects.first()
    assert float(updated_slip.total_payment) == 6000000.0
    assert float(updated_slip.withholding_tax) == 300000.0
