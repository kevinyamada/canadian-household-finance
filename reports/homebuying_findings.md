# Why does buying a home still feel out of reach?

**Question: Is the down payment really the biggest obstacle to buying a home?**

**Answer:** not always. In four of nine buyer examples, cash covers the modeled purchase costs but gross income falls short of the mortgage screen. These are hypothetical examples, not a count of Canadian households.

## The example to remember

Two earners in Vancouver have **CAD 100,000 in cash** and **CAD 150,000 of annual gross income**. At the 2023 first-time-buyer transaction benchmark of **CAD 849,000**, they need **CAD 85,360** in minimum closing cash plus reserve. They pass that cash check.

With their remaining cash used toward the mortgage, the stressed debt-service screen requires **CAD 190,014 of gross income**. They are still **CAD 40,014 short each year**.

That is the problem a bank review needs to catch: being ready with the down payment does not establish that the mortgage fits.

## What changes the result?

For that same example, applied separately:

| Change | Remaining annual gross-income shortfall |
|---|---:|
| No change | CAD 40,014 |
| Home costs 10% less | CAD 17,429 |
| Home costs 20% less | CAD 0 |
| Mortgage rate 1 point lower | CAD 24,922 |
| CAD 25,000 more cash | CAD 32,879 |
| Gross income 20% higher | CAD 10,014 |
| 30-year amortization | CAD 30,070 |

Among these changes, a home priced 20% lower brings the example within both modeled financial limits. It does not establish a mortgage approval.

The three-city comparison also shows why one national answer is insufficient. The two-earner profile fits the modeled financial limits at the Victoria and Halifax benchmarks. The single-earner profile has enough cash in those two markets but remains income constrained.

## A direct price and cash answer

For the Vancouver two-earner example, about **CAD 690,000** fits the financial screen with starting cash and income fixed. Alternatively, keeping the benchmark price and income requires about **CAD 168,000 more cash**. The price display is rounded down and extra cash up to CAD 1,000. These alternatives are not spending recommendations or approvals.

The revised table shows cash/income above or below the requirement. The earlier zero cash shortfall correctly meant the minimum budget was covered; it hid the extra amount available for the down payment. [Read the recheck](calculation_review.md).

## What the further research found

**History:** between 2021 and 2023, higher transaction prices and mortgage rates increased the minimum-down income hurdle. Buyer-family income growth offset part of that change. In Vancouver, the exact input decomposition attributes approximately **+CAD 14,424** to price, **+CAD 27,144** to rates and **−CAD 20,000** to observed buyer-family income. These are descriptive contributions, not causal effects or matched-borrower outcomes.

**Later rates:** applying observed 2025 rate averages to unchanged 2023 prices reduces the income hurdle. It cannot establish whether observed 2025 affordability improved, because comparable later city buyer prices and incomes are not in the selected source.

**First-time-buyer measures:** a longer mortgage lowers the Vancouver example's monthly payment from **CAD 4,742 to CAD 4,367**, while first-five-year interest rises from **CAD 193,345 to CAD 196,837**. BC tax relief reduces closing cash; HBP uses existing RRSP wealth with future repayments. The FHSA example adds only a refund at an explicitly assumed tax rate. None is treated as free wealth, and none of these individual program changes clears the Vancouver example's income shortfall.

**Waiting:** with initially CAD 2,000 saved each month and rent rising 3% a year, the Vancouver two-earner example adds about **CAD 45,738** over two years. If prices stay flat, its required income falls to **CAD 178,220**. If prices rise 5% a year, the requirement instead reaches **CAD 199,572**. These are scenarios, not predictions or advice to buy now.

## The banking audit conclusion

**Hold the practice file.** The baseline income shortfall remains, and borrower/property evidence is missing. The working paper distinguishes a passed calculation from verified income, funds, debts, credit, valuation, costs and eligibility.

This is an independent review exercise informed by public OSFI B-20. It uses a common CMHC-style 39%/44% debt-service screen; actual uninsured lender criteria can differ. It does not reproduce TD's policies or assess an actual customer.

## What the project delivers

- 468 saved purchase scenarios across 2020–2023 inputs; nine latest-year baseline examples.
- 162 waiting scenarios, 36 program comparisons, nine later-rate replays and an exact historical input decomposition.
- A Python model, separate SQL reconciliation and source/rule checks.
- A seven-page imported Power BI report and an interactive GitHub Pages website.
- Seven shareable figures in PNG/SVG, a PDF, source tables and a mortgage audit working paper.

The prices and baseline rates are **2023**, not present-day quotes. Rules are reviewed November 16, 2026. Buyer finances, closing allowance, reserve and carrying costs are assumptions. City transaction medians do not represent identical homes or every renter.

[Explore the website](https://kevinyamada.github.io/canadian-household-finance/) · [Audit working paper](../docs/bank_audit_case.md) · [Methodology and sources](../docs/homebuying_methodology.md) · [Figure gallery](figures/homebuying/README.md)

## November 17 extension: newer rates and a worked audit

At the unchanged Vancouver benchmark, September 2026 rates change required income from CAD 190,014 to CAD 175,293. Income is still CAD 25,293 short. This holds the 2023 price/tax schedule and profile finances fixed; it is not observed current affordability.

A separate CAD 764,100 worked case needs CAD 167,429 income correctly. Qualifying at the contract rate incorrectly reduces that to CAD 141,543, creating a false pass. Four controlled mistakes are retained across 117 scenarios (585 correct/flawed rows); they do not measure a bank error rate.

[Source refresh and retrieval limits](source_refresh.md) · [Calculation audit](mortgage_calculation_audit.md) · [Interview brief](../docs/interview_brief.md)
