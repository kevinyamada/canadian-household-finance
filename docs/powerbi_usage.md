# Open the Power BI report

1. Download [HomebuyingBarriers.pbix](https://github.com/kevinyamada/canadian-household-finance/releases/download/v3.0.0/HomebuyingBarriers.pbix).
2. Open it in a current **Power BI Desktop** for Windows.
3. Begin on **Start here**, then use **Cash and income** to change the city, buyer and one assumption.

The regular .pbix file contains its imported data. It does not need the author's source folders or a Statistics Canada download to display the results. A Power BI Service subscription is not needed for this local report.

## Pages

- **Start here:** the question, main finding and nine hypothetical buyer examples.
- **Cash and income:** select one city, one buyer and one scenario; inspect cash, income and monthly costs.
- **What helps:** compare one change at a time and review buyer measures.
- **Over time:** observed 2020–2023 inputs with current rules held fixed.
- **Waiting to buy:** 12/24-month scenarios under three price paths and selected rent growth.
- **Bank audit:** calculation results and evidence still needed before sign-off.

The audit page reviews the selected buyer's baseline, independently of a scenario chosen on another page. The history page is a market comparison at minimum down, not the selected buyer's personal income.

## About the figures

Prices and baseline rates are **2023**, the latest comparable city observations in the selected Statistics Canada source. They are not 2026 quotes. Rules are reviewed November 16, 2026. Buyer finances and property costs are assumptions.

“Within modeled limits” is not approval. The comparison uses a CMHC-style 39% GDS/44% TDS screen; an uninsured lender may apply different criteria. All fictional audit files remain on hold pending evidence.

## If Power BI asks for folders or an update

Check the filename: use the release **HomebuyingBarriers.pbix**. Older intermediate .pbit templates and editable .pbip source projects have different opening behaviour.

The release is exported and reopened in native Power BI Desktop with an imported DataModel. Its data does not use local File.Contents paths. If your installed Desktop cannot read the file format, update using the official [Microsoft Power BI Desktop download](https://www.microsoft.com/en-us/power-platform/products/power-bi/desktop). The release notes record the version used for verification.

You do not need to choose “Get data” or browse for CSV files to inspect the report.

## Editable source

Open powerbi/HomebuyingBarriers.pbip from the cloned repository. It links to the sibling .Report and .SemanticModel folders. Keep those folders together.

To rebuild from saved official extracts, run the commands in the [methodology](homebuying_methodology.md) from desktop VS Code, then open the project and refresh. In the editable project, select one city, buyer and scenario on Cash and income; guarded measures intentionally stay blank if the selection does not identify one case.

The older [v2.0.0 renter-saving audit](https://github.com/kevinyamada/canadian-household-finance/releases/tag/v2.0.0) remains archived separately.
