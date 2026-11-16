# What the analysis says and what to do next

**Decision:** Review leverage and income relative to consumption separately. Show all three components before describing household saving. Monitor payment growth alongside income growth. Keep the previous-quarter forecast as the benchmark.

Group findings use **2025Q4**; the national payment finding uses **2026Q2**. These are separate snapshots.

## 1. Compare different kinds of household pressure

**Household groups | 2025Q4**

Debt / annualized disposable income: mortgage owners 306.1%; renters 56.4%.

Debt relative to income and income relative to consumption measure different kinds of pressure.

**Action:** Review leverage and income relative to consumption separately.

**Inspect:** Power BI → Household groups. Evidence: `data/processed/segment_latest.csv`.

## 2. Positive saving can hide an income gap

**Renter average | 2025Q4**

Income less consumption: CAD -572. Pension adjustment: CAD +841. Net saving: CAD +269.

The pension adjustment changes the sign. Positive net saving does not mean income covered consumption.

**Action:** Show all three components before describing household saving.

**Inspect:** Power BI → Reporting controls. Evidence: `data/processed/segment_latest.csv`.

## 3. Payments rose while the ratio fell

**National payment ratio | 2026Q2**

Ratio 14.52%. Payments +0.97%; income +2.06% quarter over quarter.

Income grew faster than required payments. The lower ratio does not mean payments fell.

**Action:** Monitor payment growth alongside income growth.

**Inspect:** Power BI → Household pressure. Evidence: `data/processed/summary.json`.

## 4. Complex models had higher average error

**Forecast test | 2019Q1 to 2026Q2**

Average absolute error: previous quarter 0.245; random forest 0.250; neural 0.387 percentage points.

Lower error is better. The small sample does not establish a clear model advantage; the neural extension is exploratory.

**Action:** Keep the previous-quarter forecast as the benchmark.

**Inspect:** Power BI → Model evaluation and GPU experiment. Evidence: `data/processed/holdout_scores.csv; data/processed/gpu_comparison.csv`.

## What the AI experiment adds

The saved H100 experiment tests review of deliberately misleading statements against trusted evidence cards. The selected reviewer flagged 100.00% of unsupported evaluation examples, with a 1.40% false alarm rate on supported examples. These are 1,456 unique, balanced template cases, with 5 matched repetitions. The result supports a review prototype; it does not establish reliability on arbitrary bank reports. A comprehensive rules baseline and independently reviewed real excerpts are the next validation.

## Actions completed in this project

- Added this summary and the opening Key insights page, with dates, evidence and a next action for each finding.
- Kept the renter saving components separate and reconciled their accounting identity.
- Compared forecasts with the previous-quarter benchmark and retained the measured result.
- Preserved source snapshots, review exceptions and saved GPU outputs so the results can be checked without another paid run.

## What requires further evidence

Portfolio validation needs approved borrower data. Live forecasting evaluation needs new releases and archived vintages. General AI review validation needs independently labeled real report wording. The [next-step plan](../docs/next_steps.md) specifies the inputs and acceptance evidence for each.

Public household group averages. They support reporting review and investigation, not individual default predictions. Group and national dates differ.

[Plain-language walkthrough](../docs/project_walkthrough.md) · [Group findings](segment_findings.md) · [National analysis](analysis.md) · [AI benchmark](audit_benchmark.md)
