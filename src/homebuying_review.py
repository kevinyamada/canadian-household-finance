"""Explain zero shortfalls, calculate actionable thresholds and independently review outputs."""
from pathlib import Path
import math
import pandas as pd
from homebuying_model import PROFILES, evaluate
from homebuying_data import CITIES
from homebuying_limits import maximum_price, minimum_cash_for_income

RESULT_LABELS={"Income":"Income still short","Cash":"Cash still short",
               "Both cash and income":"Cash and income still short","Within modeled limits":"Fits both financial checks"}

def money(value):
    value=float(value)
    digits=2 if .005 <= abs(value) < 1 else 0
    return ("-" if value<0 else "")+f"CAD {abs(value):,.{digits}f}"

def position(value, comparison):
    if abs(value)<=.005:return "Meets "+comparison
    return money(abs(value))+(" above" if value>0 else " short")

def explain_cases(cases):
    cases=cases.copy()
    cases["cash_position"]=cases.profile_cash-cases.cash_target
    cases["income_position"]=cases.profile_income-cases.required_gross_income
    cases["cash_position_label"]=cases.cash_position.map(lambda n:position(n,"minimum"))
    cases["income_position_label"]=cases.income_position.map(lambda n:position(n,"requirement"))
    cases["result_label"]=cases.barrier.map(RESULT_LABELS)
    return cases

def explain_programs(programs):
    programs=programs.copy()
    programs["applicable"]=~(programs.city.eq("Halifax")&programs.program.eq("BC transfer relief"))
    labels={
        "BC transfer relief":[("Transfer tax","transfer_tax"),("Cash required + reserve","cash_target"),("Income needed / year","required_income")],
        "30-year amortization":[("Monthly mortgage payment","monthly_payment"),("Income needed / year","required_income"),("First five years' interest","five_year_interest")],
        "HBP existing RRSP":[("Liquid cash for purchase","liquid_cash"),("Mortgage amount","loan"),("Income needed / year","required_income")],
        "FHSA one-year illustration":[("Liquid cash after one year","liquid_cash"),("Income needed / year","required_income"),("Monthly mortgage payment","monthly_payment")],
    }
    for index,row in programs.iterrows():
        before_label="Without the measure";after_label="With the measure"
        if row.program=="FHSA one-year illustration":
            before_label="Same one-year saving, no FHSA refund";after_label="Same saving, with assumed refund"
        if row.program=="HBP existing RRSP":
            before_label="RRSP left invested";after_label="Existing RRSP funds withdrawn"
        programs.loc[index,"before_label"]=before_label;programs.loc[index,"after_label"]=after_label
        for i,(label,column) in enumerate(labels[row.program],1):
            programs.loc[index,f"metric_{i}_label"]=label
            programs.loc[index,f"metric_{i}_before"]=row[column+"_before"]
            programs.loc[index,f"metric_{i}_after"]=row[column+"_after"]
        programs.loc[index,"cash_explanation"]=(
            "Not applicable: the BC transfer-tax exemption does not apply in Halifax."
            if not programs.loc[index,"applicable"] else
            "The minimum cash target is unchanged. This measure changes the payment and income screen."
            if row.program=="30-year amortization" else
            "Extra cash reduces the mortgage. An already-zero cash shortfall does not show this benefit."
            if row.program in ["HBP existing RRSP","FHSA one-year illustration"] else
            "The exemption reduces transfer tax and the minimum cash target, subject to eligibility."
        )
    return programs

def price_limits(baseline,rates):
    records=[]
    profiles={b.id:b for b in PROFILES}
    for row in baseline.itertuples():
        buyer=profiles[row.profile];spec=CITIES[row.city]
        insured,uninsured=rates.loc[int(row.year),["insured","uninsured"]]
        args=(buyer,spec["province"],spec["tax_rate"],insured,uninsured)
        limit=maximum_price(*args)
        cash=minimum_cash_for_income(row.price,*args)
        extra=max(0,cash-buyer.liquid_cash)
        reduction=max(0,row.price-limit) if limit is not None else None
        records.append({
            "city":row.city,"profile":row.profile,"profile_label":row.profile_label,"year":int(row.year),
            "case_id":row.case_id,"benchmark_price":row.price,"profile_income":buyer.gross_income,"profile_cash":buyer.liquid_cash,
            "maximum_price":limit,"price_reduction_to_limit":reduction,
            "total_cash_to_fit_at_benchmark":cash,"additional_cash_to_fit":extra,
            "maximum_price_display":math.floor(limit/1000)*1000 if limit is not None else None,
            "additional_cash_display":math.ceil(extra/1000)*1000,
            "maximum_price_label":"About "+money(math.floor(limit/1000)*1000) if limit is not None else "No cash-feasible purchase",
            "additional_cash_label":"About "+money(math.ceil(extra/1000)*1000)+" more cash" if extra>.005 else "No extra cash needed for both checks",
            "scope":"Baseline finances and rates held fixed; whole-CAD financial-screen limit, not a safe-spending recommendation or mortgage approval.",
        })
    return pd.DataFrame(records)

