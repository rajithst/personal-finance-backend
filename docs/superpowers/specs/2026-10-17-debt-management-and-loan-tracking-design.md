# Design Specification: Debt Management & Loan Tracking (Debts Subsystem)

**Date:** 2026-10-17  
**Status:** Approved for Implementation  
**System Area:** Full-Stack (`finance/debts` Django backend + `personalfinance-web` React frontend)

---

## 1. Overview & Problem Statement

Users currently manage vehicle purchases, loan repayments, and monthly debt services as generic, undifferentiated expense transactions (e.g. debit entries for car financing or installment credit). While this records cash outflows, it provides no visibility into:
1. **Outstanding Principal & Amortization:** How much principal remains vs. total original borrowing.
2. **True Cost of Borrowing:** Breakdown of monthly installments into finance interest charges (分割払手数料) vs. principal reduction.
3. **Japanese Auto Loan Financing Realities:**
   - **Balloon / Residual Value Loans (据置型ローン / バリューローン / 残価設定型クレジット):** Fixed lower monthly payments paired with a large deferred residual balloon payment at the end of the term.
   - **Trade-In Loan Rollovers (下取り残債処理):** When an existing financed vehicle is traded in, the dealership pays off the remaining loan balance directly on behalf of the customer, and the new contract offsets or rolls that payoff amount into the new purchase.
4. **Automated Linking to Imported Bank Transactions:** Eliminating manual double-entry by automatically detecting, scoring, and suggesting matching bank outflows for each scheduled installment.

---

## 2. Core Architecture & Design Decisions

### A. Non-Disruptive Transaction Treatment (Expense Consistency)
- Monthly loan payment transactions **remain classified as regular expenses** in the core `Transaction` model.
- Dashboards, audit reports, category spend charts, and tax summaries continue working identically with zero disruption or retroactive modifications to existing expense reporting.
- The `debts` subsystem acts as an analytical overlay that links to existing transactions without modifying the `Transaction` table schema.

### B. Materialized Schedule Architecture (Approach A)
- Upon creation or modification of a debt contract, an exact payment schedule is generated as individual `DebtInstallment` records.
- Accommodates irregular first payments, balloon maturities, fee adjustments, and dealer trade-in early settlements.
- Links between installments and transactions are strictly 1-to-1 (`SET_NULL` on transaction deletion).

---

## 3. Data Models (`finance/debts/models.py`)

### 3.1 `Debt`
Represents a loan, financing agreement, or liability.

| Field Name | Type | Description |
|---|---|---|
| `id` | `BigAutoField` | Primary key |
| `user` | `ForeignKey(User)` | Owner of the debt record |
| `name` | `CharField(128)` | User-defined label for the debt |
| `debt_type` | `CharField(32)` | Choices: `auto_loan`, `home_loan`, `education_loan`, `personal_loan`, `other` |
| `lender` | `CharField(128)` | Creditor / financing institution name |
| `vendor` | `CharField(128)` | Selling dealership or merchant name |
| `status` | `CharField(32)` | Choices: `active`, `paid_off`, `closed_early` (default: `active`) |
| **Contract Terms** | | |
| `contract_date` | `DateField` | Execution date of financing agreement |
| `principal_amount` | `DecimalField(12,2)` | Total principal amount financed under the contract |
| `finance_charge` | `DecimalField(12,2)` | Total installment finance interest charges |
| `term_months` | `PositiveSmallIntegerField` | Total number of monthly payment terms |
| `payment_day` | `PositiveSmallIntegerField` | Calendar day of month installments are debited |
| `first_payment_date` | `DateField` | Due date of the initial payment |
| `first_payment_amount` | `DecimalField(12,2)` | Amount of initial payment if irregular |
| `regular_payment_amount` | `DecimalField(12,2)` | Standard recurring monthly installment amount |
| `annual_rate` | `DecimalField(5,3)` | Annual percentage rate (APR) |
| `rate_is_manual` | `BooleanField` | True if explicitly overridden, False if derived |
| **Balloon / Residual Value Terms** | | |
| `balloon_amount` | `DecimalField(12,2)` | Deferred residual balance payable at final maturity (0 if standard loan) |
| `balloon_due_date` | `DateField(null=True)` | Due date of final residual balloon payment |
| **Upfront Economics (Non-Financed)** | | |
| `cash_price` | `DecimalField(12,2)` | Total purchase price before deductions or credits |
| `down_payment_cash` | `DecimalField(12,2)` | Cash amount paid upfront |
| `trade_in_amount` | `DecimalField(12,2)` | Appraised trade-in allowance credited by dealership |
| `rolled_over_amount` | `DecimalField(12,2)` | Prior loan balance assumed and settled under contract |
| **Early Closure / Settlement** | | |
| `closed_date` | `DateField(null=True)` | Date debt was formally closed or settled |
| `closure_type` | `CharField(32)` | Choices: `natural_maturity`, `trade_in_payoff`, `refinanced`, `lump_sum` |
| `payoff_amount` | `DecimalField(12,2)` | Final settlement amount paid |
| **Auto-Matching Configuration** | | |
| `match_payee` | `CharField(128)` | Keyword pattern to match against transaction payee or alias |
| `match_amount_tolerance` | `DecimalField(8,2)` | Permitted amount deviation in currency units (default: 0) |
| `match_day_window` | `PositiveSmallIntegerField` | Permitted day deviation around scheduled date (default: 5) |
| **Relationships** | | |
| `rolled_over_from` | `ForeignKey(Debt)` | Prior debt settled by this transaction (self-referential FK) |
| `vehicle` | `ForeignKey(VehicleRecord)` | Nullable link to vehicle in Personal Vault |
| `residence` | `ForeignKey(ResidenceRecord)` | Nullable link to property in Personal Vault |
| `contract_document` | `ForeignKey(PersonalDocument)` | Nullable link to uploaded contract document in Document Vault |
| `notes` | `TextField` | Context notes and remarks |

