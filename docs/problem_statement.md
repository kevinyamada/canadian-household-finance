# The problem this project answers

A retail banking analytics team sees a lower national debt service ratio. Before calling that an improvement, it needs to know whether households are making smaller payments or whether income is simply growing faster. It also needs to decide whether a forecasting model adds enough information to use alongside the latest published figures.

## Main question

Is Canadian household payment pressure easing, what explains the change, and can a model improve the estimate of the next unpublished quarter?

The intended user is an analyst preparing an aggregate household finance update. The decision is which indicators deserve closer review and whether a model adds useful evidence. This project does not make lending decisions or estimate individual default probabilities.

## What would count as a useful answer?

| Question | Evidence | Decision it supports |
| :--- | :--- | :--- |
| Did pressure ease? | Latest debt service ratio and quarterly change | Describe the national direction |
| Why did it change? | Exact payment and income decomposition | Distinguish payment relief from income growth |
| Does the total hide something? | Mortgage and other debt components | Identify the component requiring closer review |
| Can a model help? | Time ordered MAE against persistence, uncertainty and stability | Decide whether to retain the simple benchmark |
| What if conditions worsen? | Explicit payment and income scenarios | Show sensitivity without pretending to predict policy effects |

## Answer from the original analysis

The ratio fell to 14.52% in 2026Q2 because income grew faster than payments. Payments still rose. The mortgage component also remains above its 2019Q4 level even though the overall ratio has eased. A lower national ratio is therefore not evidence that mortgage pressure has disappeared.

The selected random forest had a test MAE of 0.250 percentage points, compared with 0.245 for persistence. The original evidence does not justify replacing that simple benchmark. The Modal experiment also tested a neural alternative. Its MAE was 0.387, so it did not change the recommendation. These GPU results are reported separately as an exploratory extension.

## How an analyst would use it

At each release, refresh the inputs and check the data quality report. Review the headline ratio together with payment growth, income growth and borrowing components. Use the scenarios to explain how assumptions change the ratio. Escalate questions for portfolio analysis when the national total and mortgage component move differently.

A useful next step would require approved loan level data on renewal dates, balances, income and repayments. That is where the analyst could test whether aggregate patterns describe the bank's own borrowers. This project does not claim to have that evidence.
