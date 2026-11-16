# Methodology: housing-readiness audit

**Why does buying a home still feel out of reach?**

The study audits one part of that problem: whether public saving figures and upfront-cost assumptions support a homebuying-readiness claim. It does not measure all causes of affordability, survey people's feelings or choose a personal buying date.

## Data and definitions

The main observations are renter household averages from Statistics Canada's Distributions of Household Economic Accounts, 2020Q1–2025Q4. Income, consumption, pension-entitlement changes and net saving come from table 36-10-0662-01.

Amounts are nominal CAD per household for the quarter and are not seasonally adjusted. The households represented by an average can change over time. Consumption includes national-accounts imputations. These are not individual bank-account budgets.

Reported net saving equals disposable income plus the change in pension entitlements minus consumption, subject to published rounding. A pension entitlement is not verified money available for a down payment. Income less consumption is also an accounting measure, not measured deposit cash flow.

## Controls and annual totals

The pipeline requires unique renter quarters and complete accounting measures. It checks the quarterly saving identity with a CAD 2 rounding allowance. A year must contain all four distinct observed quarters before it enters the annual analysis. The annual values sum those four quarterly per-household estimates; minor rounding residuals remain visible.

SQLite independently calculates annual income, consumption, saving and the residual in `renter_annual_audit`. Those totals must agree with Python. The project does not multiply a favorable final quarter by four.

The public data do not observe verified deposit balances or the gross borrower income, debts, credit and loan terms needed for mortgage qualification. Those are recorded as **Needs evidence**, rather than filled in from group averages.

## Purchase-cash scenarios

The calculation uses the rule record dated November 16, 2026, with CMHC and Finance Canada sources:

- Up to CAD 500,000: 5% minimum down.
- Above CAD 500,000 and below CAD 1.5 million: 5% on the first CAD 500,000 and 10% on the remainder.
- At CAD 1.5 million or more: 20% minimum down.

The 30 scenarios combine ten illustrative purchase prices with three separately assumed closing-cost allowances, 1.5%, 2.5% and 4%. These are not measured national home prices, tax calculations or recommended budgets.

For CAD 600,000, minimum down is CAD 35,000. A 2.5% allowance adds CAD 15,000, giving CAD 50,000 in that upfront-cash scenario. Mortgage approval, property-specific taxes, insurance and a complete closing statement remain separate.

The source record notes an inconsistent legacy insurance-limit sentence on the FCAC page; the insurance boundary is taken from the current CMHC requirements and the Finance Canada reform record.

## Claim review

The register contains eight deliberately drafted claims. It demonstrates how to distinguish a supported accounting statement from an incorrect calculation or an unsupported interpretation. These are not identified errors in published StatCan reports and are not a sample for estimating real-world misstatement rates.

Examples include treating net saving as deposit cash, treating net worth as liquid funds, annualizing one quarter and applying a flat 5% rule above CAD 500,000. The review produces a reason and evidence reference. It is not a professional audit opinion, fraud detector or automated loan decision.

## Website map and graphs

The website adds published renter core-housing-need estimates from Statistics Canada 46-10-0085-01 for the ten provinces, survey years 2018, 2021, 2022 and 2024. It preserves published confidence intervals, uses the published national benchmark and marks the territories outside coverage. The national income/consumption graph and purchase-cash chart use the existing audit outputs. These measures have different definitions and periods; selecting a province does not turn national averages into provincial values. See [source selection, geometry, units and browser checks](website_visuals.md).

## Reproducibility

`src/housing_audit.py` regenerates the summary, tables, brief, SQLite views and Python figure from preserved snapshots. `src/build_powerbi.py` then embeds those outputs in the three-page report. Tests verify rule boundaries, invalid inputs, complete years, reconciliation, SQL agreement and embedded report data.

The Bank of Canada affordability index is preserved for the matched 2020–2025 period as context. Its representative-household cost ratio does not measure a renter's deposit funds and is not rescaled into borrower eligibility.

[Audit brief](../reports/housing_audit.md) · [Purchase rule record](../data/raw/housing/purchase_rules.json) · [Supporting-study methods](supporting_methodology.md)
