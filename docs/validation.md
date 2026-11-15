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
