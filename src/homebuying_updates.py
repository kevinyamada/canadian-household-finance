"""Latest-rate sensitivity and controlled mortgage-calculation audit, run in desktop Python."""
import json
import math
import sqlite3
import pandas as pd
from homebuying_data import ROOT,CITIES
from homebuying_model import PROFILES,evaluate,monthly_payment
from homebuying_review import explain_cases,money,position
from homebuying_limits import maximum_price
from refresh_homebuying_sources import load_refresh,TABLE_URL,RELEASE_URL,BOC_PAGE

OUT=ROOT/"data/processed"
ERRORS=[
    ("correct","Correct calculation","Use the qualifying payment, property costs, other debts and financed premium."),
    ("contract_rate","Use the contract rate to qualify","Reperform the qualifying rate: greater of contract rate plus 2 points or 5.25%."),
    ("omit_debt","Leave out other debt payments","Reconcile stated obligations to the credit file and debt statements; check TDS as well as GDS."),
    ("omit_costs","Leave out tax, heat and condo fees","Verify the tax bill, heating estimate and half the condo fees used in the screen."),
    ("omit_premium","Leave the premium out of the loan","Tie the financed loan amount to base principal plus the insurance premium; keep the qualifying rate fixed."),
]

def error_review(row):
    """Deliberately flawed recalculations; these never replace the production financial model."""
    r=dict(row);results=[]
    for order,(key,label,control) in enumerate(ERRORS):
        principal=r["mortgage_principal"]-(r["insurance_premium"] if key=="omit_premium" else 0)
        rate=r["contract_rate"] if key=="contract_rate" else r["qualifying_rate"]
        payment=monthly_payment(principal,rate,r["amortization_years"])
        costs=0 if key=="omit_costs" else r["annual_property_tax"]/12+r["heating"]+.5*r["condo_fee"]
        debt=0 if key=="omit_debt" else r["monthly_debt"]
        housing=payment+costs
        needed=max(housing/.39,(housing+debt)/.44)*12 if r["mortgage_principal"]>0 else 0
        passes=needed-r["profile_income"]<=.005
        fits=bool(r["cash_pass"] and passes)
        correct_fits=bool(r["cash_pass"] and r["income_pass"])
        results.append({
            "city":r["city"],"profile":r["profile"],"profile_label":r["profile_label"],
            "case_id":r["case_id"],"scenario":r["scenario"],"scenario_label":r["scenario_label"],
            "price":r["price"],"profile_income":r["profile_income"],"cash_pass":bool(r["cash_pass"]),
            "variant":key,"variant_label":label,"variant_order":order,"required_gross_income":needed,
            "correct_required_income":r["required_gross_income"],"income_understated":max(0,r["required_gross_income"]-needed),
            "income_position":r["profile_income"]-needed,"income_position_label":position(r["profile_income"]-needed,"requirement"),
            "qualifying_payment_used":payment,"rate_used":rate,"other_debt_used":debt,"housing_costs_used":costs,
            "income_pass":passes,"financial_pass":fits,"correct_financial_pass":correct_fits,
            "false_pass":bool(key!="correct" and fits and not correct_fits),
            "decision_label":"False pass" if key!="correct" and fits and not correct_fits else "Fits both financial checks" if fits else "Income still short" if r["cash_pass"] else "Minimum cash still short",
            "result_label":"Fits both financial checks" if fits else "Income still short" if r["cash_pass"] else "Minimum cash still short",
            "reviewer_check":control,
            "scope":"Controlled error demonstration, not observed bank mistakes or a default-risk estimate. Cash position is held unchanged; each error is introduced separately.",
        })
    return results

