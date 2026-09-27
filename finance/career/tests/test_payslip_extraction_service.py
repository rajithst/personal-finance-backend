import pytest
from django.core.exceptions import ValidationError
from unittest.mock import MagicMock

def test_extract_payslip_data_validates_math(mocker):
    from finance.career.services.payslip_extraction_service import extract_payslip_data, PayslipSchema
    
    mock_client = mocker.patch('finance.career.services.payslip_extraction_service.genai.Client')
    mock_response = MagicMock()
    
    mock_response.parsed = PayslipSchema(
        base_salary=100,
        overtime_pay=0,
        allowances=0,
        gross_pay=200, # Math mismatch
        tax_deductions=0,
        insurance_deductions=0,
        other_deductions=0,
        net_pay=200
    )
    mock_client.return_value.models.generate_content.return_value = mock_response
    
    with pytest.raises(ValidationError, match="Gross pay validation failed"):
        extract_payslip_data(b"pdf_bytes")

def test_extract_payslip_data_success(mocker):
    from finance.career.services.payslip_extraction_service import extract_payslip_data, PayslipSchema
    
    mock_client = mocker.patch('finance.career.services.payslip_extraction_service.genai.Client')
    mock_response = MagicMock()
    
    mock_response.parsed = PayslipSchema(
        base_salary=100,
        overtime_pay=0,
        allowances=0,
        gross_pay=100,
        tax_deductions=10,
        insurance_deductions=10,
        other_deductions=0,
        net_pay=80
    )
    mock_client.return_value.models.generate_content.return_value = mock_response
    
    result = extract_payslip_data(b"pdf_bytes")
    assert result['gross_pay'] == 100
    assert result['net_pay'] == 80
