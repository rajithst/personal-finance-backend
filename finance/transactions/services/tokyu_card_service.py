import logging
from typing import List, Optional
from pydantic import BaseModel
from decouple import config
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class TokyuTransactionItem(BaseModel):
    date: str                  # "YYYY-MM-DD". If missing on row, defaults to billing/payment date
    destination: str           # Merchant or description (e.g. "ユニクロ", "Tokyu Card Cashing Installment Fee")
    destination_original: str = "" # Original raw statement string in Japanese (e.g. "ユニクロ", "※キャッシングリボ返済金※")
    amount: float              # JPY amount
    payment_type: str = ""     # "1回払い", "リボ", "分割", "キャッシング", etc.
    is_fee_or_interest: bool = False  # True if this is finance charge / installment interest


class TokyuStatementSchema(BaseModel):
    statement_year_month: str = ""   # "YYYY-MM" (e.g. "2026-08")
    payment_date: str = ""           # "YYYY-MM-DD" (e.g. "2026-08-10" - Tokyu payment day is typically the 10th)
    card_last4: str = ""             # Masked card number (e.g. "85**")
    total_payment_due: float = 0.0   # Total billing amount for the month
    shopping_subtotal: float = 0.0   # Shopping purchase total
    cashing_principal: float = 0.0   # Cash advance principal repayment
    cashing_interest: float = 0.0    # Cash advance interest / fee
    transactions: List[TokyuTransactionItem] = []


def extract_tokyu_statement(csv_text: str, client: Optional[genai.Client] = None, file_name: str = "") -> TokyuStatementSchema:
    """
    Uses Gemini to extract structured statement details and transactions from a Tokyu Card CSV.
    Handles standard purchase months as well as installment-only / cashing months where
    point-of-sale dates may not be present on individual rows.
    """
    if client is None:
        api_key = config('GEMINI_API_KEY', default='dummy-key')
        client = genai.Client(api_key=api_key)

    file_hint = f" (from file: {file_name})" if file_name else ""
    prompt = (
        f"You are an expert Japanese credit card financial analyst extracting data from a Tokyu Card (東急カード) CSV statement{file_hint}.\n"
        "Extract all fields strictly adhering to the schema.\n\n"
        "Guidelines for Tokyu Card CSV format:\n"
        "1. Statement Month & Payment Date:\n"
        "   - Identify the statement month / billing cycle from the top headers, file metadata, or file name (e.g. '202608.csv' or '2026年8月10日お支払い分' -> statement_year_month: '2026-08', payment_date: '2026-08-10').\n"
        "   - Tokyu Card payments are due on the 10th of the month. If the exact payment date is not specified, format it as 'YYYY-MM-10'.\n"
        "2. Itemized Shopping Purchases:\n"
        "   - Rows with dates (e.g. '2025/08/07', '2026/01/15') are purchases.\n"
        "   - Extract the date in ISO format ('YYYY-MM-DD'), merchant name as destination, original statement text as destination_original, and amount.\n"
        "   - If payment method is present (e.g., '1回払い', '2回払い', 'リボ払い'), capture it.\n"
        "3. Summary & Installment/Cashing Months (CRITICAL):\n"
        "   - Some months (e.g., 202608.csv) contain NO new shopping purchases, but contain monthly installment payments for cash advances (キャッシング返済 / キャッシング元金・利息・手数料).\n"
        "   - In these months, summary rows will show the cash advance installment or interest (e.g. 54,315 JPY or interest 4,315 JPY).\n"
        "   - If there are NO point-of-sale purchase rows, extract the installment interest/fee as a transaction item dated on the payment_date with destination 'Tokyu Card Cashing Installment Fee', destination_original set to the statement row text (e.g. '※キャッシングリボ返済金※'), and is_fee_or_interest=True.\n"
        "4. Totals:\n"
        "   - Extract shopping_subtotal, cashing_principal, cashing_interest, and total_payment_due where present.\n"
        "   - Put 0.0 for any missing numbers and empty strings for missing strings.\n"
    )

    models_to_try = [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-3.8-flash",
        "gemini-flash-lite-latest",
    ]
    last_error = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    f"Tokyu Card Statement CSV Content:\n```csv\n{csv_text}\n```",
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TokyuStatementSchema,
                ),
            )
            if response.parsed:
                parsed = response.parsed
                if file_name and not parsed.statement_year_month:
                    import re
                    m = re.search(r'(20\d{2})[-_]?(\d{2})', file_name)
                    if m:
                        parsed.statement_year_month = f"{m.group(1)}-{m.group(2)}"
                        if not parsed.payment_date:
                            parsed.payment_date = f"{parsed.statement_year_month}-10"
                return parsed
        except Exception as e:
            logger.warning("Tokyu statement extraction with model %s failed: %s", model_name, e)
            last_error = e

    if last_error:
        raise last_error
    raise RuntimeError("Failed to extract Tokyu Card statement using Gemini.")
