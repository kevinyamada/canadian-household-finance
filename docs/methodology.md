# Methodology

## Question

How has the payment burden of Canadian households changed, and can a model improve an estimate of the next unpublished quarter? A retail banking analytics team could use the result to decide which aggregate indicators need closer review. This is a public data portfolio project and has no affiliation with TD.

## Data contract

One row is one Canadian calendar quarter. The source is Statistics Canada table 11-10-0065-01, filtered to Canada and seasonally adjusted at annual rates. The pipeline selects 13 named indicators, checks duplicate keys and missing values, and checks units before pivoting. Original zip bytes and metadata are kept with SHA256 hashes.

Ratios are reported in percent, so a move from 14.68 to 14.52 is a decrease of 0.16 percentage points. Dollar series are CAD millions at annual rates. Income is disposable income before interest payments. The reported ratio is rounded to two decimals; accounting checks allow 0.0051 percentage points of rounding error.

Bank of Canada V39079 is the business daily policy target rate. Its available history in this download starts in 2009. The last observed business day in each quarter supplies the contextual rate. It is left joined through SQLite. Missing earlier policy rates stay missing. Rates are never backfilled and are not used by the primary model.

## Forecast protocol

Features from quarter t predict the change in the debt service ratio from t to t+1. The features are the current ratio, its changes over one, two and four quarters, quarterly income and payment growth, the mortgage share of payments, and the interest share of payments. The target level is recovered by adding the predicted change to the current ratio.

Initial training uses earlier complete observations. The selection period is 2007Q1 through 2018Q4. Every validation prediction uses an expanding training window with the last observed target no later than its origin quarter. All scaling is fitted within that window.

Candidate settings are fixed before evaluating the final test: persistence, drift equal to the last four quarter change divided by four, ridge with alpha 1, 10 or 100, and a random forest with 160 trees, maximum depth 3, minimum leaf size 8 and seed 469. A deliberately small search is appropriate for 146 quarterly observations.

The candidate with the lowest selection period MAE is frozen before testing. The final test starts in 2019Q1. It compares that selected candidate with the two simple baselines. Parameters are refitted as each actual quarter becomes observable, but the model family and settings are not retuned using test errors. Random train/test splitting would violate time order here.

MAE and RMSE are in percentage points. Bias is predicted minus actual. A sensitivity result removes 2020Q2 and 2020Q3, but the main score includes both. This cut diagnoses shock sensitivity and is not used to select a model.

## Uncertainty

A nominal 90% symmetric calibration band uses the finite sample adjusted 90th percentile of the selected model's absolute validation errors. The calibration period was also used for selection, and time series errors are dependent, so this is an empirical band without a conformal coverage guarantee. Actual test coverage is reported.

A circular moving block bootstrap uses four quarter blocks and 4,000 replicates to describe uncertainty in the mean paired MAE difference from persistence. It is descriptive, depends on the block choice, and has limited power with only 30 test quarters. It does not establish future performance or a causal effect.

## Accounting decomposition

For payments P and income I, R = 100P/I. The payment contribution between periods 0 and 1 is 50(P1 − P0)(1/I0 + 1/I1). The income contribution is 50(P0 + P1)(1/I1 − 1/I0). Their sum equals R1 − R0. This is the symmetric average of the two possible orders of changing the inputs.

## Limits that affect interpretation

This is a revised vintage retrospective evaluation. Archived releases are not available in the project. Data for quarter t are normally released during t+1, so the next quarter estimate is a nowcast of the next unpublished quarter. Historical real time forecast accuracy could be different.

The national aggregate is not the average of individual household ratios. It cannot identify vulnerable borrowers, estimate default, measure TD portfolio risk, or support individual credit decisions. Policy rate movements are contextual and do not identify a causal payment effect. Scenario shocks are transparent accounting assumptions.
