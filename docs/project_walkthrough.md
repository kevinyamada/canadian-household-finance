# A three-minute project walkthrough

## Say this first

“I asked whether the down payment is really the biggest obstacle to buying a home. I used Statistics Canada city transaction data, modeled both purchase cash and mortgage income requirements, and built a reviewable bank audit case.

In my Vancouver example, two earners have CAD 100,000 in cash and CAD 150,000 of annual income. Their cash covers the modeled purchase costs, but income is about CAD 40,000 short of the stressed mortgage screen. A lower rate helps; a 20% cheaper home clears both modeled financial checks.

The audit recommendation is to hold the example file, resolve the income gap and verify the missing evidence. A cash-ready calculation is not a mortgage approval.”

Prices and baseline rates are 2023 benchmarks. Rules were reviewed November 16, 2026. The buyers are hypothetical.

## Website demo

1. Open the [site](https://kevinyamada.github.io/canadian-household-finance/). The default case is Vancouver / Two earners / Baseline.
2. Point to the separate cash and annual gross-income bars. Explain why CAD 100,000 cash can coexist with a CAD 40,014 income shortfall.
3. Choose **Price 20% lower**. Both modeled checks fit. Return to Baseline.
4. Open **Would this mortgage file pass a first review?** Show the income exception and missing evidence.
5. If there is time, show a different city and the waiting chart. Explain that paths are scenarios, not price forecasts.

## Power BI demo

Start on **Start here** for the finding and nine cases. On **Cash and income**, select one city, buyer and scenario. Use **What helps** for one-change comparisons, then finish on **Bank audit**.

The audit page reviews the selected baseline, not a scenario selected elsewhere. The six pages contain imported data and do not need the author's local folders.

## Technical follow-up

Show [the SQL](../sql/homebuying.sql) and one [boundary test](../tests/test_homebuying.py). Explain semiannual interest compounding, financed insurance, the stress-test rate and why property assessment is an assumption.

Explain the source grain: city first-time-buyer transaction medians, hypothetical borrower profiles, national mortgage-rate benchmarks, and a geography-vintage boundary in 2020. These cannot establish an actual borrower's income, a matched-house price trend or current loan approval.

[Findings](../reports/homebuying_findings.md) · [Audit working paper](bank_audit_case.md) · [Methodology](homebuying_methodology.md)