### 3.2 `DebtInstallment`
Materialized installment row for every scheduled payment.

| Field Name | Type | Description |
|---|---|---|
| `id` | `BigAutoField` | Primary key |
| `debt` | `ForeignKey(Debt)` | Parent debt (`related_name='installments'`, cascade delete) |
| `sequence` | `PositiveSmallIntegerField` | `0` for down payment, `1..N` for monthly installments |
| `kind` | `CharField(16)` | `down_payment`, `installment`, `balloon` |
| `due_date` | `DateField` | Scheduled debit date |
| `amount` | `DecimalField(12,2)` | Total payment due |
| `principal` | `DecimalField(12,2)` | Principal reduction portion |
| `interest` | `DecimalField(12,2)` | Finance charge portion |
| `balance_after` | `DecimalField(12,2)` | Principal balance remaining immediately following this payment |
| `is_settled_early` | `BooleanField` | True if resolved via dealer trade-in / early payoff without direct transaction |
| `transaction` | `OneToOneField(Transaction)` | Linked actual bank debit record (`null=True, blank=True, on_delete=SET_NULL`) |
| `linked_at` | `DateTimeField(null=True)` | Timestamp when link was confirmed |
| `link_source` | `CharField(16)` | `manual`, `suggested` |

---

## 4. Calculation & Amortization Engine (`services/debt_calculator.py`)

### 4.1 APR & Payment Solving
Given principal $P$, term $N$, regular payment $M$, irregular first payment $M_1$, and optional balloon $B$:
1. Solve for monthly periodic interest rate $r$ using Newton-Raphson:
   $$P = \frac{M_1}{(1+r)} + \sum_{k=2}^{N-1} \frac{M}{(1+r)^k} + \frac{M + B}{(1+r)^N}$$
2. Real Annual Rate (実質年率): $\text{APR} = r \times 12$.
3. If total finance charge $F$ is explicitly provided from contract (分割払手数料), amortization adjustments align each installment's interest:
   $$I_k = \text{round}(B_{k-1} \times r)$$
   $$P_k = M_k - I_k$$
   $$B_k = B_{k-1} - P_k$$
4. Final installment absorbs exact rounding variance to guarantee ending balance equals 0.00.

### 4.2 Early Payoff & Trade-In Settlement Logic
When a loan is terminated early via trade-in:
- All future installments with `due_date > closed_date` are flagged `is_settled_early = True`.
- Scheduled balance at settlement date is compared against dealer payoff:
  $$\text{Rebate / Adjustment} = B_{\text{scheduled}} - \text{Payoff Amount}$$
- Status of debt transitions to `closed_early` with `closure_type='trade_in_payoff'`.

---

## 5. Intelligent Transaction Matching Engine (`services/debt_matcher.py`)

