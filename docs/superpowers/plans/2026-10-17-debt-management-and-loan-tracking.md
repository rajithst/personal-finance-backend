# Debt Management & Loan Tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a comprehensive Debt Management & Loan Tracking subsystem that models installment loans (standard and balloon / residual value financing), materializes exact payment schedules, and automatically scores and links imported bank transactions to installments.

**Architecture:** A new Django app `finance/debts` exposes REST endpoints and calculation services for schedule amortization and transaction matching without touching the core `Transaction` model. The React frontend (`personalfinance-web`) adds a dedicated top-level Debts view, amortization schedule data table, transaction confirmation flow, dashboard KPI widget, and cross-links from Personal Hub vehicle cards.

**Tech Stack:** Python 3.12, Django 5.2, Django REST Framework, pytest-django, React 19, TypeScript, Vite.

**Spec:** [`docs/superpowers/specs/2026-10-17-debt-management-and-loan-tracking-design.md`](file:///Users/rajith/Documents/Projects/PersonalFinance/PFServer/personalfinance/docs/superpowers/specs/2026-10-17-debt-management-and-loan-tracking-design.md)

## Global Constraints
- Core `Transaction` records remain regular expenses; no fields or logic in `finance/transactions/models.py` are altered.
- Links between `DebtInstallment` and `Transaction` are 1-to-1 (`SET_NULL` on transaction deletion).
- Unicode NFKC normalization is strictly enforced for transaction payee and alias matching to handle Japanese full-width and half-width character equivalence.
- Frontend tables must use `.table-container` and `.data-table` classes matching the application design system.
- Zero monetary figures or customer names from user contracts are hardcoded into production code or test fixtures.

## Review Focus
1. **Irregular First Installment:** An initial payment amount differing from regular recurring payments is amortized accurately without distorting subsequent balances.
2. **Balloon / Residual Value Maturity:** Loans with a deferred residual balloon payment properly amortize monthly payments and settle the final balloon at term end.
3. **Early Settlement / Dealer Trade-In:** When a debt is closed before maturity, future unbilled installments transition to `is_settled_early = True` and do not appear as missed payments.
4. **Bank Holiday Date Shifts:** Transactions matching ±5 calendar days around the scheduled due date are recognized and scored by the matching engine.
5. **Cascade Safety on Transaction Deletion:** Deleting a transaction safely resets the linked installment back to unlinked state without corrupting the debt schedule.

---

### Task 1: Django App Setup & Data Models

**Files:**
- Create: `finance/debts/__init__.py`
- Create: `finance/debts/apps.py`
- Create: `finance/debts/models.py`
- Create: `finance/debts/admin.py`
- Create: `finance/debts/tests/__init__.py`
- Create: `finance/debts/tests/test_models.py`
- Modify: `core/settings.py`

**Interfaces:**
- Consumes: `settings.AUTH_USER_MODEL`, `finance.transactions.models.Transaction`, `finance.personal_vault.models.VehicleRecord`, `finance.personal_vault.models.ResidenceRecord`, `finance.personal_vault.models.PersonalDocument`
- Produces: `Debt`, `DebtInstallment` models

- [ ] **Step 1: Write the failing model tests**

```python
# finance/debts/tests/test_models.py
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from finance.debts.models import Debt, DebtInstallment

User = get_user_model()

@pytest.mark.django_db
def test_create_debt_model():
    user = User.objects.create_user(username="debt_tester", email="debt@example.com")
    debt = Debt.objects.create(
        user=user,
        name="Auto Loan Alpha",
        debt_type="auto_loan",
        lender="Financier Alpha",
        principal_amount=Decimal("2000000.00"),
        term_months=36,
        payment_day=26,
        first_payment_date="2025-01-26",
        regular_payment_amount=Decimal("60000.00"),
        annual_rate=Decimal("5.000"),
    )
    assert debt.id is not None
    assert debt.status == "active"
    assert str(debt) == "Auto Loan Alpha (Financier Alpha)"

@pytest.mark.django_db
def test_create_debt_installment_relationship():
    user = User.objects.create_user(username="inst_tester", email="inst@example.com")
    debt = Debt.objects.create(
        user=user,
        name="Test Debt",
        principal_amount=Decimal("100000.00"),
        term_months=12,
        payment_day=10,
        first_payment_date="2025-01-10",
        regular_payment_amount=Decimal("10000.00"),
    )
    inst = DebtInstallment.objects.create(
        debt=debt,
        sequence=1,
        kind="installment",
        due_date="2025-01-10",
        amount=Decimal("10000.00"),
        principal=Decimal("9500.00"),
        interest=Decimal("500.00"),
        balance_after=Decimal("90500.00"),
    )
    assert inst.id is not None
    assert inst.status == "upcoming"
    assert debt.installments.count() == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest finance/debts/tests/test_models.py -v`
Expected: FAIL (ModuleNotFoundError / No module named 'finance.debts')

- [ ] **Step 3: Implement `Debt` and `DebtInstallment` models and register app**

Create `finance/debts/apps.py`, create `finance/debts/models.py` with all fields specified in spec section 3. Add `'finance.debts'` to `INSTALLED_APPS` in `core/settings.py`. Register models in `finance/debts/admin.py`. Generate migrations via `.venv/bin/python manage.py makemigrations debts`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python manage.py migrate debts && .venv/bin/python -m pytest finance/debts/tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/settings.py finance/debts/
git commit -m "feat(debts): create debts app, models, and migrations"
```

---

### Task 2: Schedule Generator & Amortization Calculator Engine

**Files:**
- Create: `finance/debts/services/__init__.py`
- Create: `finance/debts/services/debt_calculator.py`
- Create: `finance/debts/tests/test_calculator.py`

**Interfaces:**
- Consumes: `Debt`, `DebtInstallment`
- Produces: `generate_installment_schedule(debt: Debt) -> list[DebtInstallment]`, `solve_annual_rate(principal, term, regular_payment, first_payment, balloon) -> Decimal`, `compute_early_settlement(debt: Debt, closed_date, payoff_amount) -> dict`

- [ ] **Step 1: Write the failing calculator tests**

```python
# finance/debts/tests/test_calculator.py
import pytest
from decimal import Decimal
from datetime import date
from django.contrib.auth import get_user_model
from finance.debts.models import Debt
from finance.debts.services.debt_calculator import (
    generate_installment_schedule,
    solve_annual_rate,
)

User = get_user_model()

@pytest.mark.django_db
def test_solve_annual_rate():
    # Principal 1,000,000, 12 months, 85,607/mo ~= 5.0% APR
    rate = solve_annual_rate(
        principal=Decimal("1000000.00"),
        term_months=12,
        regular_payment=Decimal("85607.00"),
        first_payment=None,
        balloon=Decimal("0.00"),
    )
    assert Decimal("4.8") < rate < Decimal("5.2")

@pytest.mark.django_db
def test_generate_standard_schedule():
    user = User.objects.create_user(username="calc_tester", email="calc@example.com")
    debt = Debt.objects.create(
        user=user,
        name="Standard Loan",
        principal_amount=Decimal("120000.00"),
        term_months=12,
        payment_day=26,
        first_payment_date=date(2025, 2, 26),
        regular_payment_amount=Decimal("10500.00"),
        finance_charge=Decimal("6000.00"),
        annual_rate=Decimal("5.000"),
    )
    installments = generate_installment_schedule(debt)
    assert len(installments) == 12
    assert installments[0].sequence == 1
    assert installments[0].due_date == date(2025, 2, 26)
    assert installments[-1].sequence == 12
    assert installments[-1].balance_after == Decimal("0.00")

@pytest.mark.django_db
def test_generate_balloon_schedule():
    user = User.objects.create_user(username="balloon_tester", email="balloon@example.com")
    debt = Debt.objects.create(
        user=user,
        name="Balloon Loan",
        principal_amount=Decimal("2000000.00"),
        balloon_amount=Decimal("1400000.00"),
        term_months=24,
        payment_day=27,
        first_payment_date=date(2024, 1, 27),
        regular_payment_amount=Decimal("33000.00"),
        annual_rate=Decimal("4.000"),
    )
    installments = generate_installment_schedule(debt)
    assert len(installments) == 24
    assert installments[-1].kind == "balloon"
    assert installments[-1].balance_after == Decimal("0.00")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest finance/debts/tests/test_calculator.py -v`
Expected: FAIL (ImportError: cannot import name 'generate_installment_schedule')

- [ ] **Step 3: Implement `debt_calculator.py`**

Implement `solve_annual_rate`, `generate_installment_schedule`, and `compute_early_settlement` handling down payments (row #0), irregular first payments, interest amortization, exact final rounding adjustment to zero balance, and balloon payment flags.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest finance/debts/tests/test_calculator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add finance/debts/services/ finance/debts/tests/test_calculator.py
git commit -m "feat(debts): implement schedule generator and amortization calculator"
```

---

### Task 3: Intelligent Transaction Matching Engine

**Files:**
- Create: `finance/debts/services/debt_matcher.py`
- Create: `finance/debts/tests/test_matcher.py`

**Interfaces:**
- Consumes: `Debt`, `DebtInstallment`, `Transaction`
- Produces: `find_transaction_suggestions(debt: Debt) -> list[dict]`, `link_transaction_to_installment(installment: DebtInstallment, transaction: Transaction, link_source='suggested') -> DebtInstallment`

- [ ] **Step 1: Write the failing matcher tests**

```python
# finance/debts/tests/test_matcher.py
import pytest
from decimal import Decimal
from datetime import date
from django.contrib.auth import get_user_model
from finance.debts.models import Debt, DebtInstallment
from finance.transactions.models import Transaction
from finance.debts.services.debt_matcher import find_transaction_suggestions, link_transaction_to_installment

User = get_user_model()

@pytest.mark.django_db
def test_match_fullwidth_japanese_payee_and_amount():
    user = User.objects.create_user(username="match_tester", email="match@example.com")
    debt = Debt.objects.create(
        user=user,
        name="Auto Loan",
        principal_amount=Decimal("500000.00"),
        term_months=10,
        payment_day=26,
        first_payment_date=date(2025, 2, 26),
        regular_payment_amount=Decimal("50000.00"),
        match_payee="AUTO LOAN",
        match_day_window=5,
    )
    inst = DebtInstallment.objects.create(
        debt=debt,
        sequence=1,
        due_date=date(2025, 2, 26),
        amount=Decimal("50000.00"),
        principal=Decimal("45000.00"),
        interest=Decimal("5000.00"),
        balance_after=Decimal("455000.00"),
    )
    # Bank imported with full-width text and weekend delay (28th instead of 26th)
    tx = Transaction.objects.create(
        user=user,
        date=date(2025, 2, 28),
        destination="ＡＵＴＯ　ＬＯＡＮ　ＫＫ",
        amount=Decimal("-50000.00"),
        is_expense=True,
    )
    suggestions = find_transaction_suggestions(debt)
    assert len(suggestions) == 1
    assert suggestions[0]["installment"].id == inst.id
    assert suggestions[0]["transaction"].id == tx.id

    link_transaction_to_installment(inst, tx)
    inst.refresh_from_db()
    assert inst.transaction_id == tx.id
    assert inst.status == "paid"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest finance/debts/tests/test_matcher.py -v`
Expected: FAIL (ImportError: cannot import name 'find_transaction_suggestions')

- [ ] **Step 3: Implement `debt_matcher.py`**

Implement Unicode NFKC normalization, amount tolerance evaluation, date window filtering, unlinked candidate exclusion, and assignment linking.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest finance/debts/tests/test_matcher.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add finance/debts/services/debt_matcher.py finance/debts/tests/test_matcher.py
git commit -m "feat(debts): implement intelligent transaction matching and linking engine"
```

---

### Task 4: Serializers, Views, and REST Endpoints

**Files:**
- Create: `finance/debts/serializers.py`
- Create: `finance/debts/views.py`
- Create: `finance/debts/urls.py`
- Create: `finance/debts/tests/test_views.py`
- Modify: `core/urls.py`

**Interfaces:**
- Consumes: `Debt`, `DebtInstallment`, `debt_calculator`, `debt_matcher`
- Produces: REST API endpoints under `/api/debts/`

- [ ] **Step 1: Write the failing API view tests**

```python
# finance/debts/tests/test_views.py
import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from finance.debts.models import Debt

User = get_user_model()

@pytest.mark.django_db
def test_create_debt_api_generates_schedule():
    user = User.objects.create_user(username="api_user", password="password123")
    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "name": "API Auto Loan",
        "debt_type": "auto_loan",
        "lender": "Test Lender",
        "principal_amount": "600000.00",
        "term_months": 12,
        "payment_day": 26,
        "first_payment_date": "2025-03-26",
        "regular_payment_amount": "52000.00",
        "annual_rate": "5.500",
    }
    response = client.post("/api/debts/", payload, format="json")
    assert response.status_code == 201
    debt_id = response.data["id"]
    debt = Debt.objects.get(id=debt_id)
    assert debt.installments.count() == 12

