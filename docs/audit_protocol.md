# Reporting controls and AI review protocol

## Question and decision

Can an AI reviewer identify unsupported financial reporting claims from a trusted StatCan evidence card, and when should ordinary code checks be used instead?

This is a controlled benchmark for a portfolio project. It is not an audit opinion, a fraud detection model, an assessment of TD controls, or evidence about errors in real bank reports.

## Real evidence

The evidence is from Statistics Canada DHEA tables 36-10-0662-01, 36-10-0660-01 and 36-10-0664-01. There are 936 group and quarter rows in the segment panel, from 2020Q1 through 2025Q4. The latest release is April 13, 2026. The group data have an older reference period than the national debt service table; their dates must remain separate.

The panel uses group means. Income quintiles are based on equivalized disposable income. Age is the age of the major income earner. Income, age and tenure views overlap and must not be added together. Joint income and age cells have fewer published measures; missing pension and saving components are not filled with zero.

## Deterministic controls

The controls test unique keys, required values, positive denominators, saving identities, net worth identities and agreement with the published debt ratio. Input units and merge cardinality are also checked before calculations.

Saving = disposable income + pension entitlement adjustment - consumption. Debt to income is reconstructed as 100 times debt divided by four times quarterly disposable income. It is a stock to annualized income measure, not the share of income paid toward debt.

A CAD 2 screening tolerance is used for identities involving rounded per household values. Fourteen historical joint group net worth rows differ by CAD 3; these are retained as review exceptions rather than silently changing the tolerance. They do not establish material misstatement or fraud. A separate CAD 10 pipeline escalation threshold is a project convention, not a professional audit materiality rule. The latest quarter has none of these net worth exceptions.

## AI benchmark frozen before evaluation

The generator creates 4,368 labeled excerpts from real age, income and tenure evidence. Half are supported and half contain a deliberately introduced problem. Seven types are included: numerical mismatch, wrong period, wrong units, debt ratio confusion, pension adjustment confusion, individual claims from averages, and unsupported causality.

Data from 2020 through 2023 form the development split. The 1,456 cases from 2024 and 2025 form the evaluation split. Only development examples are used for the smoke test. The first smoke test exposed missing unit context in the evidence card; all configurations were given explicit units, aggregation scope and measure definitions before full evaluation. Prompts and labels are fixed before running the full comparison. Templates overlap across years, so this is not evidence of generalization to arbitrary writing or new error types.

Two models, Qwen3 8B and Qwen3 32B, are evaluated under four prompts: a plain request, definitions, an explicit checklist, and verified Python calculations. The Python condition supplies arithmetic and scope statements, not the case label or error type. Model inputs exclude the ground truth label and error category. Thinking mode is disabled. Sampling uses temperature 0.6, top p 0.95, up to 160 output tokens and recorded seeds.

All eight configurations use H100 GPUs. Each worker has a 2,280 second work budget and zero retries. This is a user requested compute allowance, not a minimum cost needed for the task. Processing stops by elapsed time rather than by a desirable score. Results include every returned answer. If configurations complete different numbers of repetitions, compare the same first completed repetitions and report any omitted incomplete tail. Never compare different test subsets without labeling coverage.

## Measures and limitations

Primary measures are unsupported claim recall, false alarm rate on supported claims, balanced accuracy, and invalid response rate. An invalid or missing verdict is an abstention, not an automatic pass. Report counts and class prevalence. Repeated generations are not independent source observations; uncertainty should cluster related cases by source quarter and group.

The basic deterministic baseline handles explicit debt ratio numbers and quarter statements using the evidence card. Other wording is marked for human review. Its coverage and accuracy on covered cases must be reported separately. A hybrid review uses those exact checks where available and AI review elsewhere. Do not describe abstention as successful detection.

The supported and unsupported classes are balanced by construction. That prevalence is unlike a real audit population, so benchmark precision cannot be transported directly to a bank. No conclusions about real fraud detection, professional audit assurance or saved staff hours are supported.
