# SDD ledger — plan: docs/superpowers/plans/2026-10-04-japan-tax-knowledge-guide.md

## Status: COMPLETE

### Completed Deliverables:
1. **Calculation Engine & Rule Sets (`src/utils/tax/`)**
   - `types.ts`: Comprehensive interfaces for inputs, statutory rules, deduction breakdowns, and steps.
   - `rules/2024.ts`, `2025.ts`, `2026.ts`, `index.ts`: Year-aware statutory tax rule tables including progressive tax brackets, reconstruction surtax, basic deduction tiers, spouse/dependents deductions, and resident tax rates.
   - `computeTaxBreakdown.ts`: Pure mathematical tax engine supporting salary income deduction formulas, taxable income rounding (floor to ¥1,000), reconstruction surtax (2.1%), estimated resident tax (10% + ¥5,000 per capita levy), and discrepancy reconciliation.
   - `computeTaxBreakdown.test.ts`: 3/3 unit tests passing via Vitest.

2. **Knowledge Hub Sidebar Navigation (`src/components/knowledge/`)**
   - `articles.ts`: Metadata registry for knowledge articles (`accounting-rules`, `japan-tax-guide`).
   - `AccountingRulesArticle.tsx`: Extracted existing accounting rules matrix.
   - Updated `Sidebar.tsx`: Added expandable sub-navigation under Knowledge menu item for switching between Knowledge articles.
   - Updated `Header.tsx`: Dynamic titles & subtitles bound to `knowledgeArticle` state.
   - Updated `App.tsx` & `KnowledgeView.tsx`: Integrated multi-article router state.

3. **Reusable Content Components (`src/components/knowledge/tax/`)**
   - `FormulaCard.tsx`, `BracketTable.tsx`, `DeductionCard.tsx`, `StepFlow.tsx`.
   - 9 interactive content sections: Overview, Social Insurance, Income Tax Brackets & Surtax, Resident Tax & 1-Year Lag, Monthly Withholding vs. Year-End Adjustment, Bonus Taxes, Statutory Deductions, Tax Reduction Strategies (iDeCo, NISA, Furusato Nozei, Medical), and Stock Losses & 3-Year Carry-Forward (確定申告).

4. **Live "Your Numbers" Verification Panel (`YourNumbersPanel.tsx`)**
   - Binds live to extracted 源泉徴収票 (Tax Withholding Slips) from backend `careerService.getTaxSlips()`.
   - Dropdown selection to switch between tax slips.
   - Displays gross salary, net salary income, taxable income, and compares statutory calculated withholding tax against actual slip tax.
   - Interactive accordion breakdown of each step's mathematical calculation.

5. **Verification & Build Validation**
   - `npx vitest run src/utils/tax/computeTaxBreakdown.test.ts`: 3/3 passing.
   - `npm run lint -- --quiet`: 0 errors.
   - `npm run build:django`: `tsc -b` and `vite build` completed successfully.
