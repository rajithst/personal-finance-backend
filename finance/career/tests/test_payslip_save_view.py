import pytest
import json
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from finance.career.models import CompanyProfile, Employment, CareerDocument, MonthlyPayslip

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_save_endpoint_creates_records_and_uploads_to_gcs(api_client, mocker):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='testuser', email='test@test.com', password='password')
    api_client.force_authenticate(user=user)
    
    # Create dependencies
    company = CompanyProfile.objects.create(name='Test Company', user=user)
    employment = Employment.objects.create(
        user=user,
        company=company,
        job_title='Engineer',
        start_date='2020-01-01'
    )
    
    mock_upload = mocker.patch('finance.career.views.upload_payslip_document')
    mock_upload.return_value = 'gs://payslip-bucket/career_docs/2023/10/payslip.pdf'
    
    url = '/finance/career/payslips/save/'
    pdf_content = b"pdf_content"
    file = SimpleUploadedFile("payslip.pdf", pdf_content, content_type="application/pdf")
    
    payslip_data = {
        'employment': employment.id,
        'year': 2023,
        'month': 10,
        'base_salary': '1000.00',
        'gross_pay': '1000.00',
        'total_tax': '200.00',
        'social_insurance_total': '0.00',
        'total_deductions': '200.00',
        'net_pay': '800.00'
    }
    
    response = api_client.post(url, {
        'file': file,
        'data': json.dumps(payslip_data)
    })
    
    assert response.status_code == 201
    
    # Assert Document was created
    assert CareerDocument.objects.count() == 1
    doc = CareerDocument.objects.first()
    assert doc.document_type == 'payslip_pdf'
    assert doc.employment == employment
    assert doc.file.name == 'gs://payslip-bucket/career_docs/2023/10/payslip.pdf'
    
    # Assert Payslip was created
    assert MonthlyPayslip.objects.count() == 1
    payslip = MonthlyPayslip.objects.first()
    assert payslip.employment == employment
    assert payslip.year == 2023
    assert payslip.month == 10
    assert float(payslip.gross_pay) == 1000.0
    assert float(payslip.net_pay) == 800.0
    assert payslip.document == doc
    
    mock_upload.assert_called_once()
    kwargs = mock_upload.call_args.kwargs
    assert kwargs.get("user_id") == user.id
    assert kwargs.get("company_slug") == company.name
    assert kwargs.get("year") == 2023
    assert kwargs.get("month") == 10
    assert kwargs.get("metadata_dict") == {'filename': 'payslip.pdf'}

@pytest.mark.django_db
def test_save_endpoint_returns_400_if_pdf_missing(api_client):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='testuser', email='test@test.com', password='password')
    api_client.force_authenticate(user=user)
    
    company = CompanyProfile.objects.create(name='Test Company', user=user)
    employment = Employment.objects.create(
        user=user,
        company=company,
        job_title='Engineer',
        start_date='2020-01-01'
    )
    
    url = '/finance/career/payslips/save/'
    payslip_data = {
        'employment': employment.id,
        'year': 2023,
        'month': 10
    }
    
    response = api_client.post(url, {
        'data': json.dumps(payslip_data)
    })
    
    assert response.status_code == 400
    assert response.json() == {"error": "Missing file or data."}
