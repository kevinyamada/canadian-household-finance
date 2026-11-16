# Open the dashboard without the project-format prompts

## Everyday viewing

Use **CanadianHouseholdFinance.pbix** from the project's [GitHub Releases](https://github.com/kevinyamada/canadian-household-finance/releases). Open it in a current Power BI Desktop version. It includes the imported snapshot and opens on Key insights. A Power BI service account is not required to view these local pages.

The eight pages show the findings, household groups, reporting checks, AI review, national trends, forecast comparisons, scenarios and the neural experiment. Start with the four conclusions and their next actions, then use the detail pages to inspect the evidence.

## Rebuilding from source

The editable project is `powerbi/HouseholdFinance.pbip`. Close Power BI before running the Python pipeline. Reopen the project and select Refresh to import the generated snapshot. Then use File → Save as and choose the Power BI `.pbix` file type to create the everyday viewing copy.

Refresh in Desktop reloads the embedded snapshot. It does not download new StatCan releases. The Python pipeline handles source updates; `run.py --refresh` deliberately changes the study vintage, so review the conclusions after using it.

## What the prompts mean

| Message | Meaning | What to do |
| :--- | :--- | :--- |
| View recovered files | Power BI found recovery data from a previous session | Inspect or preserve the recovery copy before clearing the notice. During this repair, existing copies were preserved under the local ignored `.powerbi_cache_backup` folder. Recovery remains enabled. |
| Upgrade the semantic model to TMDL | The editable project can be converted to a newer model file format | This is a project-format choice. The Python generator currently writes `model.bim`; keep that source format for the documented rebuild workflow. Use the regular `.pbix` for everyday viewing. |
| Some tables have incomplete or no data | A newly generated project has not yet loaded its embedded snapshot, or a refresh failed | Select Refresh and check that it completes. A failed refresh needs investigation; a screenshot of the text-only summary alone does not establish that the detail pages work. |
| A newer Power BI Desktop version is available | The installed application has a newer supported release | Use Microsoft's [official download](https://www.microsoft.com/en-us/download/details.aspx?id=58494). App updates and project-format conversion are different actions. |

Keep the source project and the everyday copy separate in your workflow: rebuild the project with Python, verify it in Desktop, then export a fresh `.pbix`. The binary viewing file is distributed as a release asset; source code and validated data remain in Git.

[Four findings and actions](../reports/key_insights.md) · [Next-step plan](next_steps.md) · [Validation record](validation.md)
