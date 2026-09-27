from google import genai
from pydantic import BaseModel
from django.core.exceptions import ValidationError
from django.conf import settings

class PayslipSchema(BaseModel):
    base_salary: int
    overtime_pay: int
    allowances: int
    gross_pay: int
    tax_deductions: int
    insurance_deductions: int
    other_deductions: int
    net_pay: int

def extract_payslip_data(pdf_bytes: bytes) -> dict:
    api_key = getattr(settings, 'GEMINI_API_KEY', 'dummy-key')
    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            "Extract all payslip data exactly according to the schema.",
            {"mime_type": "application/pdf", "data": pdf_bytes}
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": PayslipSchema,
        }
    )
    
    data = response.parsed
    
    calculated_gross = data.base_salary + data.overtime_pay + data.allowances
    if data.gross_pay != calculated_gross:
        raise ValidationError(f"Gross pay validation failed: {data.gross_pay} != {calculated_gross}")
        
    calculated_net = data.gross_pay - (data.tax_deductions + data.insurance_deductions + data.other_deductions)
    if data.net_pay != calculated_net:
        raise ValidationError(f"Net pay validation failed: {data.net_pay} != {calculated_net}")
        
    if hasattr(data, 'model_dump'):
        return data.model_dump()
    # For tests
    return {k: v for k, v in data.__dict__.items() if not k.startswith('_')}
