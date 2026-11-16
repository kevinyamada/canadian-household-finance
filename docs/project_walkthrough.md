# What this project does, in plain language

The project helps a banking analyst answer two questions: **where is household financial pressure different, and could a report describe that pressure incorrectly?**

Start with the **Key insights** page: each conclusion has a dated number, an explanation and a next action. The [four-insight brief](../reports/key_insights.md) is the written version, and the [next-step plan](next_steps.md) explains what further evidence is needed.

## One example explains the problem

For the average renter household in 2025Q4, Statistics Canada reported:

| Item | CAD per household for the quarter |
| :--- | ---: |
| Disposable income | 18,326 |
| Consumption | 18,898 |
| Income less consumption | -572 |
| Pension entitlement adjustment | +841 |
| Reported net saving | +269 |

The calculation is **18,326 - 18,898 + 841 = 269**. Positive net saving therefore does not mean income covered consumption. A report saying renters had $269 of income left after spending would misdescribe the measure. Pension entitlements and national accounts consumption are accounting concepts; this is a group average, not an individual bank account budget.

Mortgage owners show another kind of pressure: their debt was 306.1% of annualized disposable income, compared with 56.4% for renters. That measures how much debt exists relative to income. The national debt service ratio elsewhere in the report measures required payments relative to income. The two ratios answer different questions.

## What was built

1. **Python in VS Code** downloads and joins Statistics Canada data, calculates the measures and checks their definitions and accounting relationships.
2. **SQL** compares each household group with the same quarter a year earlier and creates a view highlighting claims that need review.
3. **Power BI Desktop** lets an analyst compare groups and inspect the checks before writing a conclusion.
4. **Modal H100 experiments** test AI review against deliberately misleading statements and compare neural forecasts with a simple benchmark. Saved responses allow reproduction without another GPU run.

The main group analysis contains 936 rows: 39 groups across 24 quarters. The national analysis contains 146 quarters. Neither is customer credit data.

## The answer and the action

Review leverage and income relative to consumption separately. Show the pension adjustment whenever interpreting net saving. Use the checks to catch inconsistent inputs and use AI flags as suggestions for human review. An analyst can then request approved portfolio evidence to investigate the groups; these public averages do not identify which customers will miss payments.

In the controlled AI test, the selected Qwen3-32B checklist reviewer flagged all deliberately unsupported evaluation statements across five matched repetitions, with a 1.40% false alarm rate on supported statements. This describes 1,456 unique, templated evaluation cases. It does not establish performance on arbitrary real reports; rules could cover every known template. See the [benchmark findings](../reports/audit_benchmark.md).

The forecasting experiments did not beat the simple prediction that the next quarter resembles the current quarter. Keeping that benchmark is the evidence-based decision.

## Five-minute Power BI demo

Open the regular `CanadianHouseholdFinance.pbix` in Power BI Desktop. It contains the loaded snapshot. The `.pbip` is the editable source project used when rebuilding. See the [opening guide](powerbi_usage.md).

| Time | Page | What to show |
| :--- | :--- | :--- |
| First minute | Key insights | Read the four findings and the action under each. Explain that the group and national dates differ. |
| Second minute | Household groups and Reporting controls | Compare mortgage owners and renters, then explain -572 + 841 = 269 and the six checks. |
| Third minute | AI reporting review | Compare detection, false alarms and abstentions. Explain that the incorrect statements were deliberately generated. |
| Fourth minute | Household pressure and Model evaluation | Show 14.52% in 2026Q2 and why income growth lowered it. Explain why the forest did not justify replacing persistence. |
| Fifth minute | Payment scenarios | Select payment change 10 and income change -2. The assumed ratio becomes 16.30%. Clear both slicers afterwards. |

The GPU experiment page gives the earlier neural result. It is useful for a modeling discussion, but the household finding is the clearest starting point.

## Thirty-second interview explanation

> I built a Python, SQL and Power BI project to compare Canadian household financial pressure and check whether the reporting could be misleading. Renters had income below consumption, even though reported net saving was positive. I traced the difference to a pension adjustment, added reconciliation controls, and tested AI review using controlled mistakes on Modal H100 GPUs. The result is a dashboard and reproducible review workflow that helps an analyst ask better questions before using aggregate data for a decision.

[Problem and decision](problem_statement.md) · [Interview questions](interview_notes.md) · [Methodology](methodology.md)
