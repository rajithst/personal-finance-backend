# Payroll, Tax & Pension Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dedicated, deep-dive Payroll, Tax & Pension Analytics subsystem that aggregates structured `MonthlyPayslip` records and renders an interactive dashboard analyzing gross-to-net cashflows, deduction friction, pension equity (with 50/50 employer matching), tax seasonality, and career compensation trajectories.

**Architecture:** A Django REST API endpoint (`GET /api/career/payslips/analytics/`) aggregates payslip data by company, year, and bonus status. A modular React frontend (`PayrollAnalyticsView.tsx`) visualizes the data through a 5-card KPI ribbon and 4 focused analytical lenses using Recharts.

**Tech Stack:** Python 3.12, Django 5.2, Django REST Framework, React 19, TypeScript, Recharts 3.10, Lucide React icons, pytest.

**Spec:** [`docs/superpowers/specs/2026-10-03-payroll-analytics-design.md`](file:///Users/rajith/Documents/Projects/PersonalFinance/PFServer/personalfinance/docs/superpowers/specs/2026-10-03-payroll-analytics-design.md)

---

## Global Constraints

* All API data must be strictly isolated to the requesting user via `RequestManager` (`user=request.user`).
* Attendance and work time metrics (hours, overtime hours, paid leave days) are excluded.
* Japan statutory 50/50 pension match doubling rule: `total_pension_system_contribution = total_pension_employee * 2`.
* Tax aggregation must cleanly separate National Income Tax (`income_tax`), Municipal Resident Tax (`resident_tax`), and Year-End Tax Adjustments (`year_end_tax_adjustment`).
* Code must compile cleanly with `npm run build` and pass all backend `pytest` suites.

---

## Review Focus

1. **Zero Payslips Scenario:** Ensure endpoint and UI handle users with zero payslip records without division-by-zero errors or crash.
2. **Empty Filter Results:** When a specific company or year filter has zero records, UI displays a clear reset action instead of blank charts.
3. **Bonus-Only Payslips:** Correctly categorize or exclude bonus slips (`is_bonus=True`) when the bonus toggle is toggled off.
4. **Standard Remuneration Bracket Transitions:** Ensure timeline correctly captures standard remuneration grades (`std_remuneration_pension`, `std_remuneration_health`) across months.
5. **Multi-Currency Safety:** Default to JPY (`¥`) with formatted integers, handling legacy decimal conversions gracefully.

---

## Tasks

### Task 1: Backend Analytics Aggregation Endpoint & Service

**Files:**
- Create: `finance/career/tests/test_payslip_analytics_view.py`
- Modify: `finance/career/views.py`
- Modify: `finance/career/urls.py`

**Interfaces:**
- Produces: `GET /api/career/payslips/analytics/?company_id=&year=&include_bonus=` returning `summary`, `yearly_comparisons`, `monthly_timeline`, and `deduction_composition`.

- [ ] **Step 1: Write the failing test suite for `PayslipAnalyticsView`**

```python
# finance/career/tests/test_payslip_analytics_view.py
import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from finance.career.models import CompanyProfile, Employment, MonthlyPayslip

@pytest.mark.django_db
class TestPayslipAnalyticsView:
    def test_analytics_aggregations_and_ratios(self, client, auth_user):
        client.force_authenticate(user=auth_user)
        # Create company, employment, and sample payslips
        company = CompanyProfile.objects.create(user=auth_user, name="Astellas Pharma")
        employment = Employment.objects.create(
            user=auth_user, company=company, job_title="Engineer",
            start_date="2024-01-01", is_current=True
        )
        MonthlyPayslip.objects.create(
            user=auth_user, employment=employment, year=2024, month=5,
            gross_pay=1000000, net_pay=800000, pension=90000, health_insurance=50000,
            income_tax=40000, resident_tax=20000, total_tax=60000,
            social_insurance_total=140000, total_deductions=200000, is_bonus=False
        )
        MonthlyPayslip.objects.create(
            user=auth_user, employment=employment, year=2024, month=6,
            gross_pay=1000000, net_pay=800000, pension=90000, health_insurance=50000,
            income_tax=40000, resident_tax=20000, total_tax=60000,
            social_insurance_total=140000, total_deductions=200000, is_bonus=True
        )

        url = reverse('career-payslips-analytics')
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()['data']
        summary = data['summary']
        assert summary['total_gross_pay'] == 2000000.0
        assert summary['total_net_pay'] == 1600000.0
        assert summary['total_pension_employee'] == 180000.0
        assert summary['total_pension_system_contribution'] == 360000.0  # 50/50 match
        assert summary['overall_take_home_ratio'] == 80.0
        assert len(data['monthly_timeline']) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest finance/career/tests/test_payslip_analytics_view.py`
Expected: FAIL with `NoReverseMatch` or `404`

- [ ] **Step 3: Implement `PayslipAnalyticsView` and wire into `urls.py`**

In `finance/career/views.py`:
- Filter `MonthlyPayslip.objects.filter(user=request.user)`.
- Apply optional filters: `company_id` (via `employment__company_id`), `year`, and `include_bonus`.
- Compute totals, statutory doubling for pension, ratios, YoY growth comparisons, monthly Recharts points, and deduction percentage breakdowns.
- Register `path('payslips/analytics/', PayslipAnalyticsView.as_view(), name='career-payslips-analytics')` in `finance/career/urls.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest finance/career/tests/test_payslip_analytics_view.py`
Expected: PASS (100%)

- [ ] **Step 5: Commit**

```bash
git add finance/career/views.py finance/career/urls.py finance/career/tests/test_payslip_analytics_view.py
git commit -m "feat(career): implement payslip analytics backend aggregation endpoint"
```

---

### Task 2: Frontend TypeScript Contracts & API Client

**Files:**
- Modify: `personalfinance-web/src/types/career.ts`
- Modify: `personalfinance-web/src/services/careerService.ts`

**Interfaces:**
- Produces: `PayslipAnalyticsData`, `PayrollSummary`, `YearlyComparison`, `MonthlyTimelinePoint`, `DeductionCompositionItem` interfaces and `careerService.getPayslipAnalytics(params)`.

- [ ] **Step 1: Define TypeScript interfaces in `career.ts`**

Add:
```typescript
export interface PayrollSummary {
  total_gross_pay: number;
  total_net_pay: number;
  total_social_insurance: number;
  total_pension_employee: number;
  total_pension_system_contribution: number;
  total_health_insurance: number;
  total_employment_insurance: number;
  total_income_tax: number;
  total_resident_tax: number;
  total_taxes: number;
  total_year_end_adjustment: number;
  total_other_deductions: number;
  total_deductions: number;
  overall_take_home_ratio: number;
  overall_tax_ratio: number;
  overall_social_ratio: number;
  overall_deduction_ratio: number;
  payslips_count: number;
}

export interface YearlyComparison {
  year: number;
  gross_pay: number;
  net_pay: number;
  pension: number;
  health_insurance: number;
  social_insurance_total: number;
  income_tax: number;
  resident_tax: number;
  total_tax: number;
  total_deductions: number;
  take_home_ratio: number;
  yoy_gross_growth_pct: number | null;
  yoy_net_growth_pct: number | null;
}

export interface MonthlyTimelinePoint {
  year_month: string;
  year: number;
  month: number;
  is_bonus: boolean;
  company_id: number;
  company_name: string;
  gross_pay: number;
  net_pay: number;
  pension: number;
  health_insurance: number;
  employment_insurance: number;
  social_insurance_total: number;
  income_tax: number;
  resident_tax: number;
  total_tax: number;
  total_deductions: number;
  take_home_ratio: number;
  std_remuneration_pension?: number | null;
  std_remuneration_health?: number | null;
}

export interface DeductionCompositionItem {
  name: string;
  amount: number;
  percentage: number;
  color: string;
}

export interface PayslipAnalyticsData {
  summary: PayrollSummary;
  yearly_comparisons: YearlyComparison[];
  monthly_timeline: MonthlyTimelinePoint[];
  deduction_composition: DeductionCompositionItem[];
}
```

- [ ] **Step 2: Add API service method in `careerService.ts`**

```typescript
getPayslipAnalytics: async (params?: {
  company_id?: number;
  year?: number;
  include_bonus?: boolean;
}): Promise<PayslipAnalyticsData> => {
  const query = new URLSearchParams();
  if (params?.company_id) query.append('company_id', String(params.company_id));
  if (params?.year) query.append('year', String(params.year));
  if (params?.include_bonus !== undefined) query.append('include_bonus', String(params.include_bonus));
  const res = await api.get<{ data: PayslipAnalyticsData; status: boolean; message: string }>(
    `/career/payslips/analytics/?${query.toString()}`
  );
  return res.data.data;
},
```

- [ ] **Step 3: Run `npm run build` to verify type compliance**

Run: `npm run build` in `personalfinance-web`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/types/career.ts src/services/careerService.ts
git commit -m "feat(career): define payslip analytics types and service method"
```

---

### Task 3: KPI Header & Filter Deck Components

**Files:**
- Create: `personalfinance-web/src/components/career/analytics/PayrollKPIHeader.tsx`
- Create: `personalfinance-web/src/components/career/analytics/PayrollFilterDeck.tsx`

**Interfaces:**
- `PayrollKPIHeaderProps`: takes `summary: PayrollSummary`, `currency: string`.
- `PayrollFilterDeckProps`: takes `companies`, `years`, selected filters, callbacks.

- [ ] **Step 1: Implement `PayrollKPIHeader.tsx`**

Render 5 cards:
1. Cumulative Gross Earnings (with average monthly badge)
2. Net Take-Home Pay (vibrant green `#10b981`)
3. Net Retention Ratio (e.g. `78.2%` with `-21.8% friction`)
4. Pension Accumulated & System Equity (with `50/50 employer match: ¥2X,XXX,XXX`)
5. Total Taxes Paid (Income Tax % vs Resident Tax %)

- [ ] **Step 2: Implement `PayrollFilterDeck.tsx`**

Render glass container with:
- Title, subtitle, Back Button (`← Back to Career Hub`)
- Company Dropdown (`All Companies` + list of employers)
- Fiscal Year Dropdown (`All Time` + years)
- Bonus Toggle button (`[Include Seasonal Bonuses]`)

- [ ] **Step 3: Run `npm run build` to verify components**

Run: `npm run build` in `personalfinance-web`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/components/career/analytics/PayrollKPIHeader.tsx src/components/career/analytics/PayrollFilterDeck.tsx
git commit -m "feat(career): add payroll kpi header and filter deck components"
```

---

### Task 4: Analytical Lenses 1 & 2 (Friction/Waterfall & Pension Vault)

**Files:**
- Create: `personalfinance-web/src/components/career/analytics/PayrollFrictionLens.tsx`
- Create: `personalfinance-web/src/components/career/analytics/PensionVaultLens.tsx`

**Interfaces:**
- `PayrollFrictionLens`: takes `monthlyTimeline`, `deductionComposition`, `summary`, `currency`.
- `PensionVaultLens`: takes `monthlyTimeline`, `summary`, `currency`.

- [ ] **Step 1: Implement `PayrollFrictionLens.tsx` (Lens 1)**

- Recharts Stacked Bar / Composition Chart: Gross pay composed of Net Pay, Pension, Health, Income Tax, Resident Tax, Other.
- Recharts Donut Pie Chart: Breakdown percentage of all deductions.
- Metrics Strip: Social Insurance Burden % vs Tax Friction %.

- [ ] **Step 2: Implement `PensionVaultLens.tsx` (Lens 2)**

- Recharts Dual-Line Area Chart: Cumulative Employee Pension Contributions vs Total System Contributions (reflecting 50% employer statutory match).
- Recharts Step Chart: Standard Monthly Remuneration bracket transitions (`標準報酬月額`) over time.
- Health Insurance and Employment Insurance protection card.

- [ ] **Step 3: Run `npm run build` to verify**

Run: `npm run build` in `personalfinance-web`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/components/career/analytics/PayrollFrictionLens.tsx src/components/career/analytics/PensionVaultLens.tsx
git commit -m "feat(career): implement friction waterfall and pension vault lenses"
```

---

### Task 5: Analytical Lenses 3 & 4 (Tax Dynamics & Multi-Year Trajectory)

**Files:**
- Create: `personalfinance-web/src/components/career/analytics/TaxDynamicsLens.tsx`
- Create: `personalfinance-web/src/components/career/analytics/CumulativeYoYLens.tsx`

**Interfaces:**
- `TaxDynamicsLens`: takes `monthlyTimeline`, `summary`, `currency`.
- `CumulativeYoYLens`: takes `yearlyComparisons`, `monthlyTimeline`, `currency`.

- [ ] **Step 1: Implement `TaxDynamicsLens.tsx` (Lens 3)**

- Recharts Grouped Bar Chart: National Income Tax (`所得税`) vs Municipal Resident Tax (`住民税`) per month.
- Special Event Badges:
  - June Inhabitant Tax Step-Up Callout (reflecting previous calendar year taxable earnings).
  - December Year-End Adjustment (`年末調整`) indicator (refund or additional withholding).

- [ ] **Step 2: Implement `CumulativeYoYLens.tsx` (Lens 4)**

- Recharts Area Curve: Lifetime Cumulative Gross vs. Cumulative Net Take-Home, highlighting the widening deduction gap.
- YoY Comparative Audit Table:
  - Columns: Year, Gross Pay, Social Insurance, Income Tax, Resident Tax, Total Deductions, Net Pay, Take-Home %, YoY Growth %.
  - Color-coded badges for growth changes.

- [ ] **Step 3: Run `npm run build` to verify**

Run: `npm run build` in `personalfinance-web`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/components/career/analytics/TaxDynamicsLens.tsx src/components/career/analytics/CumulativeYoYLens.tsx
git commit -m "feat(career): implement tax dynamics and cumulative yoy lenses"
```

---

### Task 6: Main View Assembly & Navigation Integration

**Files:**
- Create: `personalfinance-web/src/components/career/PayrollAnalyticsView.tsx`
- Modify: `personalfinance-web/src/components/layout/Sidebar.tsx`
- Modify: `personalfinance-web/src/components/career/CareerHubView.tsx`
- Modify: `personalfinance-web/src/App.tsx`

**Interfaces:**
- Connects route state `currentTab === "payroll_analytics"`.
- Wires top navigation, sidebar, and back navigation.

- [ ] **Step 1: Implement `PayrollAnalyticsView.tsx`**

Assembles:
- Data fetching via `careerService.getPayslipAnalytics`.
- `PayrollFilterDeck` with active filters.
- `PayrollKPIHeader`.
- 4-Lens Segmented Tab Switcher (Friction & Deductions, Pension & Social Security, Tax Dynamics, Multi-Year & YoY).
- Dynamic rendering of each lens.
- Zero-state and empty-state handlers.

- [ ] **Step 2: Update `Sidebar.tsx`**

Add 5th sub-item under Career Hub:
```tsx
{
  subTab: "payroll_analytics",
  label: "Payroll & Tax Analytics",
  icon: LineChart,
  color: "#06b6d4",
}
```

- [ ] **Step 3: Update `CareerHubView.tsx`**

In the top contextual action buttons deck, add:
```tsx
<button
  type="button"
  className="btn btn-secondary btn-sm"
  onClick={() => onNavigateToAnalytics?.()}
  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
>
  <LineChart size={14} color="#06b6d4" />
  <span>Payroll Analytics</span>
</button>
```

- [ ] **Step 4: Register in `App.tsx`**

Wire `currentTab === "payroll_analytics"` to render `<PayrollAnalyticsView currency={currency} onBack={() => setCurrentTab("career")} />`.

- [ ] **Step 5: Run `npm run build` to verify integration**

Run: `npm run build` in `personalfinance-web`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/components/career/PayrollAnalyticsView.tsx src/components/layout/Sidebar.tsx src/components/career/CareerHubView.tsx src/App.tsx
git commit -m "feat(career): assemble payroll analytics view and wire navigation"
```

---

### Task 7: End-to-End Verification & Full Test Suite

**Files:**
- All touched files.

- [ ] **Step 1: Run full backend test suite in worktree**

Run: `pytest`
Expected: All backend tests PASS (100%)

- [ ] **Step 2: Run frontend production build**

Run: `npm run build` in `personalfinance-web`
Expected: PASS with 0 errors

- [ ] **Step 3: Verification report**

Verify that all 4 lenses render, filtering works across companies and years, pension employer match displays accurately, and navigation seamlessly flows between Career Hub and Payroll Analytics.
