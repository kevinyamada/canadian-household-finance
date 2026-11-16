# Homebuying barriers: methodology

**Question: Is the down payment really the biggest obstacle to buying a home?**

The project compares two separate constraints: cash needed to complete a purchase and gross income needed under a mortgage debt-service screen. It then asks which changes relieve the constraint and what evidence a bank would still need.

## What is observed

Statistics Canada table [46-10-0099-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=4610009901) supplies resident first-time-buyer transaction benchmarks for Vancouver City, Victoria City and Halifax Regional Municipality. The latest comparable observations in this extract are **2023**, released August 26, 2026. These are not 2026 asking prices.

The extract fixes all buyer counts, all ages, first-time status and total sex categories. It selects buyer count, median total family income, median sale price and the published median price-to-income ratio. Each city/year is unique. The sale-price estimates are buyer based; they are not a count-weighted index of identical houses. Neither property type nor buyer composition is held constant.

Table [46-10-0062-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=4610006201), now archived, provides 2020 context using 2016 geography. The main series for 2021–2023 uses 2021 geography. The 2021 overlap is retained in homebuying_source_bridge.csv. The charts use a dashed segment at the vintage boundary. They do not silently treat all geographic definitions as identical.

Published WDS flags are retained. Quality A/B/C/D/E values are not automatically treated as missing; E requires caution. Unavailable, not-applicable, confidential and F-quality values remain unavailable. Required price/income values cannot be silently filled.

The published median price-to-income ratio is retained as its own statistic. **It is not replaced with the ratio of two medians.** Observed buyer-family income is market context; it is not the assumed borrower's verified qualifying income or a population estimate for renters.

## Mortgage rate benchmark

