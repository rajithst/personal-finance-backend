import logging
import re
from datetime import date
from dateutil import parser as dateutil_parser
from google import genai
from google.genai import types
from pydantic import BaseModel
from django.core.exceptions import ValidationError
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

    # 3. DD/MM/YYYY or MM/DD/YYYY: 1-2 digits, separator, 1-2 digits, separator, 4 digits
    dmy_match = re.match(r'^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})$', val_str)
    if dmy_match:
        p1, p2, y = int(dmy_match.group(1)), int(dmy_match.group(2)), int(dmy_match.group(3))
        if p1 > 12 >= p2:
            d, m = p1, p2
        elif p2 > 12 >= p1:
            m, d = p1, p2
        else:
            if default_month:
                if p2 == default_month and p1 != default_month:
                    d, m = p1, p2
                elif p1 == default_month and p2 != default_month:
                    m, d = p1, p2
                else:
                    d, m = p1, p2
            else:
                d, m = p1, p2
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

class PayslipSchema(BaseModel):
    # Identification & Period
    company_name: str = ""
    year: int = 0
    month: int = 0
    is_bonus: bool = False
    payment_date: str = ""
    pay_period_start: str = ""
    pay_period_end: str = ""

    # Earnings Breakdown
    base_salary: float = 0.0
    housing_allowance: float = 0.0
    discretionary_allowance: float = 0.0
    remote_work_allowance: float = 0.0
    commutation_allowance: float = 0.0
    overtime_pay: float = 0.0
    late_night_overtime_pay: float = 0.0
    holiday_work_pay: float = 0.0
    special_allowance: float = 0.0
    other_allowances: float = 0.0
    other_allowances_description: str = ""
    gross_pay: float = 0.0

    # Social Insurance Deductions
    health_insurance: float = 0.0
    nursing_insurance: float = 0.0
    pension: float = 0.0
    employment_insurance: float = 0.0
    social_insurance_total: float = 0.0

    # Taxes & Adjustments
    taxable_amount: float = 0.0
    income_tax: float = 0.0
    resident_tax: float = 0.0
    year_end_tax_adjustment: float = 0.0
    total_tax: float = 0.0

    # Other / Miscellaneous Deductions
    union_fee: float = 0.0
    mutual_aid_fee: float = 0.0
    meal_deduction: float = 0.0
    other_deductions: float = 0.0
    other_deductions_description: str = ""
    total_deductions: float = 0.0

    # Net Take-Home & Bank Transfer
    net_pay: float = 0.0
    bank_transfer_amount: float = 0.0
    bank_name: str = ""
    bank_account: str = ""

    # Notes & Remarks
    notes: str = ""

    # Attendance & Hours
    working_days: float = 0.0
    total_work_hours: float = 0.0
    overtime_hours: float = 0.0
    late_night_hours: float = 0.0
    holiday_work_hours: float = 0.0
    absent_days: float = 0.0
    loss_of_pay_days: float = 0.0
    paid_leave_days_used: float = 0.0
    remaining_paid_leave_days: float = 0.0

    # Standard Monthly Remuneration & YTD Totals
    std_remuneration_health: float = 0.0
    std_remuneration_pension: float = 0.0
    ytd_gross_pay: float = 0.0
    ytd_social_insurance: float = 0.0
    ytd_income_tax: float = 0.0


