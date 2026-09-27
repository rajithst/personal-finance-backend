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

@pytest.mark.django_db
def test_save_endpoint_returns_400_for_non_pdf(api_client):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='testnonpdf', email='nonpdf@test.com', password='password')
    api_client.force_authenticate(user=user)

    url = '/finance/career/payslips/save/'
    file = SimpleUploadedFile("test.txt", b"file_content", content_type="text/plain")
    payslip_data = {'employment': 1, 'year': 2024, 'month': 5}

    response = api_client.post(url, {
        'file': file,
        'data': json.dumps(payslip_data)
    })

    assert response.status_code == 400
    assert response.json() == {"error": "Invalid file type. Only PDF is supported."}

@pytest.mark.django_db
def test_save_endpoint_validates_year_and_month(api_client):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='testyearmonth', email='ym@test.com', password='password')
    api_client.force_authenticate(user=user)

    company = CompanyProfile.objects.create(name='YM Co', user=user)
    employment = Employment.objects.create(user=user, company=company, job_title='Eng', start_date='2020-01-01')

    url = '/finance/career/payslips/save/'
    file = SimpleUploadedFile("payslip.pdf", b"pdf_content", content_type="application/pdf")

    # Invalid year
    response = api_client.post(url, {
        'file': file,
        'data': json.dumps({'employment': employment.id, 'year': 0, 'month': 5})
    })
    assert response.status_code == 400
    assert "Valid year" in response.json().get("error", "")

    # Invalid month (e.g. 13)
    response = api_client.post(url, {
        'file': file,
        'data': json.dumps({'employment': employment.id, 'year': 2024, 'month': 13})
    })
    assert response.status_code == 400
    assert "Valid year" in response.json().get("error", "")

@pytest.mark.django_db
def test_save_endpoint_handles_none_values_gracefully(api_client, mocker):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='testuser2', email='test2@test.com', password='password')
    api_client.force_authenticate(user=user)
    
    company = CompanyProfile.objects.create(name='Null Value Co', user=user)
    employment = Employment.objects.create(
        user=user,
        company=company,
        job_title='Engineer',
        start_date='2020-01-01'
    )
    
    mocker.patch('finance.career.views.upload_payslip_document', return_value='gs://bucket/test.pdf')
    
    url = '/finance/career/payslips/save/'
    file = SimpleUploadedFile("payslip.pdf", b"pdf_content", content_type="application/pdf")
    
    # Payload with None / null values exactly like frontend sends
    payslip_data = {
        'employment': employment.id,
        'year': 2024,
        'month': 5,
        'base_salary': 350000.0,
        'housing_allowance': None,
        'discretionary_allowance': None,
        'remote_work_allowance': None,
        'late_night_overtime_pay': None,
        'holiday_work_pay': None,
        'special_allowance': None,
        'other_allowances': 0.0,
        'gross_pay': 350000.0,
        'taxable_amount': None,
        'year_end_tax_adjustment': None,
        'union_fee': None,
        'mutual_aid_fee': None,
        'meal_deduction': None,
        'other_deductions': 0.0,
        'total_tax': 25000.0,
        'social_insurance_total': 50000.0,
        'total_deductions': 75000.0,
        'net_pay': 275000.0,
        'bank_transfer_amount': None,
        'working_days': None,
        'total_work_hours': None,
        'overtime_hours': None,
        'late_night_hours': None,
        'holiday_work_hours': None,
        'absent_days': None,
        'loss_of_pay_days': None,
        'paid_leave_days_used': None,
        'remaining_paid_leave_days': None,
        'std_remuneration_health': None,
        'std_remuneration_pension': None,
        'ytd_gross_pay': None,
        'ytd_social_insurance': None,
        'ytd_income_tax': None,
    }
    
    response = api_client.post(url, {
        'file': file,
        'data': json.dumps(payslip_data)
    })
    
    assert response.status_code == 201
    payslip = MonthlyPayslip.objects.get(year=2024, month=5)
    assert float(payslip.base_salary) == 350000.0
    assert float(payslip.housing_allowance) == 0.0
    assert float(payslip.discretionary_allowance) == 0.0
    assert payslip.taxable_amount is None
    assert payslip.working_days is None


@pytest.mark.django_db
def test_save_endpoint_saves_other_descriptions_and_notes(api_client, mocker):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='testuser3', email='test3@test.com', password='password')
    api_client.force_authenticate(user=user)

    company = CompanyProfile.objects.create(name='Desc Co', user=user)
    employment = Employment.objects.create(
        user=user,
        company=company,
        job_title='Engineer',
        start_date='2020-01-01'
    )

    mocker.patch('finance.career.views.upload_payslip_document', return_value='gs://bucket/test_desc.pdf')

    url = '/finance/career/payslips/save/'
    file = SimpleUploadedFile("payslip.pdf", b"pdf_content", content_type="application/pdf")

    payslip_data = {
        'employment': employment.id,
        'year': 2025,
        'month': 11,
        'base_salary': 400000.0,
        'other_allowances': 20000.0,
        'other_allowances_description': 'Role Allowance (役職手当)',
        'gross_pay': 420000.0,
        'other_deductions': 8000.0,
        'other_deductions_description': 'Other',
        'total_deductions': 8000.0,
        'net_pay': 412000.0,
        'notes': 'Overtime adjusted by manager',
    }

    response = api_client.post(url, {
        'file': file,
        'data': json.dumps(payslip_data)
    })

    assert response.status_code == 201
    payslip = MonthlyPayslip.objects.get(year=2025, month=11)
    assert payslip.other_allowances_description == 'Role Allowance (役職手当)'
    assert payslip.other_deductions_description == 'Other'
    assert payslip.notes == 'Overtime adjusted by manager'


@pytest.mark.django_db
def test_save_endpoint_handles_slash_date_formats(api_client, mocker):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='testdateuser', email='date@test.com', password='password')
    api_client.force_authenticate(user=user)

    company = CompanyProfile.objects.create(name='Date Test Co', user=user)
    employment = Employment.objects.create(
        user=user,
        company=company,
        job_title='Engineer',
        start_date='2020-01-01'
    )

    mocker.patch('finance.career.views.upload_payslip_document', return_value='gs://bucket/test_date.pdf')

    url = '/finance/career/payslips/save/'
    file = SimpleUploadedFile("payslip.pdf", b"pdf_content", content_type="application/pdf")

    payslip_data = {
        'employment': employment.id,
        'year': 2025,
        'month': 7,
        'gross_pay': 500000.0,
        'net_pay': 400000.0,
        'payment_date': '01/07/2025',
        'pay_period_start': '2025/06/01',
        'pay_period_end': '30/06/2025',
    }

    response = api_client.post(url, {
        'file': file,
        'data': json.dumps(payslip_data)
    })

    assert response.status_code == 201
    payslip = MonthlyPayslip.objects.get(year=2025, month=7)
    assert str(payslip.payment_date) == '2025-07-01'
    assert str(payslip.pay_period_start) == '2025-06-01'
    assert str(payslip.pay_period_end) == '2025-06-30'

    doc = CareerDocument.objects.get(employment=employment, document_type='payslip_pdf')
    assert str(doc.issue_date) == '2025-07-01'