@pytest.mark.django_db
def test_debt_schedule_endpoint():
    user = User.objects.create_user(username="sched_user", password="password123")
    client = APIClient()
    client.force_authenticate(user=user)
    debt = Debt.objects.create(
        user=user,
        name="Quick Debt",
        principal_amount=Decimal("100000.00"),
        term_months=2,
        payment_day=10,
        first_payment_date="2025-01-10",
        regular_payment_amount=Decimal("50500.00"),
    )
    from finance.debts.services.debt_calculator import generate_installment_schedule
    generate_installment_schedule(debt)

    response = client.get(f"/api/debts/{debt.id}/schedule/")
    assert response.status_code == 200
    assert len(response.data) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest finance/debts/tests/test_views.py -v`
Expected: FAIL (404 Not Found on `/api/debts/`)

- [ ] **Step 3: Implement Serializers, ViewSets, and route registration**

Create `DebtSerializer`, `DebtInstallmentSerializer`, `DebtDetailSerializer`, implement `DebtViewSet` with custom actions (`schedule`, `suggestions`, `confirm_link`, `unlink`, `close`, `summary`), wire URLs to `core/urls.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest finance/debts/tests/test_views.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/urls.py finance/debts/serializers.py finance/debts/views.py finance/debts/urls.py finance/debts/tests/test_views.py
git commit -m "feat(debts): add REST endpoints for debts, schedules, and linking"
```

---

### Task 5: Frontend API Client & TypeScript Types

**Files:**
- Create: `personalfinance-web/src/types/debts.ts`
- Create: `personalfinance-web/src/services/debtService.ts`

**Interfaces:**
- Consumes: Backend `/api/debts/` endpoints, `src/services/api.ts`
- Produces: `Debt`, `DebtInstallment`, `DebtSummary`, `TransactionSuggestion` TypeScript interfaces and `debtService` methods.

- [ ] **Step 1: Define TypeScript models in `src/types/debts.ts`**

Define `Debt`, `DebtInstallment`, `DebtSummary`, `TransactionSuggestion`, `CreateDebtPayload`.

- [ ] **Step 2: Implement API service methods in `src/services/debtService.ts`**

Implement `getDebts()`, `getDebt(id)`, `getSchedule(id)`, `getSuggestions(id)`, `confirmLink(debtId, installmentId, transactionId)`, `unlink(debtId, installmentId)`, `closeDebt(id, payload)`, `getSummary()`.

- [ ] **Step 3: Verify TypeScript compilation**

Run: `cd personalfinance-web && npm run build`
Expected: PASS (0 type errors)

- [ ] **Step 4: Commit**

```bash
git add src/types/debts.ts src/services/debtService.ts
git commit -m "feat(debts): add TypeScript types and debtService client"
```

---

### Task 6: Frontend Debts Dashboard & Loan Cards View

**Files:**
- Create: `personalfinance-web/src/components/debts/DebtsView.tsx`
- Create: `personalfinance-web/src/components/debts/DebtCard.tsx`

**Interfaces:**
- Consumes: `debtService`, `src/types/debts.ts`
- Produces: Primary Debts view with top metrics (Total Outstanding, Monthly Commitments, Lifetime Cost), filter tabs (`Active`, `Paid Off`, `All`), and responsive loan cards deck.

- [ ] **Step 1: Implement `DebtCard.tsx`**

Build loan card component featuring progress bar, monthly commitment pill, lender/vendor tags, balloon indicator, pending suggestion badge, and action triggers.

- [ ] **Step 2: Implement `DebtsView.tsx`**

Build page container with summary ribbon metrics, empty state, and grid of `DebtCard` items with modal trigger states.

- [ ] **Step 3: Verify TypeScript build**

Run: `npm run build`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/components/debts/DebtCard.tsx src/components/debts/DebtsView.tsx
git commit -m "feat(debts): create DebtsView and DebtCard components"
```

