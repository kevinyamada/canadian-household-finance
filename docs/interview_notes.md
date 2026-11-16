# Interview notes

## Headline

**Why does buying a home still feel out of reach?**

The technical work audits the saving figures and upfront-cost assumptions behind a homebuying-readiness claim. It does not model every cause of housing affordability.

## The problem and solution

A report can have correct arithmetic and an unsupported conclusion. Published net saving includes pension entitlements, so it does not establish money available for a deposit. A single quarter also does not establish a full-year saving rate.

I built source and period checks, an independent SQL reconciliation, a versioned purchase-rule calculation and a claim register. Power BI follows the audit from conclusion to evidence and cash scenarios.

## Questions to prepare for

**What is the main finding?** Reported renter net saving was positive CAD 269 in 2025Q4, but its components were −572 income less consumption and +841 pension adjustment. The four-quarter sum of reported saving was −557 for 2025. Neither figure proves a renter's liquid funds.

**Why does a bank care?** An analyst reviewing a housing-readiness report needs to know which conclusions are supported before using it for decisions. The audit makes the source definitions, assumptions and missing evidence visible.

**Is this a real audit opinion?** No. It demonstrates reporting controls and review of deliberately drafted claims using real public data. It does not allege fraud or misstatement by Statistics Canada or a bank.

**Why use four quarters?** The source is not seasonally adjusted. I sum the four observed quarterly household estimates and reject incomplete years. I do not multiply one favorable quarter by four.

**What does the purchase example show?** At CAD 600,000, the minimum down payment is 25,000 on the first 500,000 plus 10,000 on the balance. An assumed 2.5% closing allowance adds 15,000. That is an illustrative 50,000 upfront-cash scenario, not a complete closing statement.

**Can you say whether a particular renter should buy?** No. Verified liquid funds, gross income, debts, credit, property costs and loan terms are not observed. Group averages cannot establish an individual's eligibility.

**How do you know the calculation works?** Tests cover the price-tier boundaries, invalid inputs, missing quarters, saving reconciliation, SQL/Python agreement and the data embedded in Power BI.

**Why are the report tables separate?** Annual estimates, quarter observations, claim checks and hypothetical purchase cases have different grains. I keep the evidence and assumptions separate to prevent invalid joins or totals.

**Where do the GPU experiments fit?** Earlier saved H100 work tested AI review of deliberately misleading financial excerpts. It is supporting evidence about a controlled prototype, not production audit reliability. It is not needed for the main calculation, and no new paid run was launched for this update.

## Resume bullets

- Built a financial-reporting audit with Python and SQLite to reconcile 24 quarters of Statistics Canada renter data, validate annual saving totals and check purchase-price rules.
- Created a three-page Power BI report and an interactive Canadian housing website with provincial comparisons, purchase-cash scenarios, published figures and 57 automated tests.

Project link: https://kevinyamada.github.io/canadian-household-finance/

## What to practise before an interview

Explain the question and recommendation in 30 seconds without reading. Then use the three-minute Power BI walkthrough. Be ready to explain the difference between reported saving, income less consumption and verified cash.

For a technical follow-up, show one SQL reconciliation, one rule-boundary test and the source record. Use the map to discuss coverage and uncertainty. The provincial survey, national accounts and hypothetical purchase cases have different definitions and periods.

## Skills to demonstrate

Python preparation and controls, SQL aggregation and reconciliation, source lineage, accounting definitions, rule boundaries, explicit missing evidence and clear Power BI communication.

Understand the scripts and limits before presenting. Describe assistance honestly if asked.

[Three-minute walkthrough](project_walkthrough.md) · [Method and sources](methodology.md)
