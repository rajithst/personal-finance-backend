import logging
import re
from datetime import date
from dateutil import parser as dateutil_parser
from google import genai
from google.genai import types
from pydantic import BaseModel
from decouple import config

logger = logging.getLogger(__name__)


def _safe_date_or_none(val, default_year=None, default_month=None) -> str | None:
    if not val:
        return None
    val_str = str(val).strip()
    if not val_str:
        return None

    # 1. Standard ISO format: YYYY-MM-DD
    iso_match = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})$', val_str)
    if iso_match:
        y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
        try:
            return date(y, m, d).isoformat()
        except ValueError:
            return None

    # 2. YYYY/MM/DD or YYYY.MM.DD or YYYY年M月D日
    ymd_match = re.match(r'^(\d{4})[/.\-年](\d{1,2})[/.\-月](\d{1,2})日?$', val_str)
    if ymd_match:
        y, m, d = int(ymd_match.group(1)), int(ymd_match.group(2)), int(ymd_match.group(3))
        try:
            return date(y, m, d).isoformat()
        except ValueError:
            return None

    # 3. Japanese Imperial format: 令和X年M月D日 or 平成X年M月D日
    reiwa_match = re.match(r'^令和?\s*(\d{1,2})[/.\-年](\d{1,2})[/.\-月](\d{1,2})日?$', val_str)
    if reiwa_match:
        y = 2018 + int(reiwa_match.group(1))
        m = int(reiwa_match.group(2))
        d = int(reiwa_match.group(3))
        try:
            return date(y, m, d).isoformat()
        except ValueError:
            return None

    try:
        parsed = dateutil_parser.parse(val_str, dayfirst=True)
        return parsed.date().isoformat()
    except Exception:
        pass

    return None


def _resolve_japanese_year(val) -> int:
    """Converts Japanese imperial year or integer year to 4-digit Gregorian year."""
    if not val:
        return 0
    val_str = str(val).strip()

    # Direct 4-digit year
    year_match = re.match(r'^(19\d\d|20\d\d)$', val_str)
    if year_match:
        return int(year_match.group(1))

    # 令和X年 or RX
    reiwa_match = re.search(r'(?:令和|R)\s*(\d{1,2})', val_str, re.IGNORECASE)
    if reiwa_match:
        return 2018 + int(reiwa_match.group(1))

    # 平成X年 or HX
    heisei_match = re.search(r'(?:平成|H)\s*(\d{1,2})', val_str, re.IGNORECASE)
    if heisei_match:
        return 1988 + int(heisei_match.group(1))

    # If small number, assume Reiwa (e.g. 5 -> 2023, 6 -> 2024)
    try:
        num = int(val_str)
        if 1 <= num <= 50:
            return 2018 + num
        if 1900 <= num <= 2100:
            return num
    except (ValueError, TypeError):
        pass

    return 0


class TaxSlipSchema(BaseModel):
    # Payer & Identity
    company_name: str = ""
    tax_year: int = 0
    issue_date: str = ""

    # 4 Core Statutory Boxes
    total_payment: float = 0.0
    income_after_deduction: float = 0.0
    total_income_deductions: float = 0.0
    withholding_tax: float = 0.0

    # Detailed Deductions & Exemptions
    social_insurance_deduction: float = 0.0
    basic_deduction: float = 480000.0
    life_insurance_deduction: float = 0.0
    earthquake_insurance_deduction: float = 0.0
    housing_loan_deduction: float = 0.0
    spouse_deduction: float = 0.0
    dependents_count: int = 0

    # Notes & Remarks
    notes: str = ""