def extract_payslip_data(pdf_bytes: bytes) -> dict:
    api_key = config('GEMINI_API_KEY', default='dummy-key')
    client = genai.Client(api_key=api_key)
    
    prompt = (
        "Extract all payslip data exactly according to the schema. Put 0 for missing numbers, and empty string for missing strings.\n"
        "Important instructions for Japanese payslips:\n"
        "- year: 4-digit calendar year (e.g. 2024, 2025, 2026). If given as Japanese era year (e.g. 令和8年/R8 = 2026, 令和6年/R6 = 2024), convert to Gregorian year.\n"
        "- month: Payroll month (1-12) e.g. for 05 or 5月度, extract 5.\n"
        "- is_bonus: true if seasonal bonus statement (賞与明細 / 賞与支給明細書), false for regular monthly salary (給与明細 / 給与支給明細書).\n"
        "- company_name: Name of company/employer (e.g. アステラス製薬).\n"
        "- base_salary: 職務給 or 基本給 (e.g. 723,700).\n"
        "- housing_allowance: 住宅手当 (e.g. 45,000).\n"
        "- discretionary_allowance: 裁量労働手当 (e.g. 70,000).\n"
        "- remote_work_allowance: 在宅勤務手当 (e.g. 4,250).\n"
        "- commutation_allowance: 通勤手当 (e.g. 1,516). Commuting allowance is often listed separately or under non-taxable earnings.\n"
        "- payment_date: Payday / payment date strictly in YYYY-MM-DD format (e.g. 2025-07-25). If formatted as DD/MM/YYYY, MM/DD/YYYY, YYYY/MM/DD, or Japanese era like 令和7年7月25日, convert it to YYYY-MM-DD.\n"
        "- pay_period_start: Pay period start date strictly in YYYY-MM-DD format (e.g. 2025-06-01). Convert any other format to YYYY-MM-DD.\n"
        "- pay_period_end: Pay period end date strictly in YYYY-MM-DD format (e.g. 2025-06-30). Convert any other format to YYYY-MM-DD.\n"
        "- other_allowances: Any other miscellaneous allowance amount not covered above (e.g. 役職手当, 資格手当, その他手当).\n"
        "- other_allowances_description: Specific name or description of other_allowances (e.g. '資格手当 / Qualification Allowance' or '役職手当'). If the PDF literally names it as 'Other' or 'その他' with no other description, set this to 'Other'. If other_allowances is 0, leave empty.\n"
        "- taxable_amount: 課税対象額 or 支給額合計（課税のみ） (e.g. 842,950).\n"
        "- gross_pay: Total Gross Pay (総支給額). MUST equal sum of base_salary and ALL allowances including commutation_allowance (e.g. 723,700 + 45,000 + 70,000 + 4,250 + 1,516 = 844,466). If the payslip shows '支給額合計（課税のみ）' which excludes commuting allowance, add commutation_allowance to get the full gross_pay.\n"
        "- pension: 厚生年金保険 (e.g. 59,475).\n"
        "- health_insurance: 健康保険 (e.g. 22,534).\n"
        "- nursing_insurance: 介護保険 (e.g. 0).\n"
        "- employment_insurance: 雇用保険 (e.g. 4,222).\n"
        "- social_insurance_total: Total social insurance (sum of pension, health, nursing, employment = 86,231).\n"
        "- income_tax: 所得税 (e.g. 68,630).\n"
        "- resident_tax: 地方税 or 住民税 (e.g. 70,300).\n"
        "- total_tax: Sum of income_tax and resident_tax (e.g. 138,930).\n"
        "- union_fee: 労働組合費 (e.g. 9,400).\n"
        "- mutual_aid_fee: 共済会費 (e.g. 1,440).\n"
        "- meal_deduction: 給食代 or 食費 (e.g. 270).\n"
        "- other_deductions: Any other miscellaneous deduction amount not covered above (e.g. 社宅費, 財形貯蓄, 親睦会費, その他控除).\n"
        "- other_deductions_description: Specific name or description of other_deductions (e.g. '社宅費 / Company Housing' or '財形貯蓄'). If the PDF literally names it as 'Other' or 'その他' with no other description, set this to 'Other'. If other_deductions is 0, leave empty.\n"
        "- notes: Any remarks, communications, or notes on the payslip (連絡事項 / 備考). If other_allowances or other_deductions exist and no other note is present, summarize them here.\n"
        "- total_deductions: 控除額計 / Total deductions (e.g. 236,271).\n"
        "- net_pay: Net take-home pay (振込額 / 差引支給額合計 = 608,195). It MUST equal gross_pay - total_deductions (844,466 - 236,271 = 608,195).\n"
        "- bank_transfer_amount: 振込額 (e.g. 608,195).\n"
        "- paid_leave_days_used: 年次有休取得 (e.g. 4.0).\n"
        "- remaining_paid_leave_days: 年次有休残 (e.g. 16.0).\n"
        "- std_remuneration_health: 標準報酬月額 (健康保険 e.g. 830,000).\n"
        "- std_remuneration_pension: 標準報酬月額 (厚生年金 e.g. 650,000).\n"
        "- ytd_gross_pay: 課税対象額累計 (e.g. 4,223,930).\n"
        "- ytd_social_insurance: 社会保険料累計 (e.g. 428,668).\n"
        "- ytd_income_tax: 所得税額累計 (e.g. 345,520).\n"
        "Ensure all mathematical relationships hold exactly to the yen with zero mismatch:\n"
        "- gross_pay = sum of base_salary and all allowances (including commutation_allowance)\n"
        "- social_insurance_total = pension + health_insurance + nursing_insurance + employment_insurance\n"
        "- total_tax = income_tax + resident_tax + year_end_tax_adjustment\n"
        "- total_deductions = social_insurance_total + total_tax + union_fee + mutual_aid_fee + meal_deduction + other_deductions\n"
        "- net_pay = gross_pay - total_deductions = bank_transfer_amount\n"
    )

    models_to_try = ['gemini-3.5-flash-lite', 'gemini-3.8-flash']
    response = None
    last_error = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=PayslipSchema,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                )
            )
            if response and response.parsed:
                break
        except Exception as e:
            logger.warning("Extraction attempt with model %s failed: %s", model_name, e)
            last_error = e

    if not response or not response.parsed:
        if last_error:
            raise last_error
        raise ValidationError("Could not parse payslip data from PDF.")

    data = response.parsed
    logger.info("Raw extracted payslip data: %s", getattr(data, 'model_dump', lambda: data.__dict__)())

    # Pre-normalize extracted date strings to ISO YYYY-MM-DD
    for date_field in ('payment_date', 'pay_period_start', 'pay_period_end'):
        raw_val = getattr(data, date_field, '')
        if raw_val:
            normalized = _safe_date_or_none(raw_val, default_year=data.year if data.year > 0 else None, default_month=data.month if data.month > 0 else None)
            setattr(data, date_field, normalized or "")

    # Fallback inference for year and month if 0 or missing
    if data.year == 0 or data.month == 0:
        date_candidates = [
            getattr(data, 'payment_date', ''),
            getattr(data, 'pay_period_end', ''),
            getattr(data, 'pay_period_start', '')
        ]
        for date_str in date_candidates:
            if date_str and len(date_str) >= 7:
                try:
                    parts = date_str.split('-')
                    if len(parts) >= 2:
                        y = int(parts[0])
                        m = int(parts[1])
                        if 1990 <= y <= 2100 and 1 <= m <= 12:
                            if data.year == 0:
                                data.year = y
                            if data.month == 0:
                                data.month = m
                            break
                except (ValueError, TypeError):
                    pass

    # 1. Handle Japanese payslip pattern: Non-taxable Commuting Allowance (非課税通勤費)
    # On many Japanese payslips, "支給額合計" in the earnings box is labeled "（課税のみ）" and excludes commutation_allowance.
    # If data.gross_pay + data.commutation_allowance == calculated_gross, then data.gross_pay was taxable earnings!
    calculated_gross = sum([
        data.base_salary, data.housing_allowance, data.discretionary_allowance, 
        data.remote_work_allowance, data.commutation_allowance, data.overtime_pay, 
        data.late_night_overtime_pay, data.holiday_work_pay, data.special_allowance, 
        data.other_allowances
    ])
    if data.commutation_allowance > 0 and abs((data.gross_pay + data.commutation_allowance) - calculated_gross) <= 0.01:
        if not data.taxable_amount or data.taxable_amount == 0.0:
            data.taxable_amount = data.gross_pay
        data.gross_pay = calculated_gross

    # Strict Gross Pay Check (0 yen mismatch tolerance!)
    if abs(data.gross_pay - calculated_gross) > 0.01:
        if data.gross_pay == 0.0 and calculated_gross > 0:
            data.gross_pay = calculated_gross
        elif calculated_gross == 0.0 and data.gross_pay > 0:
            data.base_salary = data.gross_pay
            calculated_gross = data.gross_pay
        else:
            raise ValidationError(f"Gross pay validation failed: {data.gross_pay} != {calculated_gross}")

    # 2. Strict Social Insurance Validation
    calculated_social = sum([data.health_insurance, data.nursing_insurance, data.pension, data.employment_insurance])
    if abs(data.social_insurance_total - calculated_social) > 0.01:
        if data.social_insurance_total == 0.0 and calculated_social > 0.0:
            data.social_insurance_total = calculated_social
        elif calculated_social == 0.0 and data.social_insurance_total > 0.0:
            data.health_insurance = data.social_insurance_total
            calculated_social = data.social_insurance_total
        else:
            raise ValidationError(f"Social insurance validation failed: {data.social_insurance_total} != {calculated_social}")

    # 3. Strict Taxes Validation
    calculated_tax = sum([data.income_tax, data.resident_tax, data.year_end_tax_adjustment])
    if abs(data.total_tax - calculated_tax) > 0.01:
        if data.total_tax == 0.0 and calculated_tax > 0.0:
            data.total_tax = calculated_tax
        elif calculated_tax == 0.0 and data.total_tax > 0.0:
            data.income_tax = data.total_tax
            calculated_tax = data.total_tax
        else:
            raise ValidationError(f"Total tax validation failed: {data.total_tax} != {calculated_tax}")

    # 4. Strict Deductions Validation
    calculated_deductions = sum([
        data.social_insurance_total, data.total_tax,
        data.union_fee, data.mutual_aid_fee, data.meal_deduction, data.other_deductions
    ])
    if abs(data.total_deductions - calculated_deductions) > 0.01:
        if data.total_deductions == 0.0 and calculated_deductions > 0.0:
            data.total_deductions = calculated_deductions
        else:
            raise ValidationError(f"Total deductions validation failed: {data.total_deductions} != {calculated_deductions}")

    # 5. Handle Non-taxable Commuting Allowance on Net Pay:
    # If net_pay was extracted as taxable net (差引支給額計) excluding commutation allowance, adjust it to match bank transfer!
    calculated_net = data.gross_pay - data.total_deductions
    if data.commutation_allowance > 0 and abs((data.net_pay + data.commutation_allowance) - calculated_net) <= 0.01:
        data.net_pay = calculated_net

    # Strict Net Pay Check (0 yen mismatch tolerance!)
    if abs(data.net_pay - calculated_net) > 0.01:
        if data.net_pay == 0.0 and calculated_net > 0.0:
            data.net_pay = calculated_net
        else:
            raise ValidationError(f"Net pay validation failed: {data.net_pay} != {calculated_net}")

    # If bank_transfer_amount is 0 or omitted, set to net_pay
    if not data.bank_transfer_amount or data.bank_transfer_amount == 0.0:
        data.bank_transfer_amount = data.net_pay

    # 6. Ensure default "Other" if other_allowances / other_deductions > 0 but description is empty
    if getattr(data, 'other_allowances', 0) > 0 and not getattr(data, 'other_allowances_description', ''):
        data.other_allowances_description = "Other"
    if getattr(data, 'other_deductions', 0) > 0 and not getattr(data, 'other_deductions_description', ''):
        data.other_deductions_description = "Other"

    # Default note if notes is empty and descriptions exist
    if not getattr(data, 'notes', ''):
        note_parts = []
        if getattr(data, 'other_allowances_description', ''):
            note_parts.append(f"Other Allowance: {data.other_allowances_description}")
        if getattr(data, 'other_deductions_description', ''):
            note_parts.append(f"Other Deduction: {data.other_deductions_description}")
        if note_parts:
            data.notes = "; ".join(note_parts)

    if hasattr(data, 'model_dump'):
        return data.model_dump()
    # For tests
    return {k: v for k, v in data.__dict__.items() if not k.startswith('_')}
