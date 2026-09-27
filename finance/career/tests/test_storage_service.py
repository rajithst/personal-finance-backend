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

