# Explaining the project in an interview

## Thirty second explanation

I built a household finance reporting project using Statistics Canada data, Python, SQL and Power BI. I wanted to see what national averages hide and whether the reporting could be checked automatically. One finding was that mortgage owners had much higher debt relative to income, while renters had income below consumption despite positive reported net saving. I traced that difference to the pension adjustment, built reconciliation checks, and tested AI reviewers on deliberately misleading excerpts.

## The problem and solution

The problem is that correct numbers can still lead to a misleading conclusion. For example, calling net saving money left after spending ignores the pension entitlement adjustment. My solution keeps income, consumption, pension adjustments and net saving separate, checks their accounting relationship, and flags unsupported reporting claims for review.

## One example I can explain

For renters in 2025Q4, average disposable income was CAD 18,326 and consumption was CAD 18,898. Subtracting them gives negative CAD 572. Adding the CAD 841 pension adjustment gives positive CAD 269 net saving. Both numbers are correct, but they answer different questions. This is a group average and includes national accounts concepts, so it is not an individual cash budget.

## What I actually built

| Skill | Concrete evidence |
| :--- | :--- |
| Python | Three group tables joined at quarter and household group grain, with one to one merge validation |
| SQL | Quarterly joins, changes within each household group and a reporting review view |
| Power BI | Group comparisons, reporting controls, national trends, model results and scenarios |
| Data quality | Source hashes, unit checks, missingness rules and accounting reconciliations |
| AI evaluation | Two models, four prompts, development based selection, a later evaluation period and explicit abstentions |
| Communication | Findings tied to a decision, with source dates and limits stated clearly |

## How auditing fits

This demonstrates data lineage, reconciliation, exception handling and review of whether claims agree with evidence. It is a reporting controls project, not a professional audit opinion or a fraud detector. The benchmark labels are simulated mistakes added to excerpts based on real StatCan observations.

## Questions I should be ready to answer

Why not just forecast? The original forest and later neural model did not improve on persistence. I kept that result and focused the main project on a reporting question with observable, useful findings.

Why use a GPU? The reporting experiment runs Qwen3 8B and 32B locally on Modal H100 GPUs to compare reviewer prompts and repeated answers. Saved results allow CPU reproduction. A GPU is not needed to calculate the household ratios, and the extended compute budget is not a requirement for routine reporting.

How did I avoid leakage? The reviewer configuration is chosen using 2020 through 2023 excerpts. The 2024 and 2025 excerpts are reserved for evaluation. Prompts receive evidence and the claim, never its label. Templates repeat across years, so I do not claim this measures performance on arbitrary new writing.

Why not add more rules? That is a fair alternative. Rules could cover all seven fixed templates. This benchmark tests reviewer behavior under controlled mistakes, not whether AI is necessary. A stronger comparison would use real report wording and a broader rules baseline.

What would improve it? A real reporting sample with independently reviewed labels and approved bank portfolio data. That would test whether the public aggregate patterns and controlled error examples matter in an actual workflow.

## Relevance to internships

TD data science and business intelligence role examples researched in November 2026 included Python, SQL, data preparation, Power BI, data quality and communication. This project gives concrete examples of those skills. It does not imply TD endorsement or production banking experience.

[TD Data Science role example](https://ca.linkedin.com/jobs/view/data-science-intern-co-op-winter-2027-at-td-4464483120)

[TD Business Intelligence role example](https://td.wd3.myworkdayjobs.com/en-US/TD_Bank_Careers/job/Toronto-Ontario/AI2-Business-Intelligence-Co-op-Intern--WINTER-2027-_R_1506122)

Understand and rerun the scripts before presenting the work. Describe assistance honestly if asked. Use the measured benchmark results in reports/audit_benchmark.md rather than assuming the larger model performed better.
