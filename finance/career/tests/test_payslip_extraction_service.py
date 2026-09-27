import pytest
from django.core.exceptions import ValidationError
from unittest.mock import MagicMock

def test_extract_payslip_data_validates_math(mocker):
    from finance.career.services.payslip_extraction_service import extract_payslip_data, PayslipSchema
    
    mock_client = mocker.patch('finance.career.services.payslip_extraction_service.genai.Client')
    mock_response = MagicMock()
    
    mock_response.parsed = PayslipSchema(
        base_salary=100.0,
        other_allowances=10.0,
        gross_pay=200.0,  # Math mismatch (200 != 110)
    )
    mock_client.return_value.models.generate_content.return_value = mock_response
    
    with pytest.raises(ValidationError, match="Gross pay validation failed"):
        extract_payslip_data(b"pdf_bytes")

def test_extract_payslip_data_fails_on_1_yen_mismatch(mocker):
    from finance.career.services.payslip_extraction_service import extract_payslip_data, PayslipSchema
    
    mock_client = mocker.patch('finance.career.services.payslip_extraction_service.genai.Client')
    mock_response = MagicMock()
    
    # Exactly 1 yen difference: calculated gross = 100, gross_pay = 101
    mock_response.parsed = PayslipSchema(
        base_salary=100.0,
        gross_pay=101.0,
    )
    mock_client.return_value.models.generate_content.return_value = mock_response
    
    with pytest.raises(ValidationError, match="Gross pay validation failed"):
        extract_payslip_data(b"pdf_bytes")

def test_extract_payslip_data_success(mocker):
    from finance.career.services.payslip_extraction_service import extract_payslip_data, PayslipSchema
    
    mock_client = mocker.patch('finance.career.services.payslip_extraction_service.genai.Client')
    mock_response = MagicMock()
    
    mock_response.parsed = PayslipSchema(
        base_salary=100.0,
        gross_pay=100.0,
        health_insurance=10.0,
        social_insurance_total=10.0,
        income_tax=10.0,
        total_tax=10.0,
        total_deductions=20.0,
        net_pay=80.0
    )
    mock_client.return_value.models.generate_content.return_value = mock_response
    
    result = extract_payslip_data(b"pdf_bytes")
    assert result['gross_pay'] == 100.0
    assert result['net_pay'] == 80.0

def test_extract_payslip_data_fallback(mocker):
    from finance.career.services.payslip_extraction_service import extract_payslip_data, PayslipSchema
    
    mock_client = mocker.patch('finance.career.services.payslip_extraction_service.genai.Client')
    mock_response = MagicMock()
    mock_response.parsed = PayslipSchema(
        base_salary=200.0,
        gross_pay=200.0,
        net_pay=200.0
    )
    mock_client.return_value.models.generate_content.side_effect = [
        Exception("503 Service Unavailable"),
        mock_response
    ]
    
    result = extract_payslip_data(b"pdf_bytes")
    assert result['gross_pay'] == 200.0
    assert mock_client.return_value.models.generate_content.call_count == 2

def test_extract_payslip_data_year_month_inference(mocker):
    from finance.career.services.payslip_extraction_service import extract_payslip_data, PayslipSchema

    mock_client = mocker.patch('finance.career.services.payslip_extraction_service.genai.Client')
    mock_response = MagicMock()
    # Schema returned without year and month, but with payment_date
    mock_response.parsed = PayslipSchema(
        year=0,
        month=0,
        payment_date="2024-05-25",
        company_name="Tech Mahindra",
        base_salary=300000.0,
        gross_pay=300000.0,
        net_pay=300000.0,
    )
    mock_client.return_value.models.generate_content.return_value = mock_response

    result = extract_payslip_data(b"pdf_bytes")
    assert result['year'] == 2024
    assert result['month'] == 5
    assert result['company_name'] == "Tech Mahindra"

def test_extract_payslip_data_handles_nontaxable_commutation(mocker):
    from finance.career.services.payslip_extraction_service import extract_payslip_data, PayslipSchema

    mock_client = mocker.patch('finance.career.services.payslip_extraction_service.genai.Client')
    mock_response = MagicMock()
    # Real-world Japanese payslip (Astellas):
    # base_salary=723700, housing=45000, discretionary=70000, remote=4250, commutation=1516
    # Taxable 支給額合計 (gross_pay in pdf) = 842950
    # Deductions = 236271
    # Taxable 差引支給額計 (net_pay in pdf) = 606679
    # Bank transfer 振込額 = 608195
    mock_response.parsed = PayslipSchema(
        base_salary=723700.0,
        housing_allowance=45000.0,
        discretionary_allowance=70000.0,
        remote_work_allowance=4250.0,
        commutation_allowance=1516.0,
        gross_pay=842950.0,  # 支給額合計（課税のみ）
        pension=59475.0,
        health_insurance=22534.0,
        employment_insurance=4222.0,
        social_insurance_total=86231.0,
        income_tax=68630.0,
        resident_tax=70300.0,
        total_tax=138930.0,
        mutual_aid_fee=1440.0,
        meal_deduction=270.0,
        union_fee=9400.0,
        total_deductions=236271.0,
        net_pay=606679.0,  # 差引支給額計
        bank_transfer_amount=608195.0
    )
    mock_client.return_value.models.generate_content.return_value = mock_response

    result = extract_payslip_data(b"pdf_bytes")
    # Must balance perfectly to 0 yen mismatch:
    assert result['commutation_allowance'] == 1516.0
    assert result['taxable_amount'] == 842950.0
    assert result['gross_pay'] == 844466.0
    assert result['total_deductions'] == 236271.0
    assert result['net_pay'] == 608195.0
    assert result['bank_transfer_amount'] == 608195.0


def test_extract_payslip_data_includes_other_descriptions_and_notes(mocker):
    from finance.career.services.payslip_extraction_service import extract_payslip_data, PayslipSchema

    mock_client = mocker.patch('finance.career.services.payslip_extraction_service.genai.Client')
    mock_response = MagicMock()
    mock_response.parsed = PayslipSchema(
        base_salary=500000.0,
        other_allowances=25000.0,
        other_allowances_description="Qualification Allowance (資格手当)",
        gross_pay=525000.0,
        social_insurance_total=60000.0,
        total_tax=40000.0,
        other_deductions=15000.0,
        other_deductions_description="Company Housing Rent (社宅費)",
        total_deductions=115000.0,
        net_pay=410000.0,
        notes="Dispatched assignment allowance included."
    )
    mock_client.return_value.models.generate_content.return_value = mock_response

    result = extract_payslip_data(b"pdf_bytes")
    assert result['other_allowances'] == 25000.0
    assert result['other_allowances_description'] == "Qualification Allowance (資格手当)"
    assert result['other_deductions'] == 15000.0
    assert result['other_deductions_description'] == "Company Housing Rent (社宅費)"
    assert result['notes'] == "Dispatched assignment allowance included."



