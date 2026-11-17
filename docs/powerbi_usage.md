# Open the Power BI report

1. Download [HomebuyingBarriers.pbix](https://github.com/kevinyamada/canadian-household-finance/releases/download/v3.2.0/HomebuyingBarriers.pbix).
2. Open it in a current Power BI Desktop for Windows.
3. Begin on **Start here**, then change the city, buyer and assumption on **Cash and income**.

The regular .pbix contains imported data. It does not need the author's source folders or a Statistics Canada download to display results. A Power BI Service subscription is not needed for this local report.

## Nine pages

- **Start here:** the question, finding and nine hypothetical buyer examples.
- **Cash and income:** money available, required amounts and signed positions.
- **What helps:** scenario comparisons and the main effect of buyer measures.
- **Price limits:** a price within both checks, or extra cash at the benchmark price.
- **Latest rates:** September 2026 monthly mortgage rates on the unchanged 2023 price, finances and tax schedule.
- **Calculation audit:** correct and four deliberately flawed calculations, with false passes identified.
- **Over time:** observed 2020–2023 inputs with current rules held fixed.
- **Waiting to buy:** 12/24-month scenarios with three price paths and rent growth.
- **Bank audit:** calculation results and evidence still needed before sign-off.

A positive cash/income position is above the requirement; negative is short. Cash above the minimum goes toward the down payment, while the stated reserve stays aside. It is not cash left after purchase.

The price-limit and audit pages review the selected baseline, independently of a scenario selected elsewhere. Price displays are rounded down and extra cash up to CAD 1,000.

## Scope

Prices and baseline rates are 2023 benchmarks, not current listings or offered rates. Rules were reviewed November 16, 2026. Buyer finances and costs are assumptions.

Passing both financial checks is not approval or a comfortable spending budget. The comparison uses a CMHC-style 39%/44% debt-service screen; uninsured lender criteria can differ. The fictional files still need verified evidence.

## If Power BI asks for folders or an update

Use the release **HomebuyingBarriers.pbix**. Earlier intermediate .pbit templates and editable .pbip projects have different opening behaviour.

The release contains a native imported DataModel. Its data do not use local File.Contents paths. If an older Desktop cannot read the format, use the official [Power BI Desktop download](https://www.microsoft.com/en-us/power-platform/products/power-bi/desktop). Release notes record the tested version.

You do not need to choose Get data or browse for CSV files to inspect the report.

## Editable source

Open powerbi/HomebuyingBarriers.pbip with its sibling .Report and .SemanticModel folders together. To rebuild, use the [methodology](homebuying_methodology.md) commands in desktop VS Code, then open and refresh the project.

Select one city, buyer and scenario on Cash and income. Guarded measures stay blank if the selection does not identify one case.

[Calculation review](../reports/calculation_review.md) · [Exact price/cash thresholds](../data/processed/homebuying_price_limits.csv)

For the calculation-audit example, select Vancouver / Two earners / Price 10% lower. Correct income needed is CAD 167,429; incorrectly using the contract rate gives CAD 141,543 and creates a false pass. This page uses its own scenario selection. Newer rates are a separately labeled sensitivity, not current-market affordability.
