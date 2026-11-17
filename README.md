# Why does buying a home still feel out of reach?

**Is the down payment really the biggest obstacle to buying a home?**

This project separates purchase cash from mortgage income, then checks whether a calculation and its supporting evidence can be trusted.

**Finding:** four of nine hypothetical buyer examples have enough minimum cash but insufficient income under the mortgage screen.

[Website](https://kevinyamada.github.io/canadian-household-finance/) · [Short interview brief](docs/interview_brief.md) · [Findings](reports/homebuying_findings.md) · [Worked calculation audit](reports/mortgage_calculation_audit.md)

![Cash and income](reports/figures/homebuying/01_cash_and_income.png)

## One buyer, two hurdles

The Vancouver two-earner example has CAD 100,000 cash and CAD 150,000 gross annual income. At the CAD 849,000 transaction benchmark, cash is CAD 14,640 above the minimum budget including reserve. That extra cash goes toward the down payment.

The mortgage-income screen still needs CAD 190,014, leaving CAD 40,014 short. About CAD 690,000 fits the starting finances under the stated baseline assumptions.

## What the newer rates change

September 2026 national mortgage rates reduce required income to CAD 175,293 and the monthly mortgage payment from CAD 4,742 to CAD 4,303. Income remains short.

This holds the 2023 price, tax schedule and buyer finances fixed. It isolates rates; it does not establish today's affordability. The latest reviewed Statistics Canada release still uses 2023 sales and matched buyer income. [Source dates and retrieval limits](reports/source_refresh.md)

## The banking audit example

At a separately stated CAD 764,100 price, the correct calculation needs CAD 167,429 income. Using the contract rate instead of the qualifying rate gives CAD 141,543 and creates a false pass for the CAD 150,000-income buyer.

Four defined mistakes are tested across 117 saved purchase scenarios. All 585 correct/flawed results are retained, with reviewer controls and evidence requirements. These are deliberate demonstrations, not observed bank mistakes or a bank error rate.

[Calculation audit](reports/mortgage_calculation_audit.md) · [Mortgage-file working paper](docs/bank_audit_case.md) · [All calculations](data/processed/homebuying_calculation_audit.csv)

## Explore the work

| Deliverable | Contents |
|---|---|
| [Interactive website](https://kevinyamada.github.io/canadian-household-finance/) | Coloured Canada map, cash/income comparisons, price limits, newer rates and audit example |
| [Power BI Desktop report](https://github.com/kevinyamada/canadian-household-finance/releases/download/v3.2.0/HomebuyingBarriers.pbix) | Nine native pages with imported data |
| [Nine figures](reports/figures/homebuying/README.md) | PNGs, editable SVGs and a nine-page PDF |
| [Figure/data pack](https://github.com/kevinyamada/canadian-household-finance/releases/download/v3.2.0/HomebuyingBarriers-Figures.zip) | Figures, source tables, review notes and interview brief |
| [Calculation review](reports/calculation_review.md) | Budgets, loan schedules, program accounting and thresholds |
| [Methodology](docs/homebuying_methodology.md) | Sources, assumptions, rules and limitations |

The website starts in light mode and remembers an explicit theme choice. The coloured provincial map measures renter core housing need; it is separate from city purchase examples.

## Sources and scope

Vancouver City, Victoria City and Halifax Regional Municipality use Statistics Canada city-buyer transaction medians. The buyer/property mix can change. Buyer finances, eligibility, costs and reserves are assumptions. Halifax uses an urban tax-rate scenario.

Original matched price/rate benchmarks are 2023. Mortgage and tax rules were reviewed November 16, 2026; source availability was reviewed November 17. The new monthly-rate sensitivity keeps historical taxes and finances fixed. Statistics Canada's desktop WDS endpoint returned HTTP 403, so its official release pages were reviewed and the existing checksummed extract retained; revisions were not re-downloaded.

Public OSFI B-20 informs the evidence review. A CMHC-style 39% GDS/44% TDS screen supports consistent comparisons; actual uninsured lender limits can differ. These results are not approvals, comfortable-spending recommendations or default predictions. No TD customer data or internal policy is used.

[Original source manifest](data/raw/homebuying/manifest.json) · [Refresh manifest](data/raw/homebuying_refresh/manifest.json) · [Validation](reports/homebuying_validation.json)

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

Python 3.12+; Windows for native Power BI checks. The regular PBIX contains imported data and needs no author's folders. [Opening guide](docs/powerbi_usage.md)

An intentional rate refresh uses src/refresh_homebuying_sources.py with --as-of and a dated --statcan-review file. Review policy/tax changes and matched buyer-data revisions separately; do not relabel an old price with a new rate date.

[Model](src/homebuying_model.py) · [Price/cash search](src/homebuying_limits.py) · [Updates and audit](src/homebuying_updates.py) · [SQL](sql/homebuying_updates.sql) · [Study](src/homebuying_study.py)

Analysis, SQL, plots and checks run in desktop VS Code. Earlier national forecasts and the renter-saving audit remain supporting research. Official data retain their applicable terms, including the [Statistics Canada Open Licence](https://www.statcan.gc.ca/en/reference/licence).
