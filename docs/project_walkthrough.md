# The project in plain language

**Why does buying a home still feel out of reach?**

This project examines one part of that problem: whether a financial report's saving figures and upfront-cost assumptions actually support a claim that renters are ready to buy.

## What I did

I used Statistics Canada data to reconcile reported renter saving with income, consumption and pension adjustments. I checked all four quarters before calculating annual totals. Then I built a transparent down-payment and closing-allowance scenario and a register of deliberately drafted claims.

The key example is simple: positive saving of CAD 269 in 2025Q4 did not establish deposit cash. It included a pension adjustment. The full-year sum was negative CAD 557 per household.

The product is an audit trail in Python, SQL and Power BI. It shows the evidence, corrects the interpretation and records the information needed before calling a buyer ready.

## Three-minute demo

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
