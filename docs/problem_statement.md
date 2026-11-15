# The problem this project answers

A banking analyst preparing a household finance update needs to know what the national average hides. A lower payment ratio does not mean that every group is doing better, and positive net saving does not necessarily mean income exceeds consumption.

## Main question

Which household groups show different forms of financial pressure, and can reporting controls prevent misleading conclusions about those groups?

The intended user is an analyst reviewing an aggregate financial report. The decision is what to investigate further and which statements need correction before the report is used. This project supports monitoring and reporting review. It does not make lending decisions.

| Question | Evidence | Action |
| :--- | :--- | :--- |
| Where is leverage higher? | Published debt to annualized income ratios by housing tenure, age and income | Identify groups for further portfolio analysis |
| Does income cover consumption? | Quarterly income less consumption, shown separately from net saving | Avoid treating different pressures as interchangeable |
| Do the inputs reconcile? | Unique keys, missingness, units, identities and published ratios | Block major inconsistencies and retain small exceptions for review |
| Is the interpretation supported? | Trusted evidence cards, exact checks and an AI review benchmark | Flag unsupported wording for a person to examine |
| Does a forecasting model help? | Time ordered comparison with persistence | Keep the simple benchmark when added complexity fails |

## Concrete result

In 2025Q4, owners with mortgages had debt equal to 306.1% of annualized disposable income. Renters had a much lower ratio of 56.4%, but average disposable income was CAD 572 below consumption for the quarter. Their reported net saving was positive CAD 269 because it included a CAD 841 pension entitlement adjustment.

These results identify different questions to investigate. They do not establish which individuals will miss payments. Consumption includes national accounts imputations, so income less consumption is not bank account cash flow.

## Audit connection

The pipeline documents where each measure came from, checks transformations and reconciles calculated values to published values. It retains fourteen small historical net worth reconciliation exceptions instead of hiding them. A separate controlled benchmark measures whether an AI reviewer can detect deliberately misleading report excerpts. Those mistakes are simulated; they are not allegations about Statistics Canada or a bank.

## How an analyst would use it

Refresh the source snapshot, review the control results, inspect the group dashboard and verify the definitions behind any written conclusion. Use the resulting questions to request approved portfolio evidence, such as balances, renewal dates and repayment outcomes. Human review remains necessary before turning public aggregate findings into customer or business decisions.

The national debt service series ends in 2026Q2, while the group data end in 2025Q4. The dashboard keeps these reference periods separate. Neither the earlier random forest nor the neural forecasting extension beat persistence on MAE; that result remains documented.
