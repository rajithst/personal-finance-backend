# Tax Slip AI Extraction & Cloud Vault Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an end-to-end AI-powered upload and extraction system for Japanese Annual Withholding Tax Slips (給与所得の源泉徴収票 / Gensen Chōshūhyō) that extracts official box amounts via Gemini, auto-fills the `TaxSlipModal` form, and atomically archives the PDF into Career Vault.

**Architecture:** A stateless extraction flow where `POST /finance/career/tax-slips/extract/` reads the uploaded PDF in-memory and prompts Gemini with a structured Pydantic schema mapping directly to Japanese tax boxes. The client reviews and edits the values in `TaxSlipModal`, then submits both the verified form payload and PDF to `POST /finance/career/tax-slips/save/`, which atomically uploads the file to storage (GCS/local), creates a linked `CareerDocument`, and upserts the `TaxWithholdingSlip` database record.

**Tech Stack:** Django, Python 3.12, Google Cloud Storage, Gemini API (`google-genai`), React 18, TypeScript, Vite

**Spec:** `docs/superpowers/specs/2026-10-03-tax-slip-ai-extraction-design.md`

## Global Constraints

- Storage paths must strictly follow `career_vault/users/user_{id}/companies/{company_slug}/documents/tax_withholding_slip/{timestamp}_{safe_name}` via `upload_career_document`.
- Extracted JSON must perfectly map to the fields of the existing `TaxWithholdingSlip` Django model (`total_payment`, `income_after_deduction`, `total_income_deductions`, `withholding_tax`, etc.).
- The system must accurately convert Japanese imperial era years (令和5年 $\to$ 2023, 令和6年 $\to$ 2024, etc.) and handle standard statutory deductions (basic personal deduction of ¥480,000).
- Saving a tax slip with a PDF must be atomic: if storage upload or DB record creation fails, no orphaned state or partial records remain.
- Existing records must be safely updated if a slip already exists for the same `(employment, tax_year)`.

## Review Focus

- **Non-PDF or corrupted file uploaded for extraction** (User expects format validation) -> Endpoint returns 400 Bad Request. Tested in Task 2.
- **File size exceeds 10 MB limit** (User expects upload size enforcement) -> Endpoint rejects with 400 Bad Request. Tested in Task 2.
- **Japanese era year representation in PDF** (User expects automatic conversion e.g. 令和5年 to 2023) -> Extractor converts to Gregorian integer. Tested in Task 1.
- **Re-uploading a tax slip for an existing employment & tax year** (User expects update rather than IntegrityError) -> Save endpoint uses `update_or_create` to update existing slip and link new document. Tested in Task 2.
- **Employer name on Japanese certificate differs slightly from English database record** (User expects intelligent fuzzy matching) -> Frontend matches substring/case to preselect employment. Tested in Task 3.

---

### Task 1: Tax Slip AI Extraction Service

**Files:**
- Create: `finance/career/services/tax_slip_extraction_service.py`
- Test: `finance/career/tests/test_tax_slip_extraction_service.py`

**Interfaces:**
- Consumes: Gemini API (`google-genai`).
- Produces: `extract_tax_slip_data(pdf_bytes: bytes) -> dict` returning normalized dictionary with keys matching `TaxWithholdingSlip` model fields plus `company_name`.

- [x] **Step 1: Write the failing tests**

```python
def test_extract_tax_slip_data_converts_era_and_fields(mocker):
    # Mock genai.Client response with Reiwa 5 era year and official Japanese boxes
    # Assert extracted dict has tax_year == 2023, total_payment, withholding_tax, etc.
    pass

def test_extract_tax_slip_data_basic_deduction_default(mocker):
    # Mock genai response with basic_deduction = 0 but total deductions present
    # Assert basic_deduction defaults to 480000.0
    pass

def test_extract_tax_slip_data_model_fallback(mocker):
    # Mock primary model exception, ensure secondary model is called
    pass
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest finance/career/tests/test_tax_slip_extraction_service.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'finance.career.services.tax_slip_extraction_service'`

- [x] **Step 3: Implement `TaxSlipSchema` and `extract_tax_slip_data`**

In `finance/career/services/tax_slip_extraction_service.py`:
1. Define `TaxSlipSchema(BaseModel)` matching the official Japanese statutory boxes (`company_name`, `tax_year`, `issue_date`, `total_payment`, `income_after_deduction`, `total_income_deductions`, `withholding_tax`, `social_insurance_deduction`, `basic_deduction`, `life_insurance_deduction`, `earthquake_insurance_deduction`, `housing_loan_deduction`, `spouse_deduction`, `dependents_count`, `notes`).
2. Implement prompt targeting Japanese *給与所得の源泉徴収票*, instructing Gemini to convert Japanese imperial era years (令和 $X$ 年 $\to 2018 + X$) and extract numbers without commas.
3. Call `client.models.generate_content` using `gemini-2.5-flash` with fallback to `gemini-1.5-flash`.
4. Apply normalization for dates and default `basic_deduction` to `480000.0` when total income deductions exist.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest finance/career/tests/test_tax_slip_extraction_service.py -v`
Expected: PASS

---

### Task 2: Tax Slip Extract & Save API Views

**Files:**
- Modify: `finance/career/views.py`
- Modify: `finance/career/urls.py`
- Test: `finance/career/tests/test_tax_slip_views.py`

**Interfaces:**
- Consumes: `extract_tax_slip_data`, `upload_career_document`, `TaxWithholdingSlip`, `CareerDocument`, `Employment`.
- Produces:
  - `POST /finance/career/tax-slips/extract/` -> returns `{ "data": extracted_dict }`
  - `POST /finance/career/tax-slips/save/` -> returns `{ "message": str, "tax_slip_id": int }`

- [x] **Step 1: Write the failing view tests**

In `finance/career/tests/test_tax_slip_views.py`:
```python
def test_tax_slip_extract_rejects_non_pdf(api_client):
    # Upload text file to /finance/career/tax-slips/extract/ -> 400
    pass