def extract_tax_slip_data(pdf_bytes: bytes) -> dict:
    api_key = config('GEMINI_API_KEY', default='dummy-key')
    client = genai.Client(api_key=api_key)

    prompt = (
        "You are an expert tax accountant reviewing a Japanese Annual Withholding Tax Certificate "
        "(給与所得の源泉徴収票 / Gensen-Chōshū-Hyō).\n"
        "Extract all fields exactly according to the schema. Put 0 for missing numbers, and empty string for missing strings.\n"
        "Instructions for Japanese tax certificates:\n"
        "- company_name: Name of payer/employer (支払者の氏名又は名称, e.g. ロバート・ウォルターズ・ジャパン株式会社).\n"
        "- tax_year: 4-digit Gregorian calendar year (e.g. 令和5年 -> 2023, 令和6年 -> 2024, 2023 -> 2023). "
        "  If written as 令和X年 or 5年分, convert to the 4-digit Gregorian year (2018 + X).\n"
        "- issue_date: Date of issue or retirement (交付年月日 or 退職年月日) in YYYY-MM-DD.\n"
        "- total_payment: 支払金額 (Total annual gross pay before deductions).\n"
        "- income_after_deduction: 給与所得控除後の金額 (Income after salary earner deduction).\n"
        "- total_income_deductions: 所得控除の額の合計額 (Total allowable income deductions).\n"
        "- withholding_tax: 源泉徴収税額 (Final national withholding tax amount).\n"
        "- social_insurance_deduction: 社会保険料等の金額 (Annual health, pension, employment insurance total).\n"
        "- basic_deduction: 基礎控除の額 (Standard personal deduction, typically 480,000 for income <= 24M).\n"
        "- life_insurance_deduction: 生命保険料の控除額.\n"
        "- earthquake_insurance_deduction: 地震保険料の控除額.\n"
        "- housing_loan_deduction: 住宅借入金等特別控除の額 (Mortgage tax credit).\n"
        "- spouse_deduction: 配偶者(特別)控除の額.\n"
        "- dependents_count: 控除対象扶養親族の数 (Total count of dependents).\n"
        "- notes: 摘要 (Any remarks, e.g. '年調済み', '中途就・退職', '普D', etc.).\n"
    )

    models_to_try = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite"]
    data = None
    last_error = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(
                        data=pdf_bytes,
                        mime_type="application/pdf",
                    ),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TaxSlipSchema,
                ),
            )
            data = response.parsed
            break
        except Exception as e:
            logger.warning("Tax slip extraction attempt with model %s failed: %s", model_name, e)
            last_error = e

    if not data:
        raise last_error or RuntimeError("Tax slip extraction failed across all models.")

    raw_dict = getattr(data, 'model_dump', lambda: data.__dict__)()

    # Normalize Year
    tax_year = _resolve_japanese_year(raw_dict.get('tax_year'))
    if not tax_year or tax_year < 1900 or tax_year > 2100:
        # Default to current year or fallback
        tax_year = date.today().year

    # Normalize Issue Date
    issue_date = _safe_date_or_none(raw_dict.get('issue_date'))
    if not issue_date:
        issue_date = f"{tax_year}-12-25"

    # Normalize Basic Deduction
    basic_ded = float(raw_dict.get('basic_deduction') or 0.0)
    total_ded = float(raw_dict.get('total_income_deductions') or 0.0)
    if basic_ded == 0.0 and total_ded > 0:
        basic_ded = 480000.0

    result = {
        'company_name': str(raw_dict.get('company_name') or '').strip(),
        'tax_year': int(tax_year),
        'issue_date': issue_date,
        'total_payment': float(raw_dict.get('total_payment') or 0.0),
        'income_after_deduction': float(raw_dict.get('income_after_deduction') or 0.0),
        'total_income_deductions': total_ded,
        'withholding_tax': float(raw_dict.get('withholding_tax') or 0.0),
        'social_insurance_deduction': float(raw_dict.get('social_insurance_deduction') or 0.0),
        'basic_deduction': basic_ded,
        'life_insurance_deduction': float(raw_dict.get('life_insurance_deduction') or 0.0),
        'earthquake_insurance_deduction': float(raw_dict.get('earthquake_insurance_deduction') or 0.0),
        'housing_loan_deduction': float(raw_dict.get('housing_loan_deduction') or 0.0),
        'spouse_deduction': float(raw_dict.get('spouse_deduction') or 0.0),
        'dependents_count': int(raw_dict.get('dependents_count') or 0),
        'notes': str(raw_dict.get('notes') or '').strip(),
    }

    return result
