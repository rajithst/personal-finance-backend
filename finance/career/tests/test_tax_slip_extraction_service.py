import pytest
from unittest.mock import MagicMock

def test_extract_tax_slip_data_converts_era_and_fields(mocker):
    from finance.career.services.tax_slip_extraction_service import extract_tax_slip_data, TaxSlipSchema
    
    mock_client = mocker.patch('finance.career.services.tax_slip_extraction_service.genai.Client')
    mock_response = MagicMock()
    
    mock_response.parsed = TaxSlipSchema(
        company_name="ロバート・ウォルターズ・ジャパン株式会社",
        tax_year=2023,
        issue_date="2023-12-11",
        total_payment=8014644.0,
        income_after_deduction=6113179.0,
        total_income_deductions=1619338.0,
        withholding_tax=480900.0,
        social_insurance_deduction=1139338.0,
        basic_deduction=480000.0,
        notes="年調済み",
    )
    mock_client.return_value.models.generate_content.return_value = mock_response
    
    result = extract_tax_slip_data(b"pdf_bytes")
    assert result['company_name'] == "ロバート・ウォルターズ・ジャパン株式会社"
    assert result['tax_year'] == 2023
    assert result['issue_date'] == "2023-12-11"
    assert result['total_payment'] == 8014644.0
    assert result['income_after_deduction'] == 6113179.0
    assert result['total_income_deductions'] == 1619338.0
    assert result['withholding_tax'] == 480900.0
    assert result['social_insurance_deduction'] == 1139338.0
    assert result['basic_deduction'] == 480000.0
    assert result['notes'] == "年調済み"

def test_extract_tax_slip_data_basic_deduction_default(mocker):
    from finance.career.services.tax_slip_extraction_service import extract_tax_slip_data, TaxSlipSchema
    
    mock_client = mocker.patch('finance.career.services.tax_slip_extraction_service.genai.Client')
    mock_response = MagicMock()
    
    mock_response.parsed = TaxSlipSchema(
        company_name="Test Company",
        tax_year=2024,
        total_payment=5000000.0,
        total_income_deductions=1000000.0,
        basic_deduction=0.0,  # Zero extracted, should default to 480,000
        social_insurance_deduction=520000.0,
    )
    mock_client.return_value.models.generate_content.return_value = mock_response
    
    result = extract_tax_slip_data(b"pdf_bytes")
    assert result['basic_deduction'] == 480000.0

def test_extract_tax_slip_data_model_fallback(mocker):
    from finance.career.services.tax_slip_extraction_service import extract_tax_slip_data, TaxSlipSchema
    
    mock_client = mocker.patch('finance.career.services.tax_slip_extraction_service.genai.Client')
    mock_response = MagicMock()
    mock_response.parsed = TaxSlipSchema(
        company_name="Fallback Co",
        tax_year=2023,
        total_payment=3000000.0,
        withholding_tax=100000.0,
    )
    
    # Primary model throws exception, fallback succeeds
    mock_client.return_value.models.generate_content.side_effect = [
        Exception("Gemini 2.5 Flash unavailable"),
        mock_response
    ]
    
    result = extract_tax_slip_data(b"pdf_bytes")
    assert result['company_name'] == "Fallback Co"
    assert result['tax_year'] == 2023
    assert mock_client.return_value.models.generate_content.call_count == 2