---

### Task 7: Frontend Amortization Schedule Table & Auto-Match Confirmation Modal

**Files:**
- Create: `personalfinance-web/src/components/debts/DebtDetailModal.tsx`
- Create: `personalfinance-web/src/components/debts/AmortizationTable.tsx`
- Create: `personalfinance-web/src/components/debts/SuggestionConfirmBanner.tsx`

**Interfaces:**
- Consumes: `Debt`, `DebtInstallment`, `debtService`
- Produces: Detailed loan inspector modal with financial breakdown header, balance trajectory chart, auto-match suggestion ribbon, and standard `.data-table` schedule.

- [ ] **Step 1: Implement `AmortizationTable.tsx`**

Render table using `.table-container` and `.data-table` with columns `#`, `Due Date`, `Payment Amount`, `Principal`, `Interest`, `Remaining Balance`, `Status` (Paid, Upcoming, Settled Early, Missed), and inline action buttons.

- [ ] **Step 2: Implement `SuggestionConfirmBanner.tsx`**

Render pending candidates ribbon with one-click confirm, match scoring details, and batch confirm.

- [ ] **Step 3: Implement `DebtDetailModal.tsx`**

Combine financial summary banner, suggestion ribbon, balance-over-time visual chart, and amortization table with interactive linking/unlinking handlers.

