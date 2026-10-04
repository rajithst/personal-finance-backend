# Knowledge Hub Redesign & Comprehensive Japan Tax Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the Knowledge section into a multi-article hub with an expandable sidebar menu, and add a comprehensive Japan Tax Guide complete with a year-aware pure calculation engine (2024–2026+) and an interactive "Your Numbers" panel bound to extracted 源泉徴収票 tax slips.

**Architecture:** A pure TypeScript calculation engine (`utils/tax/computeTaxBreakdown.ts`) evaluates year-specific statutory rule tables (`2024.ts`, `2025.ts`, `2026.ts`). The UI is structured into modular sections under a central article registry (`articles.ts`), with `Sidebar.tsx` supporting sub-navigation for knowledge articles.

**Tech Stack:** React, TypeScript, Lucide Icons, Vanilla CSS (Design Tokens), Vitest / Jest (for pure calculation engine tests).

**Spec:** [`docs/superpowers/specs/2026-10-04-japan-tax-knowledge-guide-design.md`](file:///Users/rajith/Documents/Projects/PersonalFinance/PFServer/personalfinance/docs/superpowers/specs/2026-10-04-japan-tax-knowledge-guide-design.md)

## Global Constraints

- Must follow existing design tokens (`var(--bg-surface)`, `var(--accent-primary)`, etc.) and glassmorphism styling.
- All tax calculation logic must be pure TypeScript functions independent of React.
- Sidebar sub-item navigation must preserve collapsed/expanded sidebar behaviors without breaking existing layouts.
- Zero TypeScript (`tsc -b`) or linting (`oxlint` / `eslint`) errors.

## Review Focus

- Gross salary bounds below statutory minimums (e.g. gross < ¥650,000 in 2025) should not yield negative taxable income or NaN values.
- Social insurance deductions exceeding net income should cap taxable income at zero.
- Transitioning between 2024 and 2025+ tax rules must correctly reflect the raised basic deduction (up to ¥950k) and salary deduction minimum (¥650k).
- Switching between Knowledge sub-articles must update the header title and subtitle cleanly without height jumps.

---

### Task 1: Pure Tax Calculation Engine & Year-by-Year Statutory Rules

**Files:**
- Create: `personalfinance-web/src/utils/tax/types.ts`
- Create: `personalfinance-web/src/utils/tax/rules/2024.ts`
- Create: `personalfinance-web/src/utils/tax/rules/2025.ts`
- Create: `personalfinance-web/src/utils/tax/rules/2026.ts`
- Create: `personalfinance-web/src/utils/tax/rules/index.ts`
- Create: `personalfinance-web/src/utils/tax/computeTaxBreakdown.ts`
- Create: `personalfinance-web/src/utils/tax/computeTaxBreakdown.test.ts`

**Interfaces:**
- Consumes: None
- Produces: `computeTaxBreakdown(inputs: TaxSlipInputs, year: number): TaxBreakdownResult`, `getTaxRulesForYear(year: number): TaxRules`

- [ ] **Step 1: Write failing unit tests for tax engine (`computeTaxBreakdown.test.ts`)**

```typescript
import { describe, it, expect } from 'vitest';
import { computeTaxBreakdown } from './computeTaxBreakdown';

describe('computeTaxBreakdown', () => {
  it('calculates 2024 tax correctly for ¥5,000,000 gross salary', () => {
    const result = computeTaxBreakdown({
      grossSalary: 5000000,
      socialInsuranceDeduction: 750000,
    }, 2024);

    expect(result.salaryIncomeDeduction).toBe(1440000); // 5M * 20% + 440k
    expect(result.netSalaryIncome).toBe(3560000); // 5M - 1.44M
    expect(result.basicDeduction).toBe(480000);
    expect(result.totalIncomeDeductions).toBe(1230000); // 750k + 480k
    expect(result.taxableIncome).toBe(2330000); // (3560000 - 1230000) rounded to 1k
    expect(result.baseIncomeTax).toBe(135500); // 2.33M * 10% - 97.5k
    expect(result.reconstructionSurtax).toBe(2845); // 135500 * 2.1% (floor)
    expect(result.calculatedWithholdingTax).toBe(138345);
    expect(result.estimatedResidentTax).toBe(238000); // 2.33M * 10% + 5000
  });

  it('applies 2025 tax reform thresholds correctly', () => {
    const result = computeTaxBreakdown({
      grossSalary: 1500000,
      socialInsuranceDeduction: 200000,
    }, 2025);

    expect(result.salaryIncomeDeduction).toBe(650000); // 2025 minimum raised to 650k
    expect(result.basicDeduction).toBe(950000); // 2025 raised basic deduction tier
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/utils/tax/computeTaxBreakdown.test.ts`
Expected: FAIL with "module not found".

- [ ] **Step 3: Implement `types.ts`, rule tables (`2024.ts`, `2025.ts`, `2026.ts`, `index.ts`), and `computeTaxBreakdown.ts`**

Define `TaxRules` and `computeTaxBreakdown` according to Section 5 of the design spec. Handle boundary clamping (preventing negative taxable income or NaN outputs).

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/utils/tax/computeTaxBreakdown.test.ts`
Expected: PASS

- [ ] **Step 5: Run lint check**

Run: `npm run lint -- --quiet`
Expected: 0 errors

---

### Task 2: Sidebar Navigation Redesign & Knowledge Article Registry

**Files:**
- Create: `personalfinance-web/src/components/knowledge/articles.ts`
- Create: `personalfinance-web/src/components/knowledge/accounting/AccountingRulesArticle.tsx`
- Modify: `personalfinance-web/src/components/knowledge/KnowledgeView.tsx`
- Modify: `personalfinance-web/src/components/layout/Sidebar.tsx`
- Modify: `personalfinance-web/src/components/layout/Header.tsx`
- Modify: `personalfinance-web/src/App.tsx`

**Interfaces:**
- Consumes: `articles.ts` registry array
- Produces: `knowledgeArticle: "accounting" | "japan_tax"` state wiring, expandable `Sidebar` group, dynamic `Header` subtitles.

- [ ] **Step 1: Create `articles.ts` registry and extract `AccountingRulesArticle.tsx`**

Move the existing classification matrix code from `KnowledgeView.tsx` into `accounting/AccountingRulesArticle.tsx` without changing any logic. Define `KNOWLEDGE_ARTICLES` registry array in `articles.ts`.

- [ ] **Step 2: Update `KnowledgeView.tsx` to route based on `knowledgeArticle` prop**

```tsx
interface KnowledgeViewProps {
  articleId?: "accounting" | "japan_tax";
  onNavigateToPayees?: () => void;
  onSelectArticle?: (id: "accounting" | "japan_tax") => void;
}
```
Render the matching article component from `KNOWLEDGE_ARTICLES`.

- [ ] **Step 3: Update `Sidebar.tsx` with expandable Knowledge group**

Add collapsible sub-items (`Accounting Rules` and `Japan Tax Guide`) under Knowledge, matching the existing `Career` sub-navigation pattern (lines 540-607 of `Sidebar.tsx`).

- [ ] **Step 4: Update `Header.tsx` and `App.tsx` with `knowledgeArticle` state**

In `App.tsx`:
Add `const [knowledgeArticle, setKnowledgeArticle] = useState<"accounting" | "japan_tax">("accounting");`. Pass to `Header`, `Sidebar`, and `KnowledgeView`.
In `Header.tsx`:
Dynamically set `knowledge.title` and `knowledge.subtitle` based on `knowledgeArticle`.

- [ ] **Step 5: Verify build & linting**

Run: `npm run lint -- --quiet && npm run build:django`
Expected: PASS with 0 errors.

---

### Task 3: Reusable UI Components & Content Sections for Japan Tax Guide

**Files:**
- Create: `personalfinance-web/src/components/knowledge/tax/components/FormulaCard.tsx`
- Create: `personalfinance-web/src/components/knowledge/tax/components/BracketTable.tsx`
- Create: `personalfinance-web/src/components/knowledge/tax/components/DeductionCard.tsx`
- Create: `personalfinance-web/src/components/knowledge/tax/components/StepFlow.tsx`
- Create: `personalfinance-web/src/components/knowledge/tax/sections/OverviewSection.tsx`
- Create: `personalfinance-web/src/components/knowledge/tax/sections/SocialInsuranceSection.tsx`
- Create: `personalfinance-web/src/components/knowledge/tax/sections/IncomeTaxSection.tsx`
- Create: `personalfinance-web/src/components/knowledge/tax/sections/ResidentTaxSection.tsx`
- Create: `personalfinance-web/src/components/knowledge/tax/sections/WithholdingVsYearEndSection.tsx`
- Create: `personalfinance-web/src/components/knowledge/tax/sections/BonusTaxSection.tsx`
- Create: `personalfinance-web/src/components/knowledge/tax/sections/DeductionsDeepDiveSection.tsx`
- Create: `personalfinance-web/src/components/knowledge/tax/sections/TaxReductionStrategiesSection.tsx`
- Create: `personalfinance-web/src/components/knowledge/tax/sections/StockLossesSection.tsx`

**Interfaces:**
- Consumes: Design tokens (`var(--bg-surface)`, `var(--accent-primary)`), `lucide-react` icons.
- Produces: Clean, modular React section components for the Japan Tax Guide.

- [ ] **Step 1: Create reusable visual components (`FormulaCard`, `BracketTable`, `DeductionCard`, `StepFlow`)**

Implement rich glassmorphism UI cards for formulas, tax bracket progress bars, and deduction cards.

- [ ] **Step 2: Implement core tax sections (Overview, Social Insurance, Income Tax, Resident Tax)**

Build `OverviewSection.tsx`, `SocialInsuranceSection.tsx`, `IncomeTaxSection.tsx`, `ResidentTaxSection.tsx` with explanatory diagrams, bracket tables, and clear Japanese tax terminology (`支払金額`, `給与所得控除`, `所得控除`, `課税所得`, `源泉徴収税額`).

- [ ] **Step 3: Implement adjustment, deduction & special rules sections**

Build `WithholdingVsYearEndSection.tsx`, `BonusTaxSection.tsx`, `DeductionsDeepDiveSection.tsx`, `TaxReductionStrategiesSection.tsx`, `StockLossesSection.tsx`.

- [ ] **Step 4: Verify type safety & linting**

Run: `npm run lint -- --quiet`
Expected: 0 errors.

---

### Task 4: Interactive "Your Numbers" Calculation Panel & Full Integration

**Files:**
- Create: `personalfinance-web/src/components/knowledge/tax/YourNumbersPanel.tsx`
- Create: `personalfinance-web/src/components/knowledge/tax/JapanTaxGuideArticle.tsx`
- Modify: `personalfinance-web/src/components/knowledge/articles.ts`

**Interfaces:**
- Consumes: `careerService.getTaxWithholdingSlips()`, `computeTaxBreakdown()`
- Produces: `JapanTaxGuideArticle` complete with sticky table of contents and dynamic 源泉徴収票 tax slip verification.

- [ ] **Step 1: Build `YourNumbersPanel.tsx`**

1. Fetch user's tax slips via `careerService.getTaxWithholdingSlips()`.
2. Allow selecting a tax slip (or manual entry fallback).
3. Extract `total_payment` (支払金額), `social_insurance_deduction`, `housing_loan_deduction`, and `withholding_tax` from the selected slip.
4. Pass values to `computeTaxBreakdown(inputs, taxYear)`.
5. Display verification summary badge (*"Exact Statutory Match"* or *"Year-End Adjustment Difference"*) and step-by-step accordion with math expressions.

- [ ] **Step 2: Build `JapanTaxGuideArticle.tsx` with Sticky Table of Contents**

Create page shell with a left sticky sidebar listing all 10 sections with active scroll highlighting (`IntersectionObserver`), rendering `YourNumbersPanel` followed by all 9 content sections.

- [ ] **Step 3: Register `JapanTaxGuideArticle` in `articles.ts`**

Link `JapanTaxGuideArticle` component to `id: "japan_tax"` in `articles.ts`.

- [ ] **Step 4: Run full verification (Lint & Build)**

Run: `npm run lint -- --quiet && npm run build:django`
Expected: 0 errors, clean production bundle build in `personalfinance/client_dist`.

- [ ] **Step 5: Commit changes**

Commit full feature implementation to git repository.

---
