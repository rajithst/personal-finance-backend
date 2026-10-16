import io
import pytest
from django.core.exceptions import ValidationError
from finance.personal_vault.services.storage_service import (
    upload_personal_document,
    validate_vault_file,
    generate_vault_signature,
    verify_vault_signature,
)

def test_validate_vault_file_valid_pdf():
    file_obj = io.BytesIO(b"%PDF-1.4 test content")
    file_obj.name = "passport.pdf"
    validated = validate_vault_file(file_obj)
    assert validated["mime_type"] == "application/pdf"
    assert validated["safe_name"] == "passport.pdf"

def test_validate_vault_file_disallowed_extension():
    file_obj = io.BytesIO(b"malicious script")
    file_obj.name = "hack.sh"
    with pytest.raises(ValidationError):
        validate_vault_file(file_obj)

def test_validate_vault_file_size_limit():
    large_file = io.BytesIO(b"0" * (26 * 1024 * 1024)) # 26MB
    large_file.name = "big.pdf"
    with pytest.raises(ValidationError):
        validate_vault_file(large_file)

def test_vault_signature_lifecycle():
    token = generate_vault_signature(doc_id=123, user_id=45)
    doc_id, user_id = verify_vault_signature(token)
    assert doc_id == 123
    assert user_id == 45
