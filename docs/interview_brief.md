# Interview brief

## Why does buying a home still feel out of reach?

**Question:** Is the down payment really the biggest obstacle to buying a home?

**Problem:** Enough cash to close does not establish that income supports the mortgage. A bank reviewer also needs trustworthy calculations and evidence.

**What I built:** Python and SQL analysis in desktop VS Code, an interactive GitHub Pages website and a native Power BI Desktop report. Observed benchmarks come from Statistics Canada and Bank of Canada; public government guidance supplies the rules. Buyer finances and costs are explicit assumptions.

**Finding:** Four of nine baseline examples meet minimum cash but fail the income screen. The Vancouver couple has CAD 14,640 above the minimum cash target but is CAD 40,014 short in annual income. About CAD 690,000 fits that profile's starting finances under the baseline assumptions.

**Refresh:** At unchanged prices and finances, 2026-09 mortgage rates reduce that couple's required income to CAD 175,293. The gap remains. This is a rate sensitivity, not current-market affordability.

**Banking audit:** A complete fictional file traces the application to income, funds, debt and cost worksheets. Seven discrepancies overturn the apparent pass. A lower-price request fits the corrected finances, while six external-evidence controls still prevent actual sign-off. The packet retains the findings, corrections and review conclusion.

**Validation:** Independent SQLite and loan-schedule reconciliations, financial boundary tests, website checks against saved outputs and native Power BI verification. The release validation report records completed checks.

**Recommendation:** Identify the binding cash/income constraint, reperform key calculations and hold sign-off until borrower, property and policy evidence supports the result.

**Limits:** Transactions and matched buyer income remain 2023 data in the latest reviewed release. Rates are national observations, not individual offers. Historical tax schedules and assumed costs remain. The examples are not a population sample. No TD customer data or internal policy is used.

## A short spoken introduction

“I asked why saving a down payment can still leave someone unable to buy. I separated cash from the mortgage-income requirement using official Canadian data. Four of nine examples had enough minimum cash but not enough income. I then reviewed a complete fictional application: corrected the input mismatches, tested a revised request and documented what still prevents sign-off. My recommendation is to identify the actual constraint and verify the evidence before calling a file ready.”

[Interactive project](https://kevinyamada.github.io/canadian-household-finance/) · [Worked audit](../reports/mortgage_calculation_audit.md) · [Source refresh](../reports/source_refresh.md)
