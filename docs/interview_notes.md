# Interview notes

**Why does buying a home still feel out of reach?**

The focused question is whether the down payment is really the biggest obstacle. The project compares cash and income constraints, then turns one example into a banking audit working paper.

## Main point

Four of nine hypothetical buyer cases have enough cash but insufficient income under the screen. In the Vancouver two-earner example, CAD 100,000 cash covers a CAD 85,360 target, while CAD 150,000 income falls CAD 40,014 short. These are illustrative cases, not population estimates.

## Why a bank such as TD might care

Mortgage review needs calculations that another reviewer can reproduce, explicit exceptions and verified evidence. The project shows how a report can pass a cash check while failing an income screen. It records missing documents and an appropriate hold conclusion.

It does not use TD's internal policy, client records or endorsement. The 39%/44% ratios are a common CMHC-style comparison; uninsured lender rules can differ.

## Questions to prepare for

**Why did you choose these cities?** The selected Statistics Canada sources support comparable first-time-buyer measures for Vancouver City, Victoria City and Halifax Regional Municipality. I did not combine a city with a CMA or substitute an unrelated Toronto measure.

**Why is the price year 2023?** It is the latest comparable observation in the selected source, released in 2026. I label it clearly instead of presenting it as today's price.

**What is actually observed?** City buyer-based transaction medians and buyer-family incomes, national mortgage rate series and published tax schedules. Borrower finances, costs and program eligibility are assumptions.

**How is the mortgage calculated?** Fixed-rate semiannual compounding converted to monthly payments, financed insurance where applicable, and qualification at max(contract + 2 percentage points, 5.25%). Taxes, heat, half condo fees and other debt enter the debt-service screen.

**What does more cash change?** It first covers closing costs and the reserve; excess cash reduces the loan. At insurance tier boundaries, premiums can change discontinuously. Cash and income are related, but they are not the same constraint.

**What solves the Vancouver example?** A 20% cheaper purchase fits both modeled financial limits. A one-point rate cut, CAD 25,000 extra cash or a 30-year mortgage alone leaves an income shortfall. This is conditional analysis, not a prediction of a price decline.

**Why not recommend waiting?** Saving helps, but a rising target price or rent can offset it. I compare explicit paths without pretending to know their probabilities.

**What is the bank audit result?** Hold the fictional file. Resolve the modeled income exception and verify funds, income, debts, credit, property costs and eligibility. A mathematical pass is not verified approval.

**How did you validate it?** Independent SQL reconciles every purchase case. Tests cover official mortgage examples, down-payment and insurance boundaries, source flags, joins, program accounting, waiting scenarios and asset hashes. Native Desktop checks change the selected buyer and reopen the exported .pbix.

**Did you find a source issue?** FCAC's 4% monthly-payment cell has transposed digits relative to its own total interest and the standard formula. I retained the discrepancy and tested other official examples instead of changing the formula to fit a typo.

**Where do the older models fit?** Earlier saved forecast/GPU experiments are supporting work, not the main homebuying result. This extension required no new paid GPU run.

## Resume bullets

- Built a Canadian homebuying study using Python, SQL and official public data to compare cash and mortgage-income constraints across three cities, 468 purchase scenarios and 162 waiting scenarios.
- Created a ten-page Power BI report, interactive GitHub Pages website and an OSFI-informed mortgage audit working paper that separates checked calculations, policy assumptions and missing evidence.

Use wording you can explain in your own words. Describe assistance honestly if asked.

[Live project](https://kevinyamada.github.io/canadian-household-finance/) · [Three-minute demo](project_walkthrough.md) · [Methodology](homebuying_methodology.md)

## Why did the comparison show zero cash shortfalls?

The shortfall was floored at zero. It showed only money missing, so it hid the effect of extra cash in an already-funded example. I now show cash and income above or below the requirement, and program cards show the variable the program changes.

The direct price/cash search handles tax and insurance boundaries. It is checked against exhaustive small domains, including a disconnected feasible set. See the [calculation review](../reports/calculation_review.md).

## Current interview brief and follow-up questions

Use [the short interview brief](interview_brief.md) for the spoken introduction. The new [worked audit](../reports/mortgage_calculation_audit.md) shows a defined mistake that changes the financial-screen result.

- Why keep 2023 data? The latest reviewed matched city-buyer release still uses 2023 sales and income. Newer mortgage rates are a separate sensitivity.
- Why does missing debt sometimes leave the income requirement unchanged? The GDS constraint may still bind. An unchanged outcome does not validate a missing input.
- What did the deliberate errors prove? Their financial effect in the saved examples, not the error frequency at TD or any bank.
- What would a real lender need? Verified income, source of funds, debt records, property value/costs, eligibility and its actual underwriting criteria.

## Complete-file demo

Open File review (Power BI) or the complete mock-file section (website). Follow Submitted claim → Corrected review → Revised request. Explain the one-off bonus, pledged funds and omitted debt. Show why the corrected original request fails, and why financial fit after a lower-price request still does not authenticate real evidence. Use [the eight-page packet and walkthrough](mortgage_file_walkthrough.md).
