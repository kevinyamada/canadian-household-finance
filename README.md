# Why does buying a home still feel out of reach?

[Kevin Yamada · Portfolio](https://kevinyamada.github.io/)

A housing-readiness audit using public Canadian data, Python, SQL and Power BI.

[Project website](https://kevinyamada.github.io/canadian-household-finance/) · [Power BI report](https://github.com/kevinyamada/canadian-household-finance/releases/download/v2.0.0/CanadianHouseholdFinance.pbix) · [Figures and downloads](reports/figures/portfolio/README.md) · [Three-minute walkthrough](docs/project_walkthrough.md)

## The problem

A report can use correct figures and still overstate whether someone is ready to buy a home. Reported net saving is not verified deposit cash, a positive quarter is not an annual saving rate, and a simple “5% down” calculation does not apply to every purchase price.

This project examines that part of the homebuying problem. It audits the evidence behind deliberately drafted readiness claims. It does not estimate all causes of housing affordability or recommend a personal buying date.

## What the audit found

In 2025Q4, renter households had reported net saving of **CAD 269**. It reconciles as **−572 income less consumption + 841 pension adjustment = 269**. That measure does not establish money available for a deposit.

Adding all four observed quarters gives **−CAD 557** of reported net saving per household for 2025. The source is not seasonally adjusted, so multiplying the final quarter by four would give the wrong annual total.

For an **illustrative CAD 600,000** purchase, the current minimum down payment is **CAD 35,000**. A separately assumed **2.5% closing allowance** adds CAD 15,000, giving CAD 50,000 in this upfront-cash scenario. It is not a complete closing statement or mortgage approval.

**Audit action:** verify liquid funds, the full purchase budget and mortgage eligibility before signing off on a readiness claim.

[Audit brief](reports/housing_audit.md) · [Claim register](data/processed/housing_claim_register.csv) · [Cash scenarios](data/processed/home_purchase_cash_cases.csv)

![Published 2024 renter core-housing-need estimates by province, with confidence intervals and survey coverage](reports/figures/portfolio/renter_housing_need.png)

[Browse all four figures](reports/figures/portfolio/README.md) · [Download PNG, SVG and data](https://github.com/kevinyamada/canadian-household-finance/releases/tag/v2.1.0) · [Four-page PDF](reports/figures/portfolio/CanadianHouseholdFinance-Figures.pdf)

The claim register contains eight deliberately drafted examples. It does not allege errors or fraud in Statistics Canada's reporting.

## What was built

| Part | Purpose |
| :--- | :--- |
| Python in VS Code | Reconcile the source measures, require complete years, apply price-tier rules and preserve assumptions |
| SQL / SQLite | Independently calculate annual renter totals and retain the claim register and scenarios |
| Power BI Desktop | Follow the audit conclusion, inspect the saving evidence and change the purchase-cash assumptions |
| GitHub Pages | Explore a provincial housing-need map, national renter income and consumption, and interactive purchase-cash scenarios; light by default with a small dark-mode switch |
| Tests | Check accounting, time periods, price boundaries, missing evidence, SQL agreement and report data |

The main renter analysis covers **24 quarters, 2020Q1–2025Q4**. The website also maps published renter core-housing-need estimates for **ten provinces across four survey years**, with source confidence intervals and an explicit no-coverage state for territories. Its national budget chart and purchase scenarios remain separate from the provincial survey. [Map and graph methods](docs/website_visuals.md).

The wider saved household study includes 39 groups. Source hashes and the current purchase-rule record are retained.

## Power BI

The focused report has three pages:

1. **Audit conclusion:** the question, evidence and what needs verification.
2. **Savings evidence:** annual totals, the quarterly reconciliation and audit checks.
3. **Purchase cash check:** an interactive price and closing-allowance scenario.

[Download the regular PBIX](https://github.com/kevinyamada/canadian-household-finance/releases/download/v2.0.0/CanadianHouseholdFinance.pbix) for viewing in a current Power BI Desktop on Windows. The editable source is `powerbi/HouseholdFinance.pbip`. [Opening guide](docs/powerbi_usage.md).

## Run locally in VS Code

Close the editable Power BI source project before rebuilding it.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe src/build_powerbi.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe src/validate_powerbi.py
```

This rebuild uses the saved analysis outputs and does not retrain the earlier models. Use `python run.py` for the full original pipeline plus the audit. On macOS/Linux use `python3` and `.venv/bin/python`.

VS Code tasks include **Generate housing audit**, **Rebuild focused Power BI**, **Run validation** and **Validate Power BI**. Website tasks also generate the map, check the site and export the portfolio figures. The current checks ran in the user's local VS Code terminal.

The report release passed **48 tests and 30 source-report schema checks locally in VS Code**. Its Power BI viewing copy was reopened and its cash scenario was tested. The website map-and-graphs update brings the local suite to **57 passing tests**. Browser checks passed at four widths, including map/year selection, territory coverage, zoom, chart controls, the purchase-rule boundary, keyboard access and both themes. Fresh visits start light even when the operating system prefers dark.

[Methodology and definitions](docs/methodology.md) · [Validation record](docs/validation.md) · [Further evidence needed](docs/next_steps.md)

<details>
<summary>Supporting studies and earlier report</summary>

The wider work is preserved for deeper questions rather than treated as additional main objectives.

- [Household groups](reports/segment_findings.md) and [reporting controls](reports/key_insights.md).
- [Controlled AI reporting-review experiment](reports/audit_benchmark.md), using deliberately altered claims and saved Modal H100 results.
- [Earlier national forecasts](reports/analysis.md) and [exploratory neural extension](reports/gpu_experiment.md).
- [Original eight-page report](https://github.com/kevinyamada/canadian-household-finance/releases/download/v1.0.0/CanadianHouseholdFinance.pbix).

No new GPU run is required to inspect the saved experiments.

</details>

## Sources and limits

[Statistics Canada 36-10-0662-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3610066201) supplies income, consumption, pensions and saving. The saved group release covers through 2025Q4. Wealth definitions come from [36-10-0660-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3610066001).

Purchase rules are checked as of November 16, 2026 against [CMHC](https://www.cmhc-schl.gc.ca/consumers/home-buying/mortgage-loan-insurance-for-consumers/what-are-the-general-requirements-to-qualify-for-homeowner-mortgage-loan-insurance) and [Finance Canada](https://www.canada.ca/en/department-finance/news/2024/09/delivering-the-boldest-mortgage-reforms-in-decades.html). [Bank of Canada housing affordability data](https://www.bankofcanada.ca/rates/indicators/capacity-and-inflation-pressures/real-estate-market-definitions/) are saved as matched-period context, not renter-specific qualification evidence.

These are averages over changing household groups. Consumption includes national-accounts imputations. Neither net saving nor income less consumption is an individual bank-account cash flow. Annual values sum quarterly per-household estimates and retain published rounding residuals. Scenario prices and closing allowances are assumptions. No borrower eligibility, default risk or TD losses are estimated, and no TD customer data is used.
