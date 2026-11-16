# Validation record

Original analysis checked on November 14, 2026; GPU extension checked on November 15, 2026 using Python 3.12 and Power BI Desktop 2.154.956.0 on Windows.

## Python and SQL

The full analysis ran in the VS Code terminal. The 16 automated tests cover complete quarterly grain, accounting identities, source snapshot hashes, rate joins, temporal separation, future data perturbation, validation based model selection, persistence predictions, scenario arithmetic and Power BI snapshot agreement. Added checks verify GPU training inputs, future data isolation, configuration selection, reconstruction from saved seeds and runtime cost arithmetic.

The committed raw source files match their recorded SHA256 hashes. Git preserves those bytes through .gitattributes. The tested package versions are recorded in requirements-lock.txt. GitHub Actions repeats the pipeline, tests and Power BI schema checks on a clean checkout.

## Power BI Desktop

The project was opened and refreshed from its embedded snapshot. The overview showed 14.52% debt service, 2.06% income growth and 0.97% payment growth. The history displayed the full available period. The model page showed test MAE of 0.245 for persistence and 0.250 for the selected forest, with 80% interval coverage.

All 20 scenario combinations were checked against the generated Python table. Selecting payments +10% and income -2% reduced the matrix to 16.30%. Clearing both slicers restored the full matrix. The project was saved on the overview page.

Report JSON was checked against Microsoft schemas and visual field references were checked against the semantic model. Native Desktop checks are recorded separately because schemas cannot prove that DAX and Power Query execute correctly. Previews in reports/figures are cropped from the actual Desktop report.

## Modal extension

Eight H100 workers completed the bounded experiment. Saved predictions were converted losslessly to compressed NumPy arrays, with exact equality checks. Reprocessing requires no GPU calls. The selected ensemble had MAE 0.387 and empirical interval coverage 70%. The fourth Power BI page was refreshed and checked against these results. The main runtime estimate is US$10.09 in GPU charges; this is not a verified invoice. Modal reported no running apps after completion.

## Scope of these checks

These checks establish internal consistency and successful execution. They do not establish real time forecasting performance, causal effects, or suitability for customer credit decisions. Revised historical data and national aggregation remain material limits. No Power BI service deployment was performed.

## Household groups and reporting controls

The November 15 extension joins Statistics Canada tables 36-10-0662, 0660 and 0664 at quarter and household group grain. All source key sets agree before merging. The panel contains 936 rows across 39 groups and 24 quarters. Structural missingness in joint income and age pension and saving cells remains missing.

The latest tenure rows pass all six controls. Deliberate corruptions verify that duplicates, missing values, zero denominators, incorrect saving, incorrect assets and changed published ratios are caught. Same quarter prior year comparisons and the pension adjustment example are tested explicitly. Source ZIP hashes match the saved manifest.

Power BI Desktop was refreshed and the household groups page was checked against Python values. The reporting controls page shows five passing checks and one review status containing fourteen historical CAD 3 differences. The renter example displays income 18,326, consumption 18,898, pension adjustment 841 and net saving 269. Native report previews are saved as 13_powerbi_groups.png and 14_powerbi_controls.png.

The initial six page report passed 56 schema checks. The AI reviewer scorer separately tests strict boolean parsing, deterministic rule coverage and the treatment of abstentions. The full inference inputs and protocol were frozen in commit 00953ab before running the comparison.


## Completed reporting review and project handoff

On November 15, 2026 the full Python and SQL pipeline ran again in the desktop VS Code terminal using the saved source snapshots and completed Modal outputs. No additional GPU inference was launched for this validation. All **28 tests passed**, and **63 Power BI JSON files** passed their Microsoft schema checks with valid semantic field references. The checks also confirmed that every benchmark evidence value agrees with the StatCan group panel and the frozen input digest.

The saved review experiment contains eight H100 model and prompt configurations. Development data selected Qwen3-32B with the checklist prompt. Evaluation covers 1,456 unique 2024 and 2025 excerpts across five matched repetitions. The selected reviewer flagged all deliberately unsupported excerpts and had a 1.40% false alarm rate on supported excerpts. These are controlled, balanced template cases; they do not establish reliability on arbitrary real reports or superiority over a comprehensive rules baseline.

The seven-page report was loaded and refreshed in Power BI Desktop. Each page's expected heading and visual state was checked, and cropped native previews were saved in reports/figures. The AI page shows detection, false alarms and abstentions. Selecting payments +10% and income -2% returned **16.30%** in the actual Desktop matrix. Both selections were cleared after checking. The household groups page is the starting point for the interview demo.

The completed runs imply approximately US$10.09 for the earlier neural experiment and US$20.02 for the reporting review experiment in GPU runtime at list price. These are estimates rather than invoices and exclude other usage charges. Reproducing the committed analysis uses saved outputs and does not launch paid Modal work.

The [plain-language walkthrough](project_walkthrough.md) gives the main question, renter arithmetic and a five-minute dashboard demo. GitHub Actions repeats the pipeline, tests and report schema validation on a clean Linux checkout.


## Clear insights and the regular Power BI viewing file

The clarity update adds an opening Key insights page and a generated written brief. Four conclusions have a reference period, measured evidence and an analyst action. The same validated outputs generate the Python summary figure, JSON evidence and Power BI text. Four additional tests check source agreement, date labeling, changed saving and model evidence, and agreement between the opening page and the saved outputs.

The analysis and final packaging checks ran in the local VS Code terminal: **32 Python tests** and **71 source-report schema checks** passed. The upload will use these local results and skip a new hosted analysis run.

Power BI Desktop was updated from 2.154.956.0 to **2.159.1231.0** using Microsoft's signed installer. Two recovery files were preserved in the local ignored backup folder before the notice was cleared; recovery remains enabled. The regular CanadianHouseholdFinance.pbix includes its imported DataModel and eight report pages. It was reopened and saved without a recovery notice or TMDL model-format prompt. The loaded mortgage-owner ratio matched 306.1%, and the interactive payments +10% / income -2% scenario returned **16.30%**. Both selections were cleared and Key insights was restored. A desktop shortcut opens the regular viewing file.

The newer Desktop wrote source metadata with a schema version whose public URL was unavailable during validation. The Python generator regenerated the editable source with published schemas, which passed the 71 checks. The native PBIX is a separately checked viewing artifact; its hash and validation details are in reports/viewing_copy_manifest.json.

The README's opening figure is a labeled **Python-generated insight summary**. Previously validated native detail-page previews were retained when newer desktop captures were blank. Blank captures were excluded from the deliverables. Native data, scenario and prompt checks were performed independently of image capture.