- [ ] **Step 4: Verify TypeScript build**

Run: `npm run build`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/components/debts/AmortizationTable.tsx src/components/debts/SuggestionConfirmBanner.tsx src/components/debts/DebtDetailModal.tsx
git commit -m "feat(debts): create amortization schedule table and suggestion confirmation modal"
```

---

### Task 8: Frontend Add/Edit Debt Modal

**Files:**
- Create: `personalfinance-web/src/components/debts/DebtModal.tsx`

**Interfaces:**
- Consumes: `debtService`, `personalVaultService` (for vehicle/residence asset selection)
- Produces: Full create/edit modal with contract terms, balloon toggles, trade-in rollover linking, and payee auto-match keyword configuration.

- [ ] **Step 1: Implement form state and inputs in `DebtModal.tsx`**

Build inputs for identity, terms, balloon amounts, down payments, trade-in credits, and asset foreign key selectors.

- [ ] **Step 2: Wire submission to `debtService.createDebt` / `updateDebt`**

Handle auto-generation on create, refresh parent state upon success.

- [ ] **Step 3: Verify TypeScript build**

Run: `npm run build`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/components/debts/DebtModal.tsx
git commit -m "feat(debts): create DebtModal for creating and updating loan contracts"
```

---

### Task 9: Cross-Integration (Sidebar, Dashboard, Personal Hub)

