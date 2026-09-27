# Career Hub: Payslip Ingestion, AI Extraction & Cloud Storage Architecture

## 1. Executive Summary

This architecture plan defines an automated, secure, and human-navigable solution for:
1. **Cloud Storage (GCS) File Hierarchy**: Storing uploaded career documents (payslips, etc.) in a clean, predictable, and browseable directory structure.
2. **Automated AI Extraction & Auto-Population**: Extracting values from payslip PDFs using Gemini Multimodal / Structured Output to pre-populate the `MonthlyPayslip` record, using a stateless memory-only extraction flow.
3. **Seamless Client Verification Workflow**: Giving users instant visual feedback with pre-filled fields in the 3-tab `Record Monthly Payslip` modal for one-click verification and archive.

---

## 2. Cloud Storage (GCS) Directory Architecture

### 2.1 Storage Folder Hierarchy & Path Construction

The bucket objects follow a deterministic path pattern designed for **direct human browsing** in the Google Cloud Console / `gcloud storage` CLI, as well as programmatic retrieval:

**General Path Format:**
`career_vault/users/user_{id}/companies/{company_slug}/payslips/{YYYY}/{YYYY-MM}_{company_slug}_payslip.pdf`

Example:
`career_vault/users/user_1/companies/astellas-pharma/payslips/2025/2025-10_astellas-pharma_payslip.pdf`

### 2.2 GCS Object Metadata
Each uploaded object will attach custom GCS metadata for auditing and programmatic querying without hitting the database:
```json
{
  "user_id": "1",
  "company_slug": "astellas-pharma",
  "doc_type": "payslip",
  "year": "2025",
  "month": "10",
  "is_bonus": "false",
  "extracted_gross": "847664",
  "extracted_net": "678812"
}
```

---

## 3. Automated Extraction Engine (Stateless Flow)

We will use a **Stateless Extraction** approach to avoid orphaned files and maintain clean state management.

### 3.1 Extraction Pipeline Flow (`POST /api/career/payslips/extract/`)
1. The client uploads the PDF via a POST request.
2. The Django backend receives the file and holds it in memory.
3. The backend streams the file to the Gemini API (Flash 1.5/2.5) with a strict Pydantic JSON Schema (Structured Output) that maps directly to the `MonthlyPayslip` Django model.
4. The backend applies a deterministic validation layer (e.g., ensuring `base_salary + allowances = gross_pay`, and `gross_pay - deductions = net_pay`) to catch hallucinations.
5. The pre-filled JSON payload is returned to the client. No DB records or GCS uploads occur at this stage.

---

## 4. Client Review & Save Workflow

1. **Upload & Analyze**: User drops a PDF into the portal. A 1-2s spinner runs while `/api/career/payslips/extract/` is called.
2. **Review Modal**: The frontend receives the response and opens the 3-tab "Record Monthly Payslip" modal, pre-populating all extracted fields (Earnings, Deductions, Attendance).
3. **Save (`POST /api/career/payslips/save/`)**: The user reviews, makes any necessary corrections, and clicks "Save". The client sends both the verified JSON payload and the original PDF file to this endpoint.
4. **Final Commit**:
   - Django uploads the PDF to the designated GCS `career_vault/` path.
   - Django creates the `CareerDocument` DB record.
   - Django creates the `MonthlyPayslip` DB record (linked to the `CareerDocument` and `Employment`).

---

## 5. Security & Access Control

1. **Authentication**: All upload and extraction APIs require standard token/session authentication.
2. **Signed URLs for Viewing**: Documents in GCS remain strictly private. When the user wants to view a document in the portal, the frontend requests a short-lived Signed URL from the backend. This Signed URL is embedded in the UI (e.g., `<iframe>` or PDF viewer), allowing the user to seamlessly view the PDF without exposing the bucket to the public.
3. **Data Loss Prevention**: When deleting a `MonthlyPayslip`, the linked `CareerDocument` remains safely archived in the Document Vault unless explicitly purged by the user.
