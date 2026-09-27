import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_extract_endpoint_returns_400_for_non_pdf(api_client):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='testuser', email='test@test.com', password='password')
    api_client.force_authenticate(user=user)
    
    url = '/finance/career/payslips/extract/'
    file = SimpleUploadedFile("test.txt", b"file_content", content_type="text/plain")
    response = api_client.post(url, {'file': file})
    
    assert response.status_code == 400
    assert response.json() == {"error": "Invalid file type. Only PDF is supported."}

@pytest.mark.django_db
def test_extract_endpoint_calls_service_and_returns_json(api_client, mocker):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='testuser2', email='test2@test.com', password='password')
    api_client.force_authenticate(user=user)
    
    mock_extract = mocker.patch('finance.career.views.extract_payslip_data')
    mock_extract.return_value = {
        'base_salary': 100,
        'gross_pay': 100,
        'net_pay': 80
    }
    
    url = '/finance/career/payslips/extract/'
    file = SimpleUploadedFile("payslip.pdf", b"pdf_content", content_type="application/pdf")
    
    response = api_client.post(url, {'file': file})
    
    assert response.status_code == 200
    assert response.json() == mock_extract.return_value
    mock_extract.assert_called_once_with(b"pdf_content")
