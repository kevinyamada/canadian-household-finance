# Why does buying a home still feel out of reach?

**Is the down payment really the biggest obstacle to buying a home?**

This project separates the cash needed to buy from the income needed for the mortgage, then reviews the evidence a bank would need before signing off.

**Main finding:** four of nine hypothetical buyer examples have enough cash to meet the minimum purchase budget but insufficient income under the mortgage screen.

[Interactive website](https://kevinyamada.github.io/canadian-household-finance/) · [Findings](reports/homebuying_findings.md) · [Calculation review](reports/calculation_review.md) · [Bank audit case](docs/bank_audit_case.md)

![Cash and income comparison](reports/figures/homebuying/01_cash_and_income.png)

## One example

Two earners have CAD 100,000 cash and CAD 150,000 annual gross income. At Vancouver's CAD 849,000 transaction benchmark, their minimum purchase cash plus reserve is CAD 85,360. They are CAD 14,640 above that minimum; this extra amount goes toward the down payment.

The stressed mortgage screen still needs CAD 190,014 income, leaving a CAD 40,014 annual income shortfall.

The new direct price check puts this example's limit at **about CAD 690,000** with starting finances fixed. Alternatively, keeping the benchmark price and income requires **about CAD 168,000 more cash**. These are separate financial-screen scenarios, not spending recommendations or loan approvals.

## Why the old comparison showed zeros

“Cash shortfall” only measured money still missing. It stayed zero when an already-funded buyer received more cash. The updated table shows cash and income **above or below** the requirements instead.

Program cards now show what the measure changes: mortgage payment and interest for 30 years, transfer tax for BC relief, or available purchase cash for HBP/FHSA. A BC program in Halifax is marked not applicable.

The [review](reports/calculation_review.md) reconciles budgets, loans, program accounting and a separate 60-month payment schedule. **130 local tests pass**, including exhaustive checks of small price/cash search domains. Browser checks cover four widths, all 117 current purchase scenarios and all 36 program comparisons.

## Explore the work

| Deliverable | What it answers |
|---|---|
| [Website](https://kevinyamada.github.io/canadian-household-finance/) | A coloured provincial map, buyer comparisons, price limits and graphs |
| [Power BI Desktop report](https://github.com/kevinyamada/canadian-household-finance/releases/download/v3.1.0/HomebuyingBarriers.pbix) | Seven pages: answer, cash/income, changes, price limits, history, waiting and bank audit |
| [Bank audit working paper](docs/bank_audit_case.md) | What calculations, exceptions and missing evidence matter before sign-off? |
| [Seven figures](reports/figures/homebuying/README.md) | PNG/SVG files and a seven-page PDF |
| [Figure/data pack](https://github.com/kevinyamada/canadian-household-finance/releases/download/v3.1.0/HomebuyingBarriers-Figures.zip) | Figures, processed tables and review notes |
| [Methodology](docs/homebuying_methodology.md) | Sources, assumptions, rules, formulas and limits |

The website starts in light mode. Its small theme button remembers an explicit choice. The provincial map and national renter trend remain visible. The browser displays saved Python results rather than duplicating lending rules.

## Scope and data

The purchase cases use Vancouver City, Victoria City and Halifax Regional Municipality. **2023 is the latest comparable first-time-buyer observation in the selected Statistics Canada source**, released in 2026. Buyer-based transaction medians cover a changing property mix; these are not 2026 listings or matched-house prices.

Bank of Canada funds-advanced fixed five-year-and-over rates provide national benchmarks. Mortgage and tax rules were reviewed November 16, 2026. Borrower finances, eligibility, property costs and reserves are assumptions. Halifax costs use an explicitly assumed urban tax-rate scenario.

The study has 468 purchase scenarios, 162 waiting scenarios, 36 buyer-measure comparisons, nine later-rate replays, a historical price/rate/income decomposition and nine baseline price/cash thresholds. The provincial map measures renter core housing need, a separate measure and period.

Sources are Statistics Canada and official Canadian public bodies: Bank of Canada, CMHC, FCAC, CRA, OSFI, municipal/provincial governments and Natural Resources Canada. The [source manifest](data/raw/homebuying/manifest.json) preserves URLs and hashes.

## Banking and audit relevance

The practice file demonstrates reproducible calculations, documented exceptions and verified-evidence requirements relevant to a bank such as TD. The fictional files remain on hold: a mathematical pass does not verify the borrower, property or lender policy.

Public OSFI B-20 informs the review approach. A CMHC-style 39% GDS/44% TDS screen is used consistently for comparison; uninsured lender criteria can differ. This is an independent portfolio project with no TD customer data, internal policy or endorsement.

## Reproduce in desktop VS Code

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\homebuying_study.py
.\.venv\Scripts\python.exe src\export_homebuying.py
.\.venv\Scripts\python.exe src\build_homebuying_powerbi.py
.\.venv\Scripts\python.exe -m pytest -q
node tests\check_website.mjs
~~~

Python 3.12+; Windows is needed for native Power BI Desktop checks. Open powerbi/HomebuyingBarriers.pbip for editable source, or download the regular .pbix. Imported data do not need the author's folders. See the [opening guide](docs/powerbi_usage.md).

Analysis, SQL, plotting, browser checks and native report checks run through the desktop VS Code terminal. Use --refresh-sources only for an intentional official-data refresh and review rule/tax changes separately.

[Mortgage model](src/homebuying_model.py) · [Price/cash search](src/homebuying_limits.py) · [Review](src/homebuying_review.py) · [SQL](sql/homebuying.sql) · [Study](src/homebuying_study.py) · [Tests](tests/test_homebuying_limits.py)

Earlier national model experiments and the renter-saving audit remain supporting research. Official statistics retain their applicable terms, including the [Statistics Canada Open Licence](https://www.statcan.gc.ca/en/reference/licence).
