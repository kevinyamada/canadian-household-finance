# What to do with these findings

The immediate decision is to change how household pressure is monitored and described. The dashboard now opens with four conclusions and their next actions. Python regenerates the displayed evidence from the validated outputs.

## Changes completed in this project

| Finding | Change made | How to check it |
| :--- | :--- | :--- |
| Leverage and income relative to consumption answer different questions | Put the group comparison on the opening insight page and keep the measures separate | Compare the mortgage-owner and renter rows in Household groups |
| Positive net saving can coexist with income below consumption | Show the renter income gap, pension adjustment and net saving together | Reconcile -572 + 841 = 269 for 2025Q4 in Reporting controls |
| A falling payment ratio can coexist with rising payments | Present payment growth and income growth beside the ratio | Compare +0.97% payment growth with +2.06% income growth in 2026Q2 |
| The complex forecasts did not beat the simple benchmark on MAE | State the model decision explicitly and retain the comparison | Check 0.245, 0.250 and 0.387 percentage point MAE in the model pages |

The next actions below require evidence beyond the public snapshots. They are an implementation plan, not claims of completed bank deployment.

## 1. Validate the group findings against a real portfolio

**Question:** Do the public patterns appear in an approved borrower sample?

**Inputs needed:** Dated, approved records of balances, verified income, required payments, mortgage type, rate, remaining amortization, renewal date and subsequent repayment outcomes. Establish permitted uses and the observation window with the data owner before extracting records.

**Analysis:** Calculate borrower payment-to-income and debt-to-income separately. Compare renewal exposure and observed arrears by relevant segments. Keep national group averages as context; estimate borrower outcomes using the portfolio itself. Check missing income, outdated income measurements, sample selection and segment sizes.

**Acceptance evidence:** A reproducible cohort definition, reconciled portfolio totals and measured relationships with observed repayment outcomes. Select review thresholds with the business owner before using the results for action. No borrower-level recommendation is supported by the current public data alone.

## 2. Test forecasts on genuinely new releases

**Question:** Does any added model reduce error when only information available at the time is used?

**Inputs needed:** New StatCan releases, release timestamps and archived historical vintages. The existing --refresh option downloads current data; an archived-vintage store is additional work needed for a live evaluation.

**Analysis:** Freeze the forecast and input cutoff before each release. Save the previous-quarter benchmark alongside model estimates. Score MAE, uncertainty coverage and paired errors once the new outcome becomes available. Continue collecting quarters; another random split of the current revised dataset does not create new prospective evidence.

**Acceptance evidence:** An archived, time-stamped forecast ledger and enough new outcomes to assess practical improvement and uncertainty. The current result supports retaining the previous-quarter benchmark.

## 3. Validate AI review on realistic report wording

**Question:** Does AI add useful review coverage beyond well-designed deterministic checks?

**Inputs needed:** Permitted real report excerpts with independent human labels, trusted evidence and documented disagreements. Reserve an evaluation set before choosing prompts.

**Analysis:** Expand the rules baseline to cover all known error families. Compare rules, AI and their combination on the same reserved examples. Report unsupported-claim detection, false alarms, abstentions, coverage and cost. Review false alarms with a person and choose operating thresholds before measuring final performance.

**Acceptance evidence:** A labeled evaluation set, an error review and evidence of value beyond the broader rules baseline. The existing 100% detection result is limited to controlled templates and does not justify automatic approval of real financial reports.

[Four insights and actions](../reports/key_insights.md) · [Interview walkthrough](project_walkthrough.md) · [Validation record](validation.md)