For any active debt and each unlinked installment, candidate bank transactions are scored dynamically upon request:
1. **Payee & Destination Matching:**
   - Normalize string using Unicode NFKC (handling both full-width and half-width character encodings).
   - Match if `debt.match_payee.lower()` is in `destination.lower()` or `alias.lower()`.
2. **Amount Alignment:**
   - Evaluates `abs(transaction.amount) == installment.amount` (within `match_amount_tolerance`).
3. **Date Proximity:**
   - `due_date - match_day_window <= transaction.date <= due_date + match_day_window + 3` (accommodating banking holiday shifts where the debit date moves to the next business day).
4. **Exclusions:**
   - Ignores transactions already linked to any other installment, deleted transactions, or transfers between user's own accounts.

---

## 6. REST API Design (`finance/debts/urls.py` & `views.py`)

- `GET /api/debts/`: List all debts with high-level statistics (total paid, remaining balance, next due date).
- `POST /api/debts/`: Create new debt and auto-generate its `DebtInstallment` schedule.
- `GET /api/debts/<id>/`: Debt detail with vehicle, residence, and contract document metadata.
- `PUT /api/debts/<id>/`: Update terms (triggers schedule regeneration while preserving linked transaction associations).
- `DELETE /api/debts/<id>/`: Soft or hard delete debt and release installment transaction links.
- `GET /api/debts/<id>/schedule/`: Returns complete sequence of installments with linked transaction payload.
- `GET /api/debts/<id>/suggestions/`: Returns scored transaction match candidates for unpaid installments.
- `POST /api/debts/<id>/confirm_link/`: Body: `{"installment_id": 12, "transaction_id": 3456}` (or batch confirmation).
- `POST /api/debts/<id>/unlink/`: Body: `{"installment_id": 12}`.
- `POST /api/debts/<id>/close/`: Early closure endpoint for trade-in / lump-sum settlement.
- `GET /api/debts/summary/`: Top-level summary for the application dashboard.

---

## 7. Frontend UI Design (`personalfinance-web`)

### 7.1 Navigation & Placement
- **Sidebar Integration:** New primary menu item `"Debts & Loans"` with `Landmark` icon, displaying pending suggestion count badge.
- **Top Dashboard Card:** Summary KPI displaying:
  - Total Outstanding Liability
  - Monthly Debt Commitment
  - Overall Debt Free Date
- **Personal Vault Cross-Links:**
  - Vehicle cards in `VehiclesSection.tsx` display an interactive financing chip:
    - Active: `Financed via Auto Loan →`
    - Sold/Trade-In: `Settled via Trade-In →`

### 7.2 Main Debts View (`src/components/debts/DebtsView.tsx`)
- **Metric Cards:**
  1. *Total Principal Remaining*
  2. *Monthly Scheduled Outflow*
  3. *Total Interest Paid vs. Lifetime Projected*
  4. *Payoff Radar (Target completion date)*
- **Card Deck:**
  - Filter tabs: `Active Loans` | `Paid Off / Settled` | `All`.
  - Loan cards display progress bars, monthly payment badge, lender/dealer tags, and pending transaction suggestion alerts.

### 7.3 Loan Detail & Amortization View (`DebtDetailModal.tsx`)
- **Financial Architecture Banner:**
  - Visual breakdown of Cash Price, Down Payment, Trade-in Credit, Rollover Debt, Financed Principal, and Interest.
- **Auto-Suggest Confirmation Ribbon:**
  - One-click confirmation for suggested transactions with date, payee, and exact amount matching.
- **Balance-over-Time Chart:**
  - Visual comparison between contract amortization projection and actual confirmed payment trajectory.
- **Default Data Table (`.table-container` & `.data-table`):**
  - Columns: `#`, `Due Date`, `Payment Amount`, `Principal`, `Interest`, `Remaining Balance`, `Status` (Paid, Upcoming, Settled Early, Missed), `Linked Transaction`, `Actions`.

---

## 8. Verification & Test Plan

1. **Unit Testing (`finance/debts/tests/`):**
   - Test regular loan amortization schedule generation for standard term contracts.
   - Test balloon loan schedule generation for contracts with residual balloon payment at maturity.
   - Test trade-in early settlement calculation and installment status updates.
   - Test transaction suggestion scoring with Japanese full-width and half-width payee text.
2. **Integration Testing:**
   - Link transaction to installment and verify debt balance and paid percentage updates.
   - Delete linked transaction and verify installment safely transitions to unlinked without error.
3. **Frontend E2E Build:**
   - Full TypeScript build verification (`npm run build`).