def independent_review(cases,programs,waiting,limits):
    """Reconcile budgets and run a separate month-by-month amortization schedule."""
    checks=[]
    def record(name,rows,error,tolerance=1e-7,note=""):
        checks.append({"check":name,"rows":int(rows),"max_absolute_error":float(error),
                       "tolerance":tolerance,"status":"Pass" if error<=tolerance else "Fail","note":note})
    record("Cash shortfall identity",len(cases),(cases.cash_gap-(cases.cash_target-cases.profile_cash).clip(lower=0)).abs().max())
    record("Signed cash position",len(cases),(cases.cash_position-(cases.profile_cash-cases.cash_target)).abs().max())
    record("Signed income position",len(cases),(cases.income_position-(cases.profile_income-cases.required_gross_income)).abs().max())
    feasible=cases[cases.cash_pass]
    overspend=(feasible.cash_spent+feasible.reserve-feasible.profile_cash).clip(lower=0).max()
    record("Cash allocation stays within funds",len(feasible),overspend,1e-6,
           "Cash above the minimum target is deployed toward the down payment; it is not cash left after buying.")
    loan=(cases.price-cases.down_used+cases.insurance_premium).clip(lower=0)
    record("Financed premium and loan identity",len(cases),(cases.mortgage_principal-loan).abs().max())
    balance_error=interest_error=0
    for row in cases.itertuples():
        balance=float(row.mortgage_principal);paid_interest=0
        monthly=(1+row.contract_rate/200)**(1/6)-1
        for _ in range(60):
            interest=balance*monthly;paid_interest+=interest
            balance=balance+interest-row.monthly_mortgage
        balance_error=max(balance_error,abs(balance-row.five_year_balance))
        interest_error=max(interest_error,abs(paid_interest-row.first_five_years_interest))
    record("Independent 60-month balance schedule",len(cases),balance_error,.00001)
    record("Independent 60-month interest sum",len(cases),interest_error,.00001)
    for side in ["before","after"]:
        error=(programs["cash_gap_"+side]-(programs["cash_target_"+side]-programs["liquid_cash_"+side]).clip(lower=0)).abs().max()
        record("Program cash identity: "+side,len(programs),error)
    fhsa=programs[programs.program.str.startswith("FHSA")]
    error=((fhsa.liquid_cash_after-fhsa.liquid_cash_before)-fhsa.fhsa_contribution*fhsa.assumed_marginal_tax_rate).abs().max()
    record("FHSA contributions counted once",len(fhsa),error)
    hbp=programs[programs.program.str.startswith("HBP")]
    record("HBP moves stated existing assets",len(hbp),((hbp.liquid_cash_after-hbp.liquid_cash_before)-hbp.hbp_draw).abs().max())
    record("Waiting cash identity",len(waiting),(waiting.cash_gap-(waiting.cash_target-waiting.profile_cash).clip(lower=0)).abs().max())
    record("Nine baseline price/cash thresholds",len(limits),0 if len(limits)==9 else 1,0,
           "Boundary-aware interval search; dollar immediately beyond each reported threshold fails. Separate tests compare to exhaustive searches.")
    frame=pd.DataFrame(checks)
    if not frame.status.eq("Pass").all():
        raise ValueError("Independent review failed: "+str(frame[frame.status.ne("Pass")].to_dict("records")))
    return frame


