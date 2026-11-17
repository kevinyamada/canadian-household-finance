# A three-minute project walkthrough

## Say this first

“I asked whether the down payment is really the biggest obstacle to buying a home. I compared purchase cash with mortgage income requirements using official Canadian data, then built a banking audit case.

In the Vancouver two-earner example, CAD 100,000 cash covers the minimum purchase budget, but CAD 150,000 annual gross income is about CAD 40,000 short of the mortgage screen. The direct price check suggests about CAD 690,000 would fit these starting finances under the assumptions.

The audit conclusion is to resolve the exception and verify the missing evidence before sign-off. A financial calculation alone cannot establish mortgage approval.”

Prices and baseline rates are 2023 benchmarks. Rules were reviewed November 16, 2026. The buyers and property costs are hypothetical.

## Website demo

1. Start with the coloured Canada map. Change the province and survey year. Explain that it measures renter housing need, independently of the mortgage examples.
2. Use Vancouver / Two earners / Baseline. Cash is CAD 14,640 above the minimum; annual income is CAD 40,014 short.
3. Select Price 20% lower. Income is now CAD 2,630 above the requirement. This is more informative than a zero shortfall.
4. Show the direct price limit and extra-cash alternative. They use the starting profile, separately from the selected scenario.
5. Finish with the banking audit: the arithmetic is checked, while borrower and property evidence is still missing.

The program cards show the variable each measure changes. Thirty years reduces the payment but increases first-five-year interest. HBP moves existing RRSP wealth; FHSA counts contributions once.

## Power BI demo

Use Start here, Cash and income, What helps, Price limits and Bank audit. The report also has history and waiting pages. All ten pages use imported data.

A positive position is above the requirement; negative is short. Price limits and audit working papers use the selected baseline.

## Technical follow-up

Show [the SQL](../sql/homebuying.sql), [threshold tests](../tests/test_homebuying_limits.py) and [calculation review](../reports/calculation_review.md).

Explain Canadian semiannual interest compounding, financed insurance, the stress test, and why tax/insurance boundaries make a single global search unreliable. The tests compare small domains exhaustively and verify each reported threshold at the next dollar.

Explain the limits: observed transaction medians, hypothetical borrowers, national mortgage-rate benchmarks, a geography-vintage boundary and unverified property costs. These do not establish a current price, an actual customer's qualification or comfortable spending.

[Findings](../reports/homebuying_findings.md) · [Audit working paper](bank_audit_case.md) · [Methodology](homebuying_methodology.md)

## Two additions for a banking interview

Show Latest rates: the same Vancouver price and finances still leave CAD 25,293 annual income short under September 2026 rates. Explain why a new rate does not make an old transaction price current.

Then show Calculation audit, choosing Vancouver / Two earners / Price 10% lower. The wrong qualifying rate creates a false pass. Explain which source document and recalculation a reviewer should require.

[Short interview brief](interview_brief.md) · [Full calculation audit](../reports/mortgage_calculation_audit.md) · [Source refresh](../reports/source_refresh.md)

## Complete-file demo

Open File review (Power BI) or the complete mock-file section (website). Follow Submitted claim → Corrected review → Revised request. Explain the one-off bonus, pledged funds and omitted debt. Show why the corrected original request fails, and why financial fit after a lower-price request still does not authenticate real evidence. Use [the eight-page packet and walkthrough](mortgage_file_walkthrough.md).
