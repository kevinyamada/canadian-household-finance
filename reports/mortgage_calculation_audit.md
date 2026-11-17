# Could a calculation mistake change the decision?

## Worked case

Vancouver, two earners, **price 10% below the 2023 transaction benchmark**: CAD 764,100 price, CAD 150,000 gross annual income. Cash and buyer finances are unchanged. Each row introduces one deliberate mistake; the first row is the correct calculation.

| Calculation | Annual income needed | Income understated | Financial-screen result |
|---|---:|---:|---|
| Correct calculation | CAD 167,429 | CAD 0 | Income still short |
| Use the contract rate to qualify | CAD 141,543 | CAD 25,887 | Fits both financial checks — false pass |
| Leave out other debt payments | CAD 167,429 | CAD 0 | Income still short |
| Leave out tax, heat and condo fees | CAD 153,520 | CAD 13,910 | Income still short |
| Leave the premium out of the loan | CAD 162,813 | CAD 4,616 | Income still short |

The incorrect calculations are isolated demonstrations, not production lending rules. They show why a reviewer must reperform a result rather than accept a spreadsheet's “pass” label.

## What a reviewer should check

| Deliberate error | Control | Evidence |
|---|---|---|
| Contract rate used to qualify | Recalculate the applicable qualifying rate before computing the payment | Rate commitment, amortization and applicable lender/insurer rule |
| Other debts omitted | Reconcile recurring obligations and calculate both GDS and TDS | Credit report, loan/line-of-credit statements and debt schedules |
| Tax, heat and condo costs omitted | Tie costs to the subject property and the screen's treatment | Tax bill, heat records or justified estimate, condo documents |
| Financed insurance premium omitted | Reconcile base principal plus premium to the payment calculation | Down-payment calculation, premium schedule and financing documents |

An error may understate income without changing the outcome because another constraint still binds. “No decision change” does not mean the input is valid. Cash-short cases are never counted as false passes merely because a bad income calculation passes.

Across the 117 saved current-benchmark purchase scenarios, **11 scenario cases** appear to pass both financial checks under at least one deliberately flawed calculation when the correct calculation does not. This count describes the saved illustrations only; it is not a bank error rate or a population estimate. The full table includes all 585 correct/flawed recalculations.

Correct results reproduce the production income requirement and reconcile to a separate SQLite expression. These demonstrations cannot establish that an actual bank or TD made an error.

- [All audit calculations](../data/processed/homebuying_calculation_audit.csv)
- [Existing mortgage-file working paper](../docs/bank_audit_case.md)
- [CMHC input and qualifying-rate guidance](https://www.cmhc-schl.gc.ca/professionals/project-funding-and-mortgage-financing/mortgage-loan-insurance/calculating-gds-tds)
- [OSFI B-20: documentation, income verification and debt service](https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/residential-mortgage-underwriting-practices-procedures-guideline-2017)