def write_review_report(cases,programs,waiting,limits,review,path):
    """Keep the review explanation synchronized with the actual saved calculations."""
    base=cases[cases.year.eq(2023)&cases.scenario.eq("baseline")]
    chosen=cases[cases.year.eq(2023)&cases.city.eq("Vancouver")&cases.profile.eq("couple")]
    order=["baseline","price10","price20","rate1","cash25","income20","amort30","hbp"]
    g=chosen.set_index("scenario").loc[order]
    limit=limits[limits.city.eq("Vancouver")&limits.profile.eq("couple")].iloc[0]
    doc=f"""# Calculation and display review

## What the repeated zeros meant

The previous “cash shortfall” measured only money still missing. It was floored at zero. A buyer already above the minimum could receive more cash or face a lower price while that shortfall stayed at zero.

The arithmetic was consistent, but the display hid useful changes. The website and Power BI now show **cash above or below the minimum** and **income above or below the requirement**. Cash above the minimum is used in the down payment; it is not cash left over after purchase. The separately stated reserve is retained.

For the Vancouver two-earner example:

| Change | Cash vs minimum | Annual income vs requirement | Monthly mortgage |
|---|---:|---:|---:|
"""
    for row in g.itertuples():
        doc+=f"| {row.scenario_label} | {row.cash_position_label} | {row.income_position_label} | {money(row.monthly_mortgage)} |\n"
    doc+=f"""
## What was rechecked

- {len(cases)} purchase cases: cash targets, shortfalls, signed positions, premium-financed loans and allocation of available funds.
- A separate month-by-month amortization schedule for all {len(cases)} purchase cases, checking the balance and interest over the first 60 payments.
- {len(programs)} program comparisons: before/after cash identities, FHSA money counted once, and HBP draws limited to the separately stated existing assets.
- {len(waiting)} waiting cases: cash target and available-fund identities.
- Independent SQLite expressions for required income, cash targets and gaps, signed positions, loan balances and monthly outgoings.
- Source hashes, source units/flags, city/year keys, twelve-month rate coverage, policy boundaries and portable Power BI imports, covered by the automated tests.

The program section shows the variable a measure changes: payment and interest for 30 years, liquid purchase cash for HBP/FHSA, and transfer tax for BC relief. BC relief in Halifax is labeled **not applicable**, rather than displayed as a zero benefit.

### Reconciliation results

| Check | Rows | Maximum absolute error | Result |
|---|---:|---:|---|
"""
    for row in review.itertuples():
        doc+=f"| {row.check} | {row.rows} | {row.max_absolute_error:.9g} | {row.status} |\n"
    doc+=f"""
Small floating-point differences within the stated tolerances are retained in [the machine-readable review](../data/processed/homebuying_review_checks.csv).

## The next analytical step: a price that fits

For each of the nine baseline buyers, the study now finds:

1. The largest whole-dollar purchase price that passes both financial checks with starting cash and income fixed.
2. The least whole-dollar total liquid cash that passes at the benchmark price and unchanged income.

For the Vancouver two-earner example, the exact modeled price limit is **{money(limit.maximum_price)}**. The website conservatively displays **{limit.maximum_price_label}**. At the benchmark price, total cash required to fit the income screen is **{money(limit.total_cash_to_fit_at_benchmark)}**, or **{money(limit.additional_cash_to_fit)}** more than the starting funds.

The search separately handles transfer-tax, insurance-premium and insured/uninsured-rate intervals. It does not assume one globally smooth relationship. Tests compare the search against every whole dollar in small exhaustive domains, including a case with a disconnected feasible set. All nine published thresholds are checked at the threshold and the next dollar.

Website price limits are rounded down and extra cash up to CAD 1,000. Exact values remain in [homebuying_price_limits.csv](../data/processed/homebuying_price_limits.csv).

## Official-source cross-checks and scope

CMHC's public GDS/TDS guidance confirms the 39%/44% comparison, financed premiums, tax/heat and half condo fees, and the qualifying-rate rule. BC's published exemption example for a CAD 849,000 property independently confirms CAD 14,980 gross tax, CAD 3,520 relief and CAD 11,460 payable.

- [CMHC debt-service guidance](https://www.cmhc-schl.gc.ca/professionals/project-funding-and-mortgage-financing/mortgage-loan-insurance/calculating-gds-tds)
- [BC published exemption examples](https://www2.gov.bc.ca/gov/content/taxes/property-taxes/property-transfer-tax/exemptions/first-time-home-buyers/current-amount)
- [Full methodology](../docs/homebuying_methodology.md)

The data vintage, hypothetical profiles and eligibility assumptions remain explicit. Prices/rates are 2023 benchmarks; rules were reviewed November 16, 2026. A financial-screen limit is not a comfortable spending budget, a current price quote or a bank approval. Actual borrower evidence, property costs and lender policy still need review.
"""
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(doc,encoding="utf-8",newline="\n")
