# Career Hub: Japanese Withholding Tax Slip (源泉徴収票) AI Extraction & Cloud Vault Ingestion

## 1. Executive Summary

This architecture specification details the end-to-end AI extraction, automatic form population, and secure cloud archiving for Japanese Annual Withholding Tax Certificates (*給与所得の源泉徴収票 / Gensen-Chōshū-Hyō*). 

Building directly on the established patterns of the `MonthlyPayslip` ingestion architecture:
1. **Stateless AI Extraction Pipeline**: Extracts official Japanese statutory tax boxes and employer data in memory via Gemini Multimodal Structured Output without persisting orphaned files.
2. **Interactive Client Review & Autofill**: Provides real-time autofill inside `TaxSlipModal`, matching the extracted employer against registered employment tenures and leaving all fields editable for user confirmation.
3. **Atomic Cloud Vault Archiving**: On save, atomically commits the verified tax slip record, persists the original PDF into Career Vault (`CareerDocument` in GCS/local media), and creates the cross-reference linkage.

---

## 2. Extraction Schema & Japanese Tax Box Mapping

### 2.1 Pydantic Extraction Contract (`TaxSlipSchema`)
Defined in `finance/career/services/tax_slip_extraction_service.py` to match the official National Tax Agency (*国税庁*) annual statement and the existing `TaxWithholdingSlip` Django model 1-to-1:

```python
from pydantic import BaseModel

class TaxSlipSchema(BaseModel):
    # Payer & Identity
    company_name: str = ""                # 支払者の氏名又は名称 (e.g. ロバート・ウォルターズ・ジャパン株式会社)
    tax_year: int = 0                     # 4-digit Gregorian year (e.g. 令和5年 -> 2023)
    issue_date: str = ""                  # 交付年月日 or 退職年月日 (YYYY-MM-DD)
    
    # 4 Core Statutory Boxes
    total_payment: float = 0.0            # 支払金額 (Total annual gross earnings before deductions)
    income_after_deduction: float = 0.0   # 給与所得控除後の金額 (Income after employment deductions)
    total_income_deductions: float = 0.0  # 所得控除の額の合計額 (Total allowable deductions)
    withholding_tax: float = 0.0          # 源泉徴収税額 (Final withholding income tax)
    
    # Detailed Statutory Deductions & Exemptions
    social_insurance_deduction: float = 0.0      # 社会保険料等の金額 (Annual health, pension, employment)
    basic_deduction: float = 480000.0            # 基礎控除の額 (Standard statutory basic deduction)
    life_insurance_deduction: float = 0.0        # 生命保険料の控除額
    earthquake_insurance_deduction: float = 0.0    # 地震保険料の控除額
    housing_loan_deduction: float = 0.0          # 住宅借入金等特別控除の額 (Mortgage tax credit)
    spouse_deduction: float = 0.0                # 配偶者(特別)控除の額
    dependents_count: int = 0                    # 控除対象扶養親族の数
    
    # Remarks
    notes: str = ""                       # 摘要 (e.g. 年調済み, resignation date remarks, etc.)
```

### 2.2 Era Conversion & Deterministic Normalization
1. **Japanese Imperial Era Mapping**:
   - `令和` (Reiwa) $X$ 年 $\to 2018 + X$ (e.g. 令和5年 $\to 2023$, 令和6年 $\to 2024$).
   - `平成` (Heisei) $X$ 年 $\to 1988 + X$ (e.g. 平成30年 $\to 2018$).
2. **Basic Deduction Fallback**:
   - Statutory basic personal deduction in Japan is ¥480,000 for income $\le$ ¥24,000,000. If the field is omitted on the printed document, the extractor verifies against `total_income_deductions` and populates `480000.0`.
3. **Date Resolution**:
   - Parses dates into strict ISO format (`YYYY-MM-DD`). Defaults to December 25th of the tax year or the departure date if specified.

---

## 3. Backend Architecture & Endpoints

### 3.1 Service Layer (`finance/career/services/tax_slip_extraction_service.py`)
* `extract_tax_slip_data(pdf_bytes: bytes) -> dict`:
  - Instantiates `genai.Client(api_key=config('GEMINI_API_KEY'))`.
  - Prompts Gemini with structured output constraints.
  - Multi-tier model fallback: attempts `gemini-2.5-flash` first; on API failure, falls back to `gemini-1.5-flash`.
  - Applies normalization and returns a dictionary.

