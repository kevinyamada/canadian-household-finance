# Open the housing-readiness audit

## Everyday viewing

Download **CanadianHouseholdFinance.pbix** from [v2.0.0](https://github.com/kevinyamada/canadian-household-finance/releases/tag/v2.0.0). Open it in a current Power BI Desktop on Windows. It includes its imported data; a Power BI service account is not needed.

The report has three pages: **Audit conclusion**, **Savings evidence** and **Purchase cash check**. In the cash check, choose one price and one closing allowance. CAD 600,000 and 2.5% produce CAD 35,000 minimum down, CAD 15,000 assumed costs and CAD 50,000 in the scenario.

The [v1.0.0 release](https://github.com/kevinyamada/canadian-household-finance/releases/tag/v1.0.0) preserves the earlier eight-page study.

## Rebuild from source

Close the editable project, then run `python src/build_powerbi.py` in the VS Code terminal. Open `powerbi/HouseholdFinance.pbip` and select Refresh to import the generated snapshot. Check the backed saving and cash visuals before exporting a regular PBIX.

Refresh in Desktop reloads the generated snapshot; it does not download new source releases. The regular PBIX is the viewing copy. The PBIP is for rebuilding and editing.

## Prompts

| Message | Meaning and action |
| :--- | :--- |
| View recovered files | Inspect or preserve recovery data before clearing the notice. Existing repair copies were preserved locally; recovery remains enabled. |
| Upgrade the model to TMDL | This is a source-format conversion, separate from an app update. The documented generator writes model.bim. Use the regular PBIX for viewing. |
| Tables have incomplete or no data | A new source project may not have imported its snapshot yet, or a refresh failed. Select Refresh and verify the data-backed visuals. |
| A newer Desktop version is available | Use Microsoft's [official download](https://www.microsoft.com/en-us/download/details.aspx?id=58494). |

[Three-minute demo](project_walkthrough.md) · [Audit brief](../reports/housing_audit.md) · [Validation record](validation.md)
