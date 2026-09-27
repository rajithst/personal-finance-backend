# Payslip Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a secure, stateless API pipeline that accepts uploaded payslip PDFs, extracts data via Gemini, and finally saves the document to GCS alongside database records.

**Architecture:** A stateless extraction approach where the first endpoint `/extract/` reads the PDF in memory and asks Gemini to return structured JSON. The second endpoint `/save/` uploads the client-verified data and PDF to GCS and creates the `CareerDocument` and `MonthlyPayslip` records.

**Tech Stack:** Django, Python 3.12, Google Cloud Storage, Gemini API (google-genai)

**Spec:** `docs/superpowers/specs/2026-09-27-payslip-ingestion-design.md`

## Global Constraints

- Storage paths must strictly follow `career_vault/users/user_{id}/companies/{company_slug}/payslips/{YYYY}/{YYYY-MM}_{company_slug}_payslip.pdf`.
- Extracted JSON must perfectly map to the fields of the existing `MonthlyPayslip` Django model.
- Access to documents in GCS must remain strictly private (`allUsers` blocked), exposed to the client only via short-lived Signed URLs.

## Review Focus

- **Unreadable/Corrupted PDF uploaded for extraction** (User expects a graceful failure) -> Backend returns 400 Bad Request. Test in Task 3.
- **Gemini hallucinated math where Gross != Base + Allowances** (User expects strict data integrity) -> Validation layer catches this and returns 422 Unprocessable Entity. Test in Task 2.
- **User requests a Signed URL for a document belonging to a different `user_id`** (User expects data privacy) -> Storage service raises PermissionDenied. Test in Task 1.
- **User uploads a non-PDF file** (User expects format validation) -> Endpoint returns 400 Bad Request. Test in Task 3.
- **User tries to save a payslip without the attached PDF** (User expects the system to enforce the vault requirement) -> Endpoint returns 400 Bad Request. Test in Task 4.

---

### Task 1: GCS Storage Service

**Files:**
- Create: `finance/career/services/storage_service.py`
- Test: `finance/career/tests/test_storage_service.py`

**Interfaces:**
- Consumes: Google Cloud Storage python client library.
- Produces: `upload_payslip_document(file_obj, user_id, company_slug, year, month, metadata_dict) -> str` (Returns GCS URI), `generate_signed_url(gcs_uri, user_id, requesting_user) -> str`

- [ ] **Step 1: Write the failing tests**

```python
def test_upload_payslip_document_constructs_correct_path(mocker):
    # mock GCS client
    pass

def test_generate_signed_url_enforces_user_ownership(mocker):
    # expect PermissionDenied if user_id != requesting_user.id
    pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest finance/career/tests/test_storage_service.py -v`
Expected: FAIL with ModuleNotFoundError or NameError

- [ ] **Step 3: Implement `StorageService` in `finance/career/services/storage_service.py`**

Implement path builder: `career_vault/users/user_{user_id}/companies/{company_slug}/payslips/{year}/{year}-{month:02d}_{company_slug}_payslip.pdf`. Use `google.cloud.storage`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest finance/career/tests/test_storage_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add finance/career/tests/test_storage_service.py finance/career/services/storage_service.py
git commit -m "feat: add gcs storage service for career documents"
```

---

### Task 2: AI Extraction Service

**Files:**
- Create: `finance/career/services/payslip_extraction_service.py`
- Test: `finance/career/tests/test_payslip_extraction_service.py`

**Interfaces:**
- Consumes: Gemini API (`google-genai`).
- Produces: `extract_payslip_data(pdf_bytes: bytes) -> dict`

- [ ] **Step 1: Write the failing tests**

```python
def test_extract_payslip_data_validates_math(mocker):
    # mock Gemini to return hallucinated gross pay (base 100, gross 200, no allowances)
    # assert raises ValidationError
    pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest finance/career/tests/test_payslip_extraction_service.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `extract_payslip_data` in `finance/career/services/payslip_extraction_service.py`**

Define the Pydantic schema exactly matching `MonthlyPayslip` fields. Call Gemini via `google-genai` SDK with `response_schema`. Add math validation post-generation.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest finance/career/tests/test_payslip_extraction_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add finance/career/tests/test_payslip_extraction_service.py finance/career/services/payslip_extraction_service.py
git commit -m "feat: add ai payslip extraction service with validation guard"
```

---

### Task 3: Extraction API Endpoint

**Files:**
- Modify: `finance/career/urls.py`
- Modify: `finance/career/views.py`
- Test: `finance/career/tests/test_payslip_views.py`

**Interfaces:**
- Consumes: `extract_payslip_data` from Task 2.
- Produces: `POST /api/career/payslips/extract/`

- [ ] **Step 1: Write the failing tests**

```python
def test_extract_endpoint_returns_400_for_non_pdf(client):
    # post .txt file, expect 400
    pass
    
def test_extract_endpoint_calls_service_and_returns_json(client, mocker):
    # mock extract_payslip_data, post pdf, expect 200 and json payload
    pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest finance/career/tests/test_payslip_views.py::test_extract_endpoint -v`
Expected: FAIL (404 Not Found)

- [ ] **Step 3: Implement `PayslipExtractView` in `finance/career/views.py`**

Read `request.FILES['file']`, validate content-type is `application/pdf`, read bytes into memory, call extraction service, return JSON.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest finance/career/tests/test_payslip_views.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add finance/career/urls.py finance/career/views.py finance/career/tests/test_payslip_views.py
git commit -m "feat: add payslip extraction api endpoint"
```

---

### Task 4: Save Workflow API Endpoint

**Files:**
- Modify: `finance/career/urls.py`
- Modify: `finance/career/views.py`
- Test: `finance/career/tests/test_payslip_save_view.py`

**Interfaces:**
- Consumes: `upload_payslip_document` from Task 1.
- Produces: `POST /api/career/payslips/save/`

- [ ] **Step 1: Write the failing tests**

```python
def test_save_endpoint_creates_records_and_uploads_to_gcs(client, mocker):
    # mock storage service
    # post JSON data + PDF file
    # assert CareerDocument and MonthlyPayslip created
    pass
    
def test_save_endpoint_returns_400_if_pdf_missing(client):
    # post only JSON data
    # expect 400
    pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest finance/career/tests/test_payslip_save_view.py -v`
Expected: FAIL (404 Not Found)

- [ ] **Step 3: Implement `PayslipSaveView` in `finance/career/views.py`**

Extract PDF and JSON form data. Call `upload_payslip_document`. Create `CareerDocument` with the returned GCS URI. Create `MonthlyPayslip` with the JSON data, linking the user, employment, and document. Wrap in `transaction.atomic()`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest finance/career/tests/test_payslip_save_view.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add finance/career/urls.py finance/career/views.py finance/career/tests/test_payslip_save_view.py
git commit -m "feat: add payslip save endpoint with gcs upload"
```
