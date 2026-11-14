# Validation record

Checked on November 14, 2026 using Python 3.12 and Power BI Desktop 2.154.956.0 on Windows.

## Python and SQL

The full analysis ran in the VS Code terminal. The 11 automated tests cover complete quarterly grain, accounting identities, source snapshot hashes, rate joins, temporal separation, future data perturbation, validation based model selection, persistence predictions, scenario arithmetic and Power BI snapshot agreement.

The committed raw source files match their recorded SHA256 hashes. Git preserves those bytes through .gitattributes. The tested package versions are recorded in requirements-lock.txt. GitHub Actions repeats the pipeline, tests and Power BI schema checks on a clean checkout.

## Power BI Desktop

The project was opened and refreshed from its embedded snapshot. The overview showed 14.52% debt service, 2.06% income growth and 0.97% payment growth. The history displayed the full available period. The model page showed test MAE of 0.245 for persistence and 0.250 for the selected forest, with 80% interval coverage.

All 20 scenario combinations were checked against the generated Python table. Selecting payments +10% and income -2% reduced the matrix to 16.30%. Clearing both slicers restored the full matrix. The project was saved on the overview page.

Report JSON was checked against Microsoft schemas and visual field references were checked against the semantic model. Native Desktop checks are recorded separately because schemas cannot prove that DAX and Power Query execute correctly. Previews in reports/figures are cropped from the actual Desktop report.

## Scope of these checks

These checks establish internal consistency and successful execution. They do not establish real time forecasting performance, causal effects, or suitability for customer credit decisions. Revised historical data and national aggregation remain material limits. No Power BI service deployment was performed.