### 3.2 Extract Endpoint (`TaxSlipExtractView`)
* **URL**: `POST /finance/career/tax-slips/extract/`
* **Input**: Multipart `file` (application/pdf, $\le 10$ MB).
* **Processing**: In-memory byte read $\to$ `extract_tax_slip_data` $\to$ returns JSON payload.
* **Database State**: Zero mutations (stateless).

### 3.3 Atomic Save Endpoint (`TaxSlipSaveView`)
* **URL**: `POST /finance/career/tax-slips/save/`
* **Input**: Multipart form with `file` (PDF) and `data` (JSON string of reviewed form values).
* **Processing (within `transaction.atomic()` commit block)**:
  1. Resolves `employment = Employment.objects.get(id=employment_id, user=request.user)`.
  2. Uploads the original PDF using `storage_service.py` to GCS (or local media in debug) with path:
     `career_vault/users/user_{user_id}/companies/{company_slug}/documents/tax_withholding_slip/{timestamp}_{safe_name}`.
  3. Creates a `CareerDocument` DB record with `document_type='tax_withholding_slip'`, linked to the company and employment.
  4. Upserts the `TaxWithholdingSlip` record via `update_or_create` on `(employment, tax_year)` to idempotently handle re-uploads.
  5. Attaches `document = doc` to the `TaxWithholdingSlip`.
  6. Returns `{ "message": "Tax slip and vault document saved successfully.", "tax_slip_id": slip.id }`.

---

## 4. Frontend Architecture & Modal UX

### 4.1 Client Service (`careerService.ts`)
* `extractTaxSlip(file: File): Promise<any>`
* `saveExtractedTaxSlip(file: File, data: any): Promise<{ message: string; tax_slip_id: number }>`

### 4.2 Modal Component (`TaxSlipModal.tsx`)
* **AI Auto-fill Dropzone**:
  - Displays dropzone banner with `<Sparkles />` icon: *"Autofill from Tax Slip PDF"*.
  - When user attaches a PDF: triggers extraction with a loading spinner and *"Extracting..."* state.
  - On extraction success: displays green `<CheckCircle2 />` banner with file name, file size in KB, and detach button.
* **Form Field Auto-Population**:
  - Pre-fills `taxYear`, `issueDate`, `totalPayment`, `incomeAfterDeduction`, `totalIncomeDeductions`, `withholdingTax`, and all detailed deduction inputs.
  - Pre-fills `notes` (e.g. "年調済み").
  - **Fuzzy Employer Matching**: Scans `employments` and automatically selects the matching employer ID based on the extracted `company_name`.
* **Form Submission**:
  - If a PDF file was uploaded, calls `onSaveWithFile(uploadedFile, payload)`.
  - If manually entered without PDF, calls existing `onSave(payload)`.

### 4.3 Container View (`CareerHubView.tsx`)
* Implements `handleSaveTaxSlipWithFile`:
  ```tsx
  const handleSaveTaxSlipWithFile = async (file: File, data: Partial<TaxWithholdingSlip>) => {
    await careerService.saveExtractedTaxSlip(file, data);
    await loadData();
  };
  ```
* Passes `onSaveWithFile={handleSaveTaxSlipWithFile}` to `<TaxSlipModal />`.

---

## 5. Security, Validation & Error Handling

1. **Authentication & Tenant Isolation**: All endpoints require JWT authentication. Objects and database records are strictly scoped to `request.user`.
2. **File Validation**: Enforces MIME type check (`application/pdf`) and rejects files exceeding 10 MB.
3. **Idempotent Updates**: `TaxWithholdingSlip` has a unique constraint on `(employment, tax_year)`. The backend handles re-uploads cleanly through `update_or_create`.
4. **Graceful Degradation**: If AI extraction encounters an unreadable file or API failure, an informative inline error banner is rendered and the form remains fully functional for manual data entry.

---

## 6. Testing Strategy

1. **Service Tests** (`finance/career/tests/test_tax_slip_extraction_service.py`):
   - Structured JSON output parsing with mocked `genai.Client`.
   - Japanese era conversion (令和5年 $\to$ 2023, 令和6年 $\to$ 2024, 平成30年 $\to$ 2018).
   - Basic deduction inference and deduction arithmetic.
   - Primary to secondary model fallback on simulated API error.
2. **View Tests** (`finance/career/tests/test_tax_slip_views.py`):
   - Rejecting non-PDF and oversized file uploads.
   - Extract endpoint payload generation.
   - Save endpoint atomic document creation, storage upload, and tax slip upsert.
3. **Frontend Compilation**:
   - `npm run build` (`tsc -b && vite build`) verifying TypeScript type safety.
