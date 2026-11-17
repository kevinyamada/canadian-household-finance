# Would this mortgage file pass a first review?

**Educational banking audit case.** A fictional first-time buyer has the down payment. Does the evidence support signing off on purchase readiness?

This is relevant to a bank such as TD because mortgage-file review joins financial analysis with evidence quality, policy checks and a documented decision. It uses public guidance, not TD's internal policies, customer data or an actual credit decision.

## Practice file: Vancouver, two earners

| Input or calculation | Amount |
|---|---:|
| Purchase-price benchmark | CAD 849,000 |
| Assumed household gross income | CAD 150,000/year |
| Assumed liquid cash | CAD 100,000 |
| Existing monthly debt payments | CAD 500 |
| Minimum down payment | CAD 59,900 |
| Transfer tax after conditional BC relief | CAD 11,460 |
| Closing allowance | CAD 4,000 |
| Emergency reserve | CAD 10,000 |
| Minimum cash target including reserve | CAD 85,360 |
| Down payment actually used from available cash | CAD 74,540 |
| Income required by the modeled debt-service screen | CAD 190,014/year |
| Annual gross-income shortfall | CAD 40,014 |

Price is an observed **2023 buyer-based city transaction median**, not a present-day listing or valuation. Rates are the 2023 Bank of Canada benchmark. Mortgage and tax rules are reviewed November 16, 2026. Borrower finances and eligibility are assumptions.

**Review conclusion: hold.** The cash calculation fits, but the income screen does not. Borrower and property evidence is also missing. A successful cash check cannot establish an approvable mortgage file.

## Working paper

| Review objective | Work performed | Result | Evidence still needed |
|---|---|---|---|
| Enough funds to complete | Recalculate down payment, transfer tax, allowance and reserve | Modeled cash passes | Account history and source/availability of funds |
| Capacity to service debt | Use stressed payments, taxes, heat, half condo fees and other debt | Modeled income exception: CAD 40,014 | Sustainable income, employment and debt records |
| Property costs and value | Separate transaction benchmark from a property-specific bill | Assumptions remain | Purchase agreement, valuation, tax and condo documents |
| Policy and insurance | Identify assumed first-time, residency, tax and insurance conditions | Eligibility unverified | Appropriate borrower/property and insurer evidence |
| Reperformance | Reconcile Python calculations to separate SQL formulas | Arithmetic agrees | Retain versions and reviewer rationale |

Public [OSFI B-20](https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/residential-mortgage-underwriting-practices-procedures-guideline-2017) informs the evidence and independent-review approach. OSFI expects institutions to set and apply their own underwriting policies. The project uses a CMHC-style 39%/44% comparison screen; it does not claim this reproduces TD policy, establishes compliance or predicts default.

## Does a proposed fix resolve the exception?

| One change from baseline | Remaining annual income shortfall |
|---|---:|
| CAD 25,000 more cash | CAD 32,879 |
| Mortgage rate 1 percentage point lower | CAD 24,922 |
| Gross income 20% higher | CAD 10,014 |
| 30-year amortization | CAD 30,070 |
| Purchase price 20% lower | CAD 0 |

Only the lower-price case clears both modeled financial checks among these changes. It still requires evidence and lender review. Extending to 30 years reduces the monthly mortgage payment from CAD 4,742 to CAD 4,367, but raises first-five-year interest from CAD 193,345 to CAD 196,837.

**Recommended follow-up:** obtain and reconcile missing evidence, verify the lender's actual criteria, and recalculate against a real property and current offered rate. Document any exception and its disposition. This portfolio exercise does not contact borrowers or collect private financial records.

## A separate data-quality finding

The source review also found a transposed payment in FCAC's public 4% example. The monthly cell says CAD 1,587.06; its total-interest figure implies CAD 1,578.06, matching the standard formula. The model retains the formula, tests other official examples and logs the discrepancy. Trusted sources still need reconciliation.

The [machine-readable review register](../data/processed/homebuying_bank_audit.csv) covers all nine baseline cases. The [SQL queries](../sql/homebuying.sql), [model](../src/homebuying_model.py), [tests](../tests/test_homebuying.py) and [methodology](homebuying_methodology.md) make the work reviewable.


## Review update: make the cash result interpretable

A zero cash shortfall means the minimum closing budget is covered. The Vancouver two-earner example has CAD 14,640 above that minimum, which is deployed toward the down payment. It is not unused money left after purchase.

The direct price check finds about CAD 690,000 within both financial checks at starting income and cash. At the unchanged benchmark price, about CAD 168,000 additional cash would instead be needed. These alternatives are model outputs with fixed assumptions, not approvals or spending recommendations.

The [calculation review](../reports/calculation_review.md) records independent budget, SQL and month-by-month loan checks. The [threshold table](../data/processed/homebuying_price_limits.csv) preserves exact values and scope.

## A calculation that produces a false pass

The separate worked audit uses the Vancouver couple at **CAD 764,100**, a 10% lower-price scenario. Correct income needed is CAD 167,429. Using the contract rate instead of the qualifying rate incorrectly gives CAD 141,543, making CAD 150,000 income appear sufficient.

The reviewer should trace the rate commitment, verify the applicable qualifying-rate rule and reperform the payment before sign-off. Other controlled omissions examine debt, property costs and the financed premium. A missing item can remain an error even when another constraint keeps the overall outcome unchanged.

These are defined demonstrations, not findings about an actual bank's files. [Full worked calculations and controls](../reports/mortgage_calculation_audit.md) · [All 585 rows](../data/processed/homebuying_calculation_audit.csv)
