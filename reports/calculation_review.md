# Calculation and display review

## What the repeated zeros meant

The previous “cash shortfall” measured only money still missing. It was floored at zero. A buyer already above the minimum could receive more cash or face a lower price while that shortfall stayed at zero.

The arithmetic was consistent, but the display hid useful changes. The website and Power BI now show **cash above or below the minimum** and **income above or below the requirement**. Cash above the minimum is used in the down payment; it is not cash left over after purchase. The separately stated reserve is retained.

For the Vancouver two-earner example:

| Change | Cash vs minimum | Annual income vs requirement | Monthly mortgage |
|---|---:|---:|---:|
| Baseline | CAD 14,640 above | CAD 40,014 short | CAD 4,742 |
| Price 10% lower | CAD 29,308 above | CAD 17,429 short | CAD 4,148 |
| Price 20% lower | CAD 39,496 above | CAD 2,630 above | CAD 3,622 |
| Mortgage rate 1 point lower | CAD 14,640 above | CAD 24,922 short | CAD 4,292 |
| CAD 25,000 more cash | CAD 39,640 above | CAD 32,879 short | CAD 4,549 |
| Gross income 20% higher | CAD 14,640 above | CAD 10,014 short | CAD 4,742 |
| 30-year amortization | CAD 14,640 above | CAD 30,070 short | CAD 4,367 |
| HBP: draw existing RRSP funds | CAD 54,640 above | CAD 29,509 short | CAD 4,458 |

## What was rechecked

- 468 purchase cases: cash targets, shortfalls, signed positions, premium-financed loans and allocation of available funds.
- A separate month-by-month amortization schedule for all 468 purchase cases, checking the balance and interest over the first 60 payments.
- 36 program comparisons: before/after cash identities, FHSA money counted once, and HBP draws limited to the separately stated existing assets.
- 162 waiting cases: cash target and available-fund identities.
- Independent SQLite expressions for required income, cash targets and gaps, signed positions, loan balances and monthly outgoings.
- Source hashes, source units/flags, city/year keys, twelve-month rate coverage, policy boundaries and portable Power BI imports, covered by the automated tests.

The program section shows the variable a measure changes: payment and interest for 30 years, liquid purchase cash for HBP/FHSA, and transfer tax for BC relief. BC relief in Halifax is labeled **not applicable**, rather than displayed as a zero benefit.

### Reconciliation results

| Check | Rows | Maximum absolute error | Result |
|---|---:|---:|---|
| Cash shortfall identity | 468 | 0 | Pass |
| Signed cash position | 468 | 0 | Pass |
| Signed income position | 468 | 0 | Pass |
| Cash allocation stays within funds | 410 | 0 | Pass |
| Financed premium and loan identity | 468 | 0 | Pass |
| Independent 60-month balance schedule | 468 | 7.91624188e-09 | Pass |
| Independent 60-month interest sum | 468 | 5.26779331e-09 | Pass |
| Program cash identity: before | 36 | 0 | Pass |
| Program cash identity: after | 36 | 0 | Pass |
| FHSA contributions counted once | 9 | 0 | Pass |
| HBP moves stated existing assets | 9 | 0 | Pass |
| Waiting cash identity | 162 | 0 | Pass |
| Nine baseline price/cash thresholds | 9 | 0 | Pass |

Small floating-point differences within the stated tolerances are retained in [the machine-readable review](../data/processed/homebuying_review_checks.csv).

## The next analytical step: a price that fits

For each of the nine baseline buyers, the study now finds:

1. The largest whole-dollar purchase price that passes both financial checks with starting cash and income fixed.
2. The least whole-dollar total liquid cash that passes at the benchmark price and unchanged income.

For the Vancouver two-earner example, the exact modeled price limit is **CAD 690,331**. The website conservatively displays **About CAD 690,000**. At the benchmark price, total cash required to fit the income screen is **CAD 267,570**, or **CAD 167,570** more than the starting funds.

The search separately handles transfer-tax, insurance-premium and insured/uninsured-rate intervals. It does not assume one globally smooth relationship. Tests compare the search against every whole dollar in small exhaustive domains, including a case with a disconnected feasible set. All nine published thresholds are checked at the threshold and the next dollar.

Website price limits are rounded down and extra cash up to CAD 1,000. Exact values remain in [homebuying_price_limits.csv](../data/processed/homebuying_price_limits.csv).

## Official-source cross-checks and scope

CMHC's public GDS/TDS guidance confirms the 39%/44% comparison, financed premiums, tax/heat and half condo fees, and the qualifying-rate rule. BC's published exemption example for a CAD 849,000 property independently confirms CAD 14,980 gross tax, CAD 3,520 relief and CAD 11,460 payable.

- [CMHC debt-service guidance](https://www.cmhc-schl.gc.ca/professionals/project-funding-and-mortgage-financing/mortgage-loan-insurance/calculating-gds-tds)
- [BC published exemption examples](https://www2.gov.bc.ca/gov/content/taxes/property-taxes/property-transfer-tax/exemptions/first-time-home-buyers/current-amount)
- [Full methodology](../docs/homebuying_methodology.md)

The data vintage, hypothetical profiles and eligibility assumptions remain explicit. Prices/rates are 2023 benchmarks; rules were reviewed November 16, 2026. A financial-screen limit is not a comfortable spending budget, a current price quote or a bank approval. Actual borrower evidence, property costs and lender policy still need review.
