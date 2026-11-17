# Can this mortgage file be signed off?

**FICTIONAL TRAINING FILE — constructed worksheets, not genuine financial records or a lender approval.**

Follow a submitted claim, a corrected review and a revised request. Supporting schedules are constructed worksheets. Agreement with them does not authenticate real records.

## Three stages

| Stage | Price | Gross income / year | Available cash | Debt / month | Income needed / year | Review outcome |
|---|---:|---:|---:|---:|---:|---|
| Submitted claim | CAD 764,100 | CAD 150,000 | CAD 100,000 | CAD 500 | CAD 126,575 | Hold: claim not reconciled |
| Corrected review | CAD 764,100 | CAD 135,000 | CAD 85,000 | CAD 750 | CAD 161,292 | Hold: income exception and external evidence |
| Revised request | CAD 600,000 | CAD 135,000 | CAD 85,000 | CAD 750 | CAD 128,610 | Hold: external verification remains |

The submitted screen deliberately uses the contract rate to qualify. The corrected review uses recurring salary, unpledged funds, all listed debt and supporting cost assumptions. The revised request changes only the hypothetical price. Supported finances stay fixed; the historical tax proxy is recalculated at the new price.

## Findings and resolution trail

| Finding | Application | Mock support | Difference | Worksheet IDs |
|---|---:|---:|---:|---|
| Recurring gross income (CAD / year) | CAD 150,000 | CAD 135,000 | -CAD 15,000 | INC-001-A|INC-001-B|INC-001-C |
| Available purchase cash (CAD) | CAD 100,000 | CAD 85,000 | -CAD 15,000 | FND-001-A|FND-001-B |
| Other debt payments (CAD / month) | CAD 500 | CAD 750 | +CAD 250 | DBT-001-A|DBT-001-B|DBT-001-C |
| Property tax proxy (CAD / year) | CAD 1,800 | CAD 2,125 | +CAD 325 | CST-001 |
| Heating (CAD / month) | CAD 100 | CAD 150 | +CAD 50 | CST-001 |
| Condo fees (CAD / month) | CAD 200 | CAD 250 | +CAD 50 | CST-001 |
| Rate used to qualify (percentage points) | 4.15% | 6.15% | +2.00 pp | RTE-001 |

- **F-01 — Recurring gross income:** Use recurring base salaries; exclude the isolated bonus under this exercise's conservative treatment. This is not a universal rule that bonuses are ineligible. Status: Corrected in simulation; external verification remains.
- **F-02 — Available purchase cash:** Deduct pledged funds unavailable before closing; count each balance once. Status: Corrected in simulation; external verification remains.
- **F-03 — Other debt payments:** Include the omitted student-loan payment and reconcile all listed obligations. Status: Corrected in simulation; external verification remains.
- **F-04 — Property tax proxy:** Use the historical municipal schedule and stated price-as-assessment proxy. An actual property bill remains necessary. Status: Corrected in simulation; external verification remains.
- **F-05 — Heating:** Use the supporting estimate; actual heat records or a justified property estimate remain necessary. Status: Corrected in simulation; external verification remains.
- **F-06 — Condo fees:** Use the full supporting fee; include half in debt-service ratios and the full fee in modeled outgoings. Status: Corrected in simulation; external verification remains.
- **F-07 — Rate used to qualify:** Use the greater of contract rate plus two percentage points or 5.25%, rather than the payment's contract rate. Status: Corrected in simulation; external verification remains.

## What still prevents sign-off

- **OPEN-01 — Income and employment authenticity:** Independently verify actual income, employment, history and the treatment of variable pay.
- **OPEN-02 — Ownership and availability of funds:** Authenticate account histories, source of funds, restrictions and availability before closing.
- **OPEN-03 — Complete credit and debt records:** Obtain an authorized credit review and reconcile all actual recurring obligations.
- **OPEN-04 — Subject property and costs:** Verify agreement, valuation, actual taxes, heating and condo costs for the subject property.
- **OPEN-05 — Lender, insurer and program criteria:** Verify the actual rate commitment, eligibility, insurance, tax relief and applicable lending criteria.
- **OPEN-06 — Independent review and sign-off:** A qualified reviewer must document their actual review; this synthetic exercise supplies no signature or approval.

**Final conclusion:** the revised request fits both modeled financial checks. Keep the file on hold until actual borrower, property and lender evidence is verified and a qualified reviewer signs off. No actual approval, signature or compliance opinion is supplied.

## Inputs and reproduction

The initial price is a constructed 10%-lower scenario relative to the 2023 Vancouver benchmark, not a current listing. The revised CAD 600,000 price is hypothetical. Costs use the historical tax schedule and a price-as-assessment proxy. September 2026 national rates are not individual offers. Bonus treatment is a conservative exercise assumption, not a universal bank rule.

[Training inputs](../data/scenarios/mortgage_file/training_file.json) · [Saved worksheets and stages](../data/processed) · [Python](../src/mortgage_file_audit.py) · [Independent SQL](../sql/mortgage_file_audit.sql)

- [CMHC debt service](https://www.cmhc-schl.gc.ca/professionals/project-funding-and-mortgage-financing/mortgage-loan-insurance/calculating-gds-tds)
- [OSFI B-20](https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/residential-mortgage-underwriting-practices-procedures-guideline-2017)
- [Bank of Canada rates](https://www.bankofcanada.ca/rates/banking-and-financial-statistics/interest-rates-for-new-and-existing-lending-by-chartered-banks/)

Run src/homebuying_study.py in desktop VS Code to rebuild this exercise with the study. The packet exporter creates an eight-page PDF and ZIP. The website and Power BI display saved results and retain the outstanding evidence checks.