def build_updates(cases):
    manifest,review,rates=load_refresh()
    year=int(cases.year.max())
    if review["latest_sales_year"]!=year:raise ValueError("Matched buyer benchmark must be reviewed before using a new sales year")
    baseline=cases[cases.year.eq(year)&cases.scenario.eq("baseline")]
    latest=[];limits=[]
    buyers={b.id:b for b in PROFILES}
    for base in baseline.itertuples():
        spec=CITIES[base.city];buyer=buyers[base.profile]
        row=evaluate(base.price,buyer,spec["province"],spec["tax_rate"],rates["insured"],rates["uninsured"])
        row.update(city=base.city,profile=base.profile,profile_label=base.profile_label,price_year=year,
            rate_period=rates["period"],baseline_rate_year=year,scenario="latest_rate_sensitivity",
            case_id=base.case_id+"|rates:"+rates["period"],baseline_required_income=float(base.required_gross_income),
            baseline_monthly_mortgage=float(base.monthly_mortgage),baseline_contract_rate=float(base.contract_rate),
            income_requirement_change=row["required_gross_income"]-base.required_gross_income,
            payment_change=row["monthly_mortgage"]-base.monthly_mortgage,
            scope=f"{rates['period']} observed national monthly rates applied to fixed {year} prices, property-tax schedule and buyer finances. Not observed current affordability or a lender offer.")
        latest.append(row)
        limit=maximum_price(buyer,spec["province"],spec["tax_rate"],rates["insured"],rates["uninsured"])
        limits.append({"city":base.city,"profile":base.profile,"profile_label":base.profile_label,"price_year":year,
            "rate_period":rates["period"],"maximum_price":limit,"maximum_price_display":math.floor(limit/1000)*1000,
            "maximum_price_label":"About "+money(math.floor(limit/1000)*1000),"scope":row["scope"]})
    latest=explain_cases(pd.DataFrame(latest));limits=pd.DataFrame(limits)
    current=cases[cases.year.eq(year)]
    errors=pd.DataFrame([item for row in current.to_dict("records") for item in error_review(row)])
    correct=errors[errors.variant.eq("correct")]
    if (correct.required_gross_income-correct.correct_required_income).abs().max()>1e-7:
        raise ValueError("Independent audit calculation does not reproduce correct requirements")
    if errors.duplicated(["case_id","variant"]).any():raise ValueError("Duplicate audit rows")
    freshness={"checked_on":manifest["checked_on"],"latest_sales_year":year,"statcan_release_date":review["release_date"],
        "statcan_property_reference_year":review["property_reference_year"],"rate_period":rates["period"],
        "insured_rate":rates["insured"],"uninsured_rate":rates["uninsured"],
        "statcan_status":review["extract_status"],"rates_status":"Downloaded and checksummed from Bank of Canada Valet",
        "matched_baseline_kept":True,"current_rate_sensitivity_not_current_market":True,
        "source_table":TABLE_URL,"release_url":RELEASE_URL,"rates_url":BOC_PAGE,
        "scope":"A publication date, property-stock reference year and sales reference year are different. Partial-year rates are monthly observations, not a full-year average."}
    for name,frame in [("homebuying_latest_rates.csv",latest),("homebuying_latest_rate_limits.csv",limits),("homebuying_calculation_audit.csv",errors)]:
        (OUT/name).write_text(frame.to_csv(index=False,lineterminator="\n"),encoding="utf-8",newline="\n")
    (OUT/"homebuying_source_freshness.json").write_text(json.dumps(freshness,indent=2),encoding="utf-8",newline="\n")
    with sqlite3.connect(OUT/"homebuying.sqlite") as connection:
        latest.to_sql("latest_rate_cases",connection,if_exists="replace",index=False)
        limits.to_sql("latest_rate_limits",connection,if_exists="replace",index=False)
        errors.to_sql("calculation_audit",connection,if_exists="replace",index=False)
        connection.executescript((ROOT/"sql/homebuying_updates.sql").read_text(encoding="utf-8"))
        check=pd.read_sql_query("SELECT * FROM calculation_audit_reconciliation",connection)
        if check[["required_income_delta","false_pass_delta"]].abs().to_numpy().max()>1e-7:raise ValueError("Audit SQL reconciliation failed")
    write_reports(latest,limits,errors,freshness)
    def records(frame):return json.loads(frame.to_json(orient="records",double_precision=12))
    return {"source_freshness":freshness,"latest_rate_cases":records(latest),
            "latest_rate_limits":records(limits),"calculation_audit":records(errors),
            "audit_scenarios":[{"id":s,"label":g.scenario_label.iloc[0]} for s,g in current.groupby("scenario",sort=False)]}