**Files:**
- Modify: `personalfinance-web/src/App.tsx`
- Modify: `personalfinance-web/src/components/layout/Sidebar.tsx`
- Modify: `personalfinance-web/src/components/dashboard/Dashboard.tsx` (or top analytics KPI)
- Modify: `personalfinance-web/src/components/personal/VehiclesSection.tsx`

**Interfaces:**
- Consumes: `debtService.getSummary()`, `DebtsView`
- Produces: Integrated sidebar navigation entry, dashboard debt liability widget, and vehicle financing status chips.

- [ ] **Step 1: Add Debts route and sidebar item**

Add `'debts'` view state in `App.tsx` and render `DebtsView`. Add `'Debts & Loans'` item with `Landmark` icon to `Sidebar.tsx`.

- [ ] **Step 2: Add Debt summary card to dashboard**

Display total debt balance, monthly outflow commitment, and debt-free target date on the main dashboard view.

- [ ] **Step 3: Add financing badges to `VehiclesSection.tsx`**

Render interactive link chips on vehicle cards that navigate directly to the corresponding debt record.

- [ ] **Step 4: Verify TypeScript build**

Run: `npm run build`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/App.tsx src/components/layout/Sidebar.tsx src/components/dashboard/Dashboard.tsx src/components/personal/VehiclesSection.tsx
git commit -m "feat(debts): integrate sidebar navigation, dashboard KPI widget, and vehicle cross-links"
```

---

### Task 10: End-to-End Verification & Full Test Suite

**Files:**
- Test: All backend tests (`finance/debts/tests/`)
- Test: Frontend build (`npm run build`)

- [ ] **Step 1: Run complete backend test suite**

Run: `.venv/bin/python -m pytest finance/debts/tests/ -v`
Expected: ALL PASS

- [ ] **Step 2: Run all project backend tests**

Run: `.venv/bin/python -m pytest finance/ -v`
Expected: ALL PASS with no regressions across transactions, payees, categories, career, or personal_vault.

- [ ] **Step 3: Run frontend production build**

Run: `cd personalfinance-web && npm run build`
Expected: Clean build with 0 errors.

- [ ] **Step 4: Commit and finalize**

```bash
git commit -m "chore(debts): verify test suite and production build"
```