def test_tax_slip_extract_returns_extracted_json(api_client, mocker):
    # Mock extract_tax_slip_data, upload PDF -> 200 with data
    pass

def test_tax_slip_save_creates_document_and_slip(api_client, mocker):
    # Post multipart file + data -> 201/200, CareerDocument created, TaxWithholdingSlip created
    pass

def test_tax_slip_save_updates_existing_slip(api_client, mocker):
    # Post same employment and tax_year -> updates existing slip without IntegrityError
    pass
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest finance/career/tests/test_tax_slip_views.py -v`
Expected: FAIL with 404 Not Found (URLs not registered)

- [x] **Step 3: Implement `TaxSlipExtractView` and `TaxSlipSaveView`**

1. In `finance/career/views.py`:
   - `TaxSlipExtractView(APIView)`: Validates PDF mime type and 10MB limit; reads bytes and calls `extract_tax_slip_data`; returns JSON.
   - `TaxSlipSaveView(APIView)`: Uses `MultiPartParser`; validates `file` and `data`; parses JSON payload; inside `transaction.atomic()`, uploads PDF via `upload_career_document`, creates `CareerDocument` (`document_type='tax_withholding_slip'`), and upserts `TaxWithholdingSlip` with `update_or_create(employment=employment, tax_year=year, defaults=...)`.
2. In `finance/career/urls.py`:
   - Register `path('tax-slips/extract/', TaxSlipExtractView.as_view(), name='career-tax-slip-extract')`
   - Register `path('tax-slips/save/', TaxSlipSaveView.as_view(), name='career-tax-slip-save')`

- [x] **Step 4: Run test to verify it passes**

Run: `pytest finance/career/tests/test_tax_slip_views.py -v`
Expected: PASS

---

### Task 3: Frontend API & `TaxSlipModal` Integration

**Files:**
- Modify: `personalfinance-web/src/services/careerService.ts`
- Modify: `personalfinance-web/src/components/career/TaxSlipModal.tsx`
- Modify: `personalfinance-web/src/components/career/CareerHubView.tsx`

**Interfaces:**
- Consumes: `/finance/career/tax-slips/extract/` and `/finance/career/tax-slips/save/`.
- Produces:
  - `careerService.extractTaxSlip(file: File)`
  - `careerService.saveExtractedTaxSlip(file: File, data: any)`
  - `TaxSlipModal` with AI auto-fill dropzone and `onSaveWithFile` support.

- [x] **Step 1: Add frontend API methods in `careerService.ts`**

Add `extractTaxSlip(file: File)` and `saveExtractedTaxSlip(file: File, data: any)` following the exact pattern of `extractPayslip` and `saveExtractedPayslip`.

- [x] **Step 2: Update `TaxSlipModal.tsx` with AI Autofill Card**

1. Add `onSaveWithFile?: (file: File, data: Partial<TaxWithholdingSlip>) => Promise<void>` to `TaxSlipModalProps`.
2. Add `uploadedFile: File | null` and `isExtracting: boolean` states.
3. Render the ambient upload card (matching `PayslipModal`):
   - Sparkles icon: *"Autofill from Tax Slip PDF"* when empty.
   - Green badge + file info + remove button when file is attached.
4. When a PDF is selected:
   - Call `careerService.extractTaxSlip(file)`.
   - Populate `taxYear`, `issueDate`, `totalPayment`, `incomeAfterDeduction`, `totalIncomeDeductions`, `withholdingTax`, `socialInsuranceDeduction`, `basicDeduction`, other deductions, and `notes`.
   - Fuzzy match `data.company_name` against `employments` to automatically select `employmentId`.
5. On form submit:
   - If `uploadedFile && onSaveWithFile`: call `await onSaveWithFile(uploadedFile, payload)`.
   - Else: call `await onSave(payload)`.

- [x] **Step 3: Connect `handleSaveTaxSlipWithFile` in `CareerHubView.tsx`**

1. Implement `handleSaveTaxSlipWithFile = async (file: File, data: Partial<TaxWithholdingSlip>) => { await careerService.saveExtractedTaxSlip(file, data); await loadData(); }`.
2. Pass `onSaveWithFile={handleSaveTaxSlipWithFile}` to `<TaxSlipModal />`.

- [x] **Step 4: Verify frontend builds cleanly**

Run: `npm run build` in `personalfinance-web`
Expected: exit code 0, zero TypeScript errors.

---

### Task 4: End-to-End Test Suite & Verification

**Files:**
- Test: Full backend career test suite (`finance/career/tests/`)
- Build: Frontend production bundle

- [x] **Step 1: Run complete backend pytest suite**

Run: `pytest finance/career/tests/ -v`
Expected: All tests pass.

- [x] **Step 2: Verify frontend compilation**

Run: `npm run build` in `personalfinance-web`
Expected: Build passes with 0 errors.