def write_reports(latest,limits,errors,freshness):
    chosen=latest[latest.city.eq("Vancouver")&latest.profile.eq("couple")].iloc[0]
    worked=errors[errors.city.eq("Vancouver")&errors.profile.eq("couple")&errors.scenario.eq("price10")].sort_values("variant_order")
    false_cases=int(errors[errors.false_pass].case_id.nunique())
    fresh=f"""# Source refresh: what is current, and what is not?

Checked {freshness['checked_on']} in desktop VS Code.

| Input | Published period used | Treatment |
|---|---|---|
| Statistics Canada city buyer transactions and family income | {freshness['latest_sales_year']} | Latest comparable buyer release reviewed; matched historical baseline retained |
| Residential-property stock in that release | {freshness['statcan_property_reference_year']} | Not relabeled as the sales year |
| Insured fixed mortgages, five years and over, funds advanced | {freshness['rate_period']}: {freshness['insured_rate']:.2f}% | Latest common published monthly observation |
| Uninsured equivalent | {freshness['rate_period']}: {freshness['uninsured_rate']:.2f}% | Same month, same lending concept |
| Municipal property-tax rates and cost assumptions | Original 2023 schedule and explicit profile assumptions | Held fixed; not a current property bill |

Statistics Canada's release dated {freshness['statcan_release_date']} combines property-stock information for 2024 with home-sale and buyer information for 2023. A newer webpage date does not make the transactions newer.

**Retrieval limit:** {freshness['statcan_status']}. The earlier extract remains checksummed; no claim is made that revisions were re-downloaded. The latest-rate JSON files were downloaded successfully from Bank of Canada Valet, then checked for series identity, duplicate months, future dates, common coverage and checksums.

## What the newer rates change

For the Vancouver two-earner example at the unchanged CAD 849,000 price, required income changes from **{money(chosen.baseline_required_income)}** to **{money(chosen.required_gross_income)}**. Monthly mortgage payment changes from **{money(chosen.baseline_monthly_mortgage)}** to **{money(chosen.monthly_mortgage)}**. The result is **{chosen.result_label.lower()}**.

This is a rate sensitivity on old prices and unchanged finances. It cannot establish current affordability: prices, taxes, costs and buyer finances would also need updating. The 2026 monthly rate is not an annual average and is not an available offer for a particular applicant.

- [Statistics Canada table]({TABLE_URL})
- [Release explaining the reference years]({RELEASE_URL})
- [Bank of Canada lending-rate table]({BOC_PAGE})
- [Checksummed refresh sources](../data/raw/homebuying_refresh/manifest.json)
- [Nine latest-rate examples](../data/processed/homebuying_latest_rates.csv)
"""
    (ROOT/"reports/source_refresh.md").write_text(fresh,encoding="utf-8",newline="\n")
    audit=f"""# Could a calculation mistake change the decision?

## Worked case

Vancouver, two earners, **price 10% below the 2023 transaction benchmark**: {money(worked.price.iloc[0])} price, {money(worked.profile_income.iloc[0])} gross annual income. Cash and buyer finances are unchanged. Each row introduces one deliberate mistake; the first row is the correct calculation.

| Calculation | Annual income needed | Income understated | Financial-screen result |
|---|---:|---:|---|
"""
    for row in worked.itertuples():
        audit+=f"| {row.variant_label} | {money(row.required_gross_income)} | {money(row.income_understated)} | {row.result_label}{' — false pass' if row.false_pass else ''} |\n"
    audit+="""
The incorrect calculations are isolated demonstrations, not production lending rules. They show why a reviewer must reperform a result rather than accept a spreadsheet's “pass” label.

## What a reviewer should check

| Deliberate error | Control | Evidence |
|---|---|---|
| Contract rate used to qualify | Recalculate the applicable qualifying rate before computing the payment | Rate commitment, amortization and applicable lender/insurer rule |
| Other debts omitted | Reconcile recurring obligations and calculate both GDS and TDS | Credit report, loan/line-of-credit statements and debt schedules |
| Tax, heat and condo costs omitted | Tie costs to the subject property and the screen's treatment | Tax bill, heat records or justified estimate, condo documents |
| Financed insurance premium omitted | Reconcile base principal plus premium to the payment calculation | Down-payment calculation, premium schedule and financing documents |

An error may understate income without changing the outcome because another constraint still binds. “No decision change” does not mean the input is valid. Cash-short cases are never counted as false passes merely because a bad income calculation passes.
"""
    audit+=f"""
Across the 117 saved current-benchmark purchase scenarios, **{false_cases} scenario cases** appear to pass both financial checks under at least one deliberately flawed calculation when the correct calculation does not. This count describes the saved illustrations only; it is not a bank error rate or a population estimate. The full table includes all {len(errors)} correct/flawed recalculations.

Correct results reproduce the production income requirement and reconcile to a separate SQLite expression. These demonstrations cannot establish that an actual bank or TD made an error.

- [All audit calculations](../data/processed/homebuying_calculation_audit.csv)
- [Existing mortgage-file working paper](../docs/bank_audit_case.md)
- [CMHC input and qualifying-rate guidance](https://www.cmhc-schl.gc.ca/professionals/project-funding-and-mortgage-financing/mortgage-loan-insurance/calculating-gds-tds)
- [OSFI B-20: documentation, income verification and debt service](https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/residential-mortgage-underwriting-practices-procedures-guideline-2017)
"""
    (ROOT/"reports/mortgage_calculation_audit.md").write_text(audit,encoding="utf-8",newline="\n")
    brief=f"""# Interview brief

## Why does buying a home still feel out of reach?

**Question:** Is the down payment really the biggest obstacle to buying a home?

**Problem:** Enough cash to close does not establish that income supports the mortgage. A bank reviewer also needs trustworthy calculations and evidence.

**What I built:** Python and SQL analysis in desktop VS Code, an interactive GitHub Pages website and a native Power BI Desktop report. Observed benchmarks come from Statistics Canada and Bank of Canada; public government guidance supplies the rules. Buyer finances and costs are explicit assumptions.

**Finding:** Four of nine baseline examples meet minimum cash but fail the income screen. The Vancouver couple has CAD 14,640 above the minimum cash target but is CAD 40,014 short in annual income. About CAD 690,000 fits that profile's starting finances under the baseline assumptions.

**Refresh:** At unchanged prices and finances, {freshness['rate_period']} mortgage rates reduce that couple's required income to {money(chosen.required_gross_income)}. The gap remains. This is a rate sensitivity, not current-market affordability.

**Banking audit:** In a separate CAD 764,100 worked case, using the contract rate instead of the qualifying rate creates a false pass. Correct annual income required is CAD 167,429; the flawed calculation says CAD 141,543. I mapped four defined mistakes to reviewer checks and required documents.

**Validation:** Independent SQLite and loan-schedule reconciliations, financial boundary tests, website checks against saved outputs and native Power BI verification. The release validation report records completed checks.

**Recommendation:** Identify the binding cash/income constraint, reperform key calculations and hold sign-off until borrower, property and policy evidence supports the result.

**Limits:** Transactions and matched buyer income remain 2023 data in the latest reviewed release. Rates are national observations, not individual offers. Historical tax schedules and assumed costs remain. The examples are not a population sample. No TD customer data or internal policy is used.

## A short spoken introduction

“I asked why saving a down payment can still leave someone unable to buy. I separated cash from the mortgage-income requirement using official Canadian data. Four of nine examples had enough minimum cash but not enough income. I then showed what price fits and built an audit example where using the wrong qualifying rate changes the result. My recommendation is to identify the actual constraint and verify the evidence before calling a file ready.”

[Interactive project](https://kevinyamada.github.io/canadian-household-finance/) · [Worked audit](../reports/mortgage_calculation_audit.md) · [Source refresh](../reports/source_refresh.md)
"""
    (ROOT/"docs/interview_brief.md").write_text(brief,encoding="utf-8",newline="\n")
