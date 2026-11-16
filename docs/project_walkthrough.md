# The project in plain language

**Why does buying a home still feel out of reach?**

This project examines one part of that problem: whether a financial report's saving figures and upfront-cost assumptions actually support a claim that renters are ready to buy.

## What I did

I used Statistics Canada data to reconcile reported renter saving with income, consumption and pension adjustments. I checked all four quarters before calculating annual totals. Then I built a transparent down-payment and closing-allowance scenario and a register of deliberately drafted claims.

The key example is simple: positive saving of CAD 269 in 2025Q4 did not establish deposit cash. It included a pension adjustment. The full-year sum was negative CAD 557 per household.

The product is an audit trail in Python, SQL and Power BI. It shows the evidence, corrects the interpretation and records the information needed before calling a buyer ready.

## One-minute website demo

Open the [project website](https://kevinyamada.github.io/canadian-household-finance/).

1. Select a province on the map. Explain that core housing need measures renter pressure, with published survey uncertainty. It does not measure a buyer's deposit.
2. Show 2025 on the national budget graph: income was below consumption by CAD 3,570. The accounting measures are not a bank-account budget.
3. Select a CAD 600,000 purchase. At a 2.5% assumed closing allowance the scenario needs CAD 50,000; at 4% it needs CAD 59,000. Those are transparent assumptions, not mortgage approval.
4. State the audit action: verify funds, the full purchase budget and eligibility before calling someone ready to buy. Use the [published figures](../reports/figures/portfolio/README.md) when a live demo is unavailable.

## Three-minute Power BI demo

Open the focused v2.0.0 `CanadianHouseholdFinance.pbix` in Power BI Desktop.

| Time | Page | What to explain |
| :--- | :--- | :--- |
| First minute | Audit conclusion | State the problem: a saving headline is not verified deposit money |
| Second minute | Savings evidence | Reconcile −572 + 841 = 269, then explain why the full-year total is −557 |
| Third minute | Purchase cash check | Select CAD 600,000 and 2.5%; show 35,000 down + 15,000 assumed closing allowance = 50,000 in the scenario |

Keep the scope clear: the price and allowance are assumptions, the data are group averages, and a cash scenario is not mortgage approval.

## Thirty-second interview explanation

> I built an audit project around the financial claims used to describe homebuying readiness. A positive saving figure could be mistaken for money available for a deposit, so I reconciled the public renter data, checked the full year and tested the purchase-cost calculation. Python and SQL produce the audit trail, and Power BI lets someone inspect the evidence and assumptions. The result shows what must be corrected or verified before a readiness claim can be trusted.

[Interview questions](interview_notes.md) · [Problem statement](problem_statement.md) · [Audit brief](../reports/housing_audit.md)