Bank of Canada [Valet](https://www.bankofcanada.ca/valet/docs) series V122667780 (insured) and V122667786 (uninsured) cover **funds advanced**, fixed rates of five years and over. Metadata checks reject outstanding-balance series.

For each calendar year 2020–2025, the calculation takes the unweighted arithmetic mean of twelve published monthly average rates. This is not an annual loan-volume-weighted rate, a first-time-buyer-specific rate or an offered rate quote. Funds advanced can include renewals and refinancing. The 2023 rates accompany the 2023 price baseline.

A separate rate-only replay applies observed 2025 rates to fixed 2023 prices and unchanged buyer profiles. It is explicitly a scenario, not a measurement of observed 2025 affordability.

## Hypothetical buyers fixed before reviewing results

| Profile | Gross income/year | Liquid cash | Debt/month | Initially saved/month | Rent/month |
|---|---:|---:|---:|---:|---:|
| Single earner | CAD 90,000 | CAD 50,000 | CAD 300 | CAD 1,000 | CAD 2,000 |
| Two earners | CAD 150,000 | CAD 100,000 | CAD 500 | CAD 2,000 | CAD 3,000 |
| Larger deposit | CAD 120,000 | CAD 250,000 | CAD 0 | CAD 1,500 | CAD 2,500 |

Each profile is assumed to be an eligible resident first-time buyer purchasing an owner-occupied resale home with traditional down-payment funds. BC relief conditions are assumed met. These are **illustrations**, not a representative sample, client records or estimates of who banks would approve.

Common assumptions: CAD 10,000 emergency reserve; CAD 4,000 closing-cost allowance excluding transfer tax; monthly heat CAD 150, condo fees CAD 250, insurance CAD 100 and maintenance CAD 100. These require property-specific evidence. They are not measured city averages. The modeled monthly outgoings exclude living costs and income tax.

## Cash calculation

Minimum down is 5% of the first CAD 500,000 plus 10% of the remainder for prices below CAD 1.5 million. At CAD 1.5 million or above, it is 20%.

Cash target = minimum down + net transfer tax + closing allowance + reserve.

Cash above the reserve, transfer tax and closing allowance is used to reduce the mortgage, up to the purchase price. This means a larger deposit affects the income requirement too. If cash is below the minimum target, the income calculation is conditional on first having the minimum required cash; it does not pretend the transaction can close.

BC transfer tax uses the statutory marginal schedule. Eligible current first-time relief is up to CAD 8,000 through a value of CAD 835,000, tapering to zero at CAD 860,000. The Vancouver benchmark of CAD 849,000 receives partial assumed relief of CAD 3,520. Halifax deed transfer tax is 1.5%, with no first-time relief modeled.

All rules are reviewed as of **November 16, 2026**, even when prices/rates come from earlier years. The study does not reconstruct historical tax eligibility or historical loan approvals. Non-resident and foreign-buyer taxes are excluded because the profiles explicitly assume eligible residents.

## Mortgage and income calculation

For insured loans above 80% loan-to-value, premium rates are 2.8%, 3.1% or 4.0% of the base mortgage at the documented LTV tiers. A 30-year insured mortgage adds 0.20 percentage points to the premium rate. The financed premium increases the loan. No premium sales tax is modeled for the selected BC/NS cases.

Monthly fixed-rate payments use the Canadian nominal rate compounded semiannually:

- Effective monthly rate: (1 + annual rate / 2)^(1/6) − 1.
- Payment: principal × monthly rate / (1 − (1 + monthly rate)^(−12 × amortization)).
- Qualifying rate: the greater of contract rate + 2 percentage points or 5.25%.
- Stressed housing cost: stressed payment + property tax/12 + heat + 50% of condo fees.
- Required annual gross income: 12 × max(housing cost/0.39, (housing cost + other monthly debt)/0.44).

This is a common **CMHC-style 39% GDS / 44% TDS comparison screen** applied consistently to insured and uninsured cases. It is not a universal legal approval threshold: uninsured lenders set their own policies, and credit, income quality, property and insurance decisions also matter.

Baseline amortization is 25 years. The 30-year insured resale scenario assumes first-time-buyer eligibility. Interest comparisons cover the first five years at the stated rate; the analysis does not assume a rate is guaranteed for 30 years.

## Property tax is a sensitivity, not a verified bill

The model applies the published 2023 rate to an explicitly assumed assessed value equal to purchase price. Assessment sensitivities use 75% and 125% of price.

| Market | Rate used | Scope |
|---|---:|---|
| Vancouver | CAD 2.78070 per CAD 1,000 | 2023 total residential rate |
| Victoria | CAD 4.3621 per CAD 1,000 | 2023 total including school/regional levies |
| Halifax | 1.115% | 2023/24 HALIFAX urban residential scenario |

Halifax Regional Municipality has multiple tax areas; this is not a uniform municipality-wide tax bill. Actual assessments, grants, local charges, property tax statements and condo costs remain evidence gaps. The 2023 schedule is held constant during historical comparisons.

## Sensitivities and further research completed

The saved cases change one assumption at a time: price −10%/−20%; mortgage rate −1 percentage point; cash +CAD 25,000; gross income +20%; 30-year amortization; tax relief removed; reserve removed; assessment ±25%; higher heat/condo fees; or a stated draw from existing RRSP assets. Removing the reserve is a sensitivity, not a recommendation.

The 2021–2023 historical calculation decomposes the change in required income minus observed buyer-family median income into price, rates and income. Exact Shapley contributions average all six replacement orders and reconcile to the total. This is an accounting comparison of selected inputs, **not causal inference**.

Program comparisons:

- BC transfer-tax relief reduces closing cash only when eligibility is met.
- A 30-year amortization can reduce payments but increases the insured premium and first-five-year interest.
- HBP draws use separately assumed existing RRSP assets: CAD 20,000/40,000/30,000 for the profiles. The model does not add the statutory limit as free cash. Illustrative future annual repayment is draw/15; the applicable start year, eligibility and tax consequences require separate review.
- FHSA compares cases after identical twelve-month saving at flat rent/prices. Contributions are funded from that saving, counted once, up to CAD 8,000 per eligible participant. Only a refund at an assumed 30% marginal tax rate adds cash. Room, timing, deductibility and eligibility are assumed. No personal tax return is modeled.

The waiting study has 162 cases: three cities × three profiles × 12/24 months × annual price growth −5%/0%/+5% × rent growth 0%/3%/6%. Income and rates stay fixed. Incremental rent increases reduce initially stated net saving; cash earns zero interest. Paths are not forecasts and carry no probabilities. This is not a buy-versus-rent investment-return model.

## Banking audit and validation

[The bank audit working paper](bank_audit_case.md) is a fictional mortgage-file review informed by public OSFI B-20. It records the calculation result, outstanding evidence and a hold conclusion for each baseline case. No private TD policy or customer data is used.

Independent SQLite expressions reconcile cash targets and required income for every saved case. Tests cover mortgage examples, tier boundaries, eligibility, source flags, joins, program accounting, waiting assumptions, decomposition and website asset hashes.

A source exception is retained: FCAC's published 4% example shows a monthly payment of CAD 1,587.06, while its own total interest of CAD 173,418.18 and the standard formula imply CAD 1,578.06. The model uses the standard formula. Eight other monthly examples and the five-year interest example independently agree; the discrepancy is documented rather than hidden.

## Sources and reproduction

Data and rules are from Statistics Canada, Bank of Canada, CMHC, FCAC, CRA, OSFI, BC law/government, municipal/provincial tax sources and Natural Resources Canada. The source manifest preserves URLs and checksums. Some official CMHC/BC/Vancouver pages block direct downloads; the rule record states which reference facts were reviewed through their official web pages. A failed download is not presented as a preserved snapshot.

Run in the project's local desktop VS Code terminal:

~~~powershell
.\.venv\Scripts\python.exe src\homebuying_study.py
.\.venv\Scripts\python.exe src\export_homebuying.py
.\.venv\Scripts\python.exe src\build_homebuying_powerbi.py
.\.venv\Scripts\python.exe -m pytest -q
node tests\check_website.mjs
~~~

Use --refresh-sources on the study only when intentionally updating official extracts; review rule and property-tax changes separately. It uses 24 narrow WDS series rather than loading the multi-gigabyte national table. No model training, paid GPU or hosted financial computation is required.

The existing national debt-service/model experiments and renter-saving audit remain archived context. They are not used to predict an individual home purchase.
