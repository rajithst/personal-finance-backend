# Personal Information & Vault Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete, secure Personal Information & Vault subsystem featuring relational life entities (Identity & Civil, Education History, Vehicles & Mobility, Housing & Tenancy), user-isolated file storage with signed streaming, an automated Expiry Radar for time-sensitive renewals, and a responsive React frontend hub.

**Architecture:** A new Django app (`finance.personal_vault`) provides relational models, storage services, and REST APIs under `/api/v1/personal-vault/`. The React client (`personalfinance-web`) integrates a new top-level "Personal Hub" in `Sidebar.tsx` and `App.tsx` with dedicated sub-tabs, interactive modals, and an Expiry Radar.

**Tech Stack:** Django, Django REST Framework, PostgreSQL / SQLite (dev), Google Cloud Storage / Local Media, React 19, TypeScript, Lucide Icons, Vite.

**Spec:** [docs/superpowers/specs/2026-10-16-personal-vault-and-information-hub-design.md](file:///Users/rajith/Documents/Projects/PersonalFinance/PFServer/personalfinance/docs/superpowers/specs/2026-10-16-personal-vault-and-information-hub-design.md)

## Global Constraints

- Backend Django app path: `personalfinance/finance/personal_vault/`
- API prefix: `/api/v1/personal-vault/`
- User data isolation: All queries strictly scoped by `request.user`
- File upload limit: Maximum 25 MB
- Permitted MIME types: `application/pdf`, `image/jpeg`, `image/png`, `image/webp`
- Expiry severity thresholds: `expired` (<0 days), `critical` (0-30 days), `upcoming` (31-90 days), `healthy` (>90 days)
- Frontend styling: Vanilla CSS using design system tokens (`var(--...)`) matching CoinCraft theme conventions

## Review Focus

1. **Cross-Tenant IDOR on Documents**: Requesting another user's document ID returns `404 Not Found` (tested in Task 3).
2. **Disallowed File Uploads**: Uploading executable binaries or scripts returns `400 Bad Request` with an explicit MIME error (tested in Task 2).
3. **Missing File on Storage**: Accessing a document whose underlying physical file is missing returns a graceful `404` or fallback response without crashing (tested in Task 2 & Task 5).
4. **Invalid Date Sequences**: Submitting an education or lease record where `end_date < start_date` triggers a validation error (tested in Task 1 & Task 6).
5. **Radar Edge Dates**: Dates exactly on today (`days_remaining == 0`) are classified as `critical`, not `expired` or `upcoming` (tested in Task 2).

---

### Task 1: Backend Django App Setup, Models & Database Migrations

**Files:**
- Create: `personalfinance/finance/personal_vault/__init__.py`
- Create: `personalfinance/finance/personal_vault/apps.py`
- Create: `personalfinance/finance/personal_vault/models.py`
- Create: `personalfinance/finance/personal_vault/admin.py`
- Modify: `personalfinance/config/settings.py` (add `'finance.personal_vault'` to `INSTALLED_APPS`)
- Test: `personalfinance/finance/personal_vault/tests/test_models.py`

**Interfaces:**
- Produces: `PersonalDocument`, `IdentityProfile`, `EducationRecord`, `VehicleRecord`, `ResidenceRecord` Django models.

- [ ] **Step 1: Write failing model tests in `finance/personal_vault/tests/test_models.py`**

```python
import pytest
from datetime import date
from django.contrib.auth import get_user_model
from finance.personal_vault.models import (
    PersonalDocument,
    IdentityProfile,
    EducationRecord,
    VehicleRecord,
    ResidenceRecord,
)

User = get_user_model()

@pytest.mark.django_db
def test_create_identity_profile_and_documents():
    user = User.objects.create_user(username="vault_user", password="password123")
    profile = IdentityProfile.objects.create(
        user=user,
        full_legal_name="Jane Doe",
        nationality="Japanese",
        date_of_birth=date(1990, 5, 15)
    )
    assert str(profile) == "IdentityProfile(user=vault_user, name=Jane Doe)"

    doc = PersonalDocument.objects.create(
        user=user,
        title="Passport",
        category="identity",
        doc_type="passport",
        document_number="MZ123456",
        file_uri="local://personal_vault/users/user_1/passport.pdf",
        original_filename="passport.pdf"
    )
    assert doc.category == "identity"
    assert doc.user == user
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest finance/personal_vault/tests/test_models.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'finance.personal_vault'`

- [ ] **Step 3: Implement `apps.py`, `models.py`, register in `settings.py`, and run migrations**

Create `PersonalVaultConfig` in `apps.py`, implement `IdentityProfile`, `EducationRecord`, `VehicleRecord`, `ResidenceRecord`, and `PersonalDocument` in `models.py`, add `'finance.personal_vault'` to `INSTALLED_APPS` in `config/settings.py`, and run:
`python manage.py makemigrations personal_vault && python manage.py migrate`

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest finance/personal_vault/tests/test_models.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add finance/personal_vault config/settings.py
git commit -m "feat(personal_vault): add Django app, models, and migrations"
```

---

### Task 2: Backend Secure Storage Service & Expiry Radar Engine

**Files:**
- Create: `personalfinance/finance/personal_vault/services/storage_service.py`
- Create: `personalfinance/finance/personal_vault/services/expiry_service.py`
- Test: `personalfinance/finance/personal_vault/tests/test_storage_service.py`
- Test: `personalfinance/finance/personal_vault/tests/test_expiry_radar.py`

**Interfaces:**
- Consumes: Models from Task 1.
- Produces:
  - `upload_personal_document(file_obj, user_id, category, doc_type, original_filename) -> str` (URI)
  - `get_personal_document_preview_url(document, request) -> str`
  - `get_user_expiry_radar(user, reference_date=None) -> list[dict]`

- [ ] **Step 1: Write failing unit tests for storage service & expiry radar**

```python
# test_expiry_radar.py
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from finance.personal_vault.models import PersonalDocument, VehicleRecord, ResidenceRecord
from finance.personal_vault.services.expiry_service import get_user_expiry_radar

User = get_user_model()

def test_expiry_radar_classification(db):
    user = User.objects.create_user(username="test_radar_user")
    today = date(2026, 10, 16)
    
    # Critical: 10 days left
    PersonalDocument.objects.create(
        user=user, title="Passport", category="identity", doc_type="passport",
        expiry_date=today + timedelta(days=10), file_uri="local://test.pdf"
    )
    # Expired: 5 days ago
    VehicleRecord.objects.create(
        user=user, make="Toyota", model="Aqua", license_plate="12-34",
        status="active", shaken_expiry_date=today - timedelta(days=5)
    )
    # Upcoming: 45 days left
    ResidenceRecord.objects.create(
        user=user, property_name="Apt 101", address_full="Tokyo",
        status="current", move_in_date=today - timedelta(days=300),
        lease_end_date=today + timedelta(days=45)
    )

    radar = get_user_expiry_radar(user, reference_date=today)
    assert len(radar) == 3
    assert radar[0]["severity"] == "expired"
    assert radar[1]["severity"] == "critical"
    assert radar[2]["severity"] == "upcoming"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest finance/personal_vault/tests/test_expiry_radar.py`
Expected: FAIL with `ImportError: cannot import name 'get_user_expiry_radar'`

- [ ] **Step 3: Implement `storage_service.py` and `expiry_service.py`**

- `storage_service.py`: Validate file size (<= 25MB), inspect MIME type against whitelist (`application/pdf`, `image/jpeg`, `image/png`, `image/webp`), sanitize filename, write to local media or GCS path `personal_vault/users/user_{user_id}/{category}/...`, generate signed preview/download tokens via `TimestampSigner`.
- `expiry_service.py`: Query active documents, vehicles, and current residences with non-null expiry dates, calculate `days_remaining = (expiry_date - ref_date).days`, assign severity (`expired`, `critical`, `upcoming`, `healthy`), and sort chronologically.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest finance/personal_vault/tests/test_storage_service.py finance/personal_vault/tests/test_expiry_radar.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add finance/personal_vault/services finance/personal_vault/tests
git commit -m "feat(personal_vault): add storage service and expiry radar engine"
```

---

### Task 3: Backend REST Serializers, Views, URLs & Security Tests

**Files:**
- Create: `personalfinance/finance/personal_vault/serializers.py`
- Create: `personalfinance/finance/personal_vault/views.py`
- Create: `personalfinance/finance/personal_vault/urls.py`
- Modify: `personalfinance/core/urls.py` (include `finance.personal_vault.urls` at `api/v1/personal-vault/`)
- Test: `personalfinance/finance/personal_vault/tests/test_views.py`
- Test: `personalfinance/finance/personal_vault/tests/test_security.py`

**Interfaces:**
- Produces: REST endpoints for `/overview/`, `/identity/`, `/education/`, `/vehicles/`, `/residences/`, `/documents/`, `/documents/upload/`, `/documents/<id>/view/`, `/documents/<id>/download/`.

- [ ] **Step 1: Write failing security & API view tests**

```python
# test_security.py
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from finance.personal_vault.models import PersonalDocument

User = get_user_model()

@pytest.mark.django_db
def test_cross_user_document_isolation():
    user1 = User.objects.create_user(username="alice", password="password")
    user2 = User.objects.create_user(username="bob", password="password")
    doc = PersonalDocument.objects.create(
        user=user1, title="Alice Passport", category="identity",
        doc_type="passport", file_uri="local://test.pdf"
    )

    client = APIClient()
    client.force_authenticate(user=user2)
    response = client.get(f"/api/v1/personal-vault/documents/{doc.id}/")
    assert response.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest finance/personal_vault/tests/test_security.py`
Expected: FAIL with 404 or connection error (URL not wired yet)

- [ ] **Step 3: Implement serializers, viewsets, and route wiring**

Implement DRF ModelSerializers with validation, ModelViewSets with `permission_classes=[IsAuthenticated]`, `PersonalDocumentUploadView` (multipart parser), `PersonalVaultOverviewView` (KPI counts + expiry radar + recent uploads), and register URLs in `core/urls.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest finance/personal_vault/tests/test_views.py finance/personal_vault/tests/test_security.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add finance/personal_vault/ core/urls.py
git commit -m "feat(personal_vault): add REST endpoints, serializers, and security tests"
```

---

### Task 4: Frontend TypeScript Types & Resilient API/Mock Service Layer

**Files:**
- Create: `personalfinance-web/src/types/personalVault.ts`
- Create: `personalfinance-web/src/services/personalVaultService.ts`
- Test: Build verification (`npm run build` or vitest)

**Interfaces:**
- Produces:
  - Types: `PersonalDocument`, `IdentityProfile`, `EducationRecord`, `VehicleRecord`, `ResidenceRecord`, `ExpiryRadarItem`, `PersonalOverviewData`.
  - Service: `personalVaultService` (`getOverview`, `getIdentity`, `updateIdentity`, `getEducation`, `createEducation`, `updateEducation`, `deleteEducation`, `getVehicles`, `createVehicle`, `updateVehicle`, `deleteVehicle`, `getResidences`, `createResidence`, `updateResidence`, `deleteResidence`, `getDocuments`, `uploadDocument`, `deleteDocument`).

- [ ] **Step 1: Define TypeScript interfaces in `src/types/personalVault.ts`**

Define strong interfaces matching the backend schema and JSON responses.

- [ ] **Step 2: Implement `personalVaultService.ts` with live API + fallback mock data**

Create `personalVaultService` with Axios/fetch methods targeting `/api/v1/personal-vault/`, handling auth headers, plus comprehensive default mock datasets for offline/dev operation.

- [ ] **Step 3: Run TypeScript typecheck to verify types**

Run: `npm run build` in `personalfinance-web`
Expected: PASS with 0 errors.

- [ ] **Step 4: Commit**

```bash
git add src/types/personalVault.ts src/services/personalVaultService.ts
git commit -m "feat(personal-web): add TypeScript definitions and personalVaultService"
```

---

### Task 5: Frontend Document Viewer & Upload Modals with Entity Linking

**Files:**
- Create: `personalfinance-web/src/components/personal/modals/DocumentViewerModal.tsx`
- Create: `personalfinance-web/src/components/personal/modals/DocumentUploadModal.tsx`
- Create: `personalfinance-web/src/components/personal/modals/EducationRecordModal.tsx`
- Create: `personalfinance-web/src/components/personal/modals/VehicleRecordModal.tsx`
- Create: `personalfinance-web/src/components/personal/modals/ResidenceRecordModal.tsx`
- Create: `personalfinance-web/src/components/personal/modals/IdentityProfileModal.tsx`

**Interfaces:**
- Consumes: Types and `personalVaultService` from Task 4.
- Produces: Self-contained modal dialogs with form validation, drag-and-drop file upload, and document preview (PDF and images).

- [ ] **Step 1: Implement `DocumentViewerModal.tsx`**

Build modal supporting full-screen preview, zoom, pagination fallback for PDFs, and direct authenticated download.

- [ ] **Step 2: Implement `DocumentUploadModal.tsx` with contextual entity linking**

Support drag-and-drop file select, category chips, document type selection, and dynamic entity linking dropdowns (e.g. choose specific vehicle when category is 'vehicle').

- [ ] **Step 3: Implement Entity Modals**

Build `EducationRecordModal`, `VehicleRecordModal`, `ResidenceRecordModal`, and `IdentityProfileModal` with clear field labels, validation, and theme styling.

- [ ] **Step 4: Verify TypeScript build**

Run: `npm run build` in `personalfinance-web`
Expected: PASS with 0 errors.

- [ ] **Step 5: Commit**

```bash
git add src/components/personal/modals/
git commit -m "feat(personal-web): implement document viewer, uploader, and entity modals"
```

---

### Task 6: Frontend Domain Sub-Views (Identity, Education, Vehicles, Housing, & Document Vault)

**Files:**
- Create: `personalfinance-web/src/components/personal/IdentitySection.tsx`
- Create: `personalfinance-web/src/components/personal/EducationTimelineSection.tsx`
- Create: `personalfinance-web/src/components/personal/VehiclesSection.tsx`
- Create: `personalfinance-web/src/components/personal/HousingSection.tsx`
- Create: `personalfinance-web/src/components/personal/PersonalVaultDeck.tsx`

**Interfaces:**
- Consumes: Modals from Task 5, Types and Service from Task 4.
- Produces: Rich sub-view components for each life domain.

- [ ] **Step 1: Implement `IdentitySection.tsx`**

Render civil status card, emergency contacts, and verified document cards (Passport, NIC, Birth Certificate, Driving License, Residence Card).

- [ ] **Step 2: Implement `EducationTimelineSection.tsx`**

Render interactive vertical chronological timeline with institution cards, GPA badges, degree certificates, and "Add Degree" action.

- [ ] **Step 3: Implement `VehiclesSection.tsx`**

Render vehicle grid with shaken expiration countdown badges, insurance dates, license plates, and attached maintenance/inspection files.

- [ ] **Step 4: Implement `HousingSection.tsx`**

Render current residence banner with lease end countdown, landlord contact, deposit/rent details, and past rental history accordion.

- [ ] **Step 5: Implement `PersonalVaultDeck.tsx`**

Render centralized file explorer with search input, category filters (All, Identity, Education, Vehicles, Housing), table/grid toggle, and preview/download actions.

- [ ] **Step 6: Verify build**

Run: `npm run build` in `personalfinance-web`
Expected: PASS with 0 errors.

- [ ] **Step 7: Commit**

```bash
git add src/components/personal/
git commit -m "feat(personal-web): implement domain sub-views for personal hub"
```

---

### Task 7: Frontend Personal Overview Deck with Expiry Radar & Navigation Wiring

**Files:**
- Create: `personalfinance-web/src/components/personal/PersonalOverviewDeck.tsx`
- Create: `personalfinance-web/src/components/personal/PersonalHubView.tsx`
- Modify: `personalfinance-web/src/components/layout/Sidebar.tsx` (add Personal Hub nav item + 6 sub-items)
- Modify: `personalfinance-web/src/App.tsx` (wire `personal` route, state, and rendering)

**Interfaces:**
- Consumes: All sub-views from Task 6, modals from Task 5, and service from Task 4.
- Produces: Complete end-to-end integrated Personal Hub experience in the web application.

- [ ] **Step 1: Implement `PersonalOverviewDeck.tsx` with Expiry Radar**

Build 4 KPI summary cards (Total Docs, Active Vehicles, Active Leases, Expiring Soon) and the interactive Expiry Radar list with severity badges (Red/Orange/Yellow/Green) and click-to-navigate action.

- [ ] **Step 2: Implement `PersonalHubView.tsx` orchestrator**

Build main view container managing active sub-tab state (`overview`, `identity`, `education`, `vehicles`, `housing`, `vault`), data fetching from `personalVaultService`, and modals.

- [ ] **Step 3: Integrate into `Sidebar.tsx` and `App.tsx`**

Add "Personal Hub" navigation item with `ShieldCheck` icon, collapsible sub-menu, and wire up `currentTab === "personal"` rendering in `App.tsx`.

- [ ] **Step 4: Verify end-to-end frontend build**

Run: `npm run build` in `personalfinance-web`
Expected: PASS with 0 errors.

- [ ] **Step 5: Commit**

```bash
git add src/components/personal/ src/components/layout/Sidebar.tsx src/App.tsx
git commit -m "feat(personal-web): integrate PersonalHubView and Expiry Radar into main app"
```
