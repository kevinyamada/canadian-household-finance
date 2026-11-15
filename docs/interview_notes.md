# Explaining the project in an interview

## Short explanation

I built a Canadian household borrowing dashboard from Statistics Canada and Bank of Canada data. Python checks and transforms the source files, SQLite joins the quarterly tables, and Power BI presents the results. I also compared simple forecasting rules with ridge regression and a random forest using expanding time windows. The forest won during model selection but did not beat persistence in the final test, so I kept that limitation in the recommendation.

## The problem I solved

A falling debt service ratio can look like payment relief even when payments are still rising. I separated the payment and income contributions so an analyst could explain the change correctly. I then tested whether a more complex forecast was worth using for monitoring. Neither the original forest nor the later neural model beat persistence on MAE, so I kept the simpler benchmark.

## What I would discuss

The main finding is that the latest debt service ratio improved because income grew faster than required payments. Payments themselves did not fall. Separating the numerator and denominator makes the business explanation clearer.

The hardest modeling issue is information timing. Random splitting would allow information from the future into training. Even time ordered validation has a limit here because published historical data are revised. I would need archived releases to claim real time forecast performance.

The dataset has 146 quarters. More complicated models are not automatically better. The final test is a reason to keep a simple benchmark and to report a negative result honestly.

The next useful step would be approved portfolio data containing balances, loan types, renewal dates, and repayment outcomes. That would allow validation at the level where a bank actually makes decisions. Public national aggregates cannot replace that.

## How this matches internship work

TD's Winter 2027 Data Science and AI2 Business Intelligence postings describe Python, SQL, data preparation, Power BI, data quality, documentation, and communication with business partners. This project provides inspectable examples of those tasks. It does not claim Azure, Databricks, or production deployment experience.

| Skill | Evidence in this project |
| :--- | :--- |
| Python | Source ingestion, validation, feature creation, models and figures |
| SQL | Quarterly joins, views, and window functions in sql/analysis.sql |
| Power BI | Semantic model, relationships, DAX measures, slicers and three report pages |
| Statistical validation | Expanding windows, held out time period, baselines and error sensitivity |
| Data quality | Source hashes, grain checks, units and accounting identities |
| Communication | A short analysis, clear recommendation and documented limits |

[TD Data Science posting](https://ca.linkedin.com/jobs/view/data-science-intern-co-op-winter-2027-at-td-4464483120)

[TD AI2 Business Intelligence posting](https://td.wd3.myworkdayjobs.com/en-US/TD_Bank_Careers/job/Toronto-Ontario/AI2-Business-Intelligence-Co-op-Intern--WINTER-2027-_R_1506122)

These are role examples researched in November 2026, not a claim that applications remain open. Review and understand each script before presenting this as your own work, and describe any assistance honestly if asked.

## Explaining the Modal experiment

I used eight H100 workers to test eight neural configurations and sensitivity to random initialization. Every time window had its own training only normalization and parameters. The neural ensemble had MAE 0.387 versus 0.245 for persistence. That is a negative result, but it answers the model selection question. More compute did not create more economic observations or justify changing the benchmark.

The GPU comparison is exploratory because I had already examined the original test period. Before relying on a new model, I would validate it prospectively on archived releases. I would also use far fewer seeds for a routine refresh; the extended run examined initialization stability under a fixed compute allowance.
