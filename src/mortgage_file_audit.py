"""Reconcile a fictional mortgage application to constructed support worksheets."""
import hashlib,json,sqlite3
from pathlib import Path
import pandas as pd
from homebuying_data import ROOT,CITIES,write_json
from homebuying_model import Buyer,evaluate,number,monthly_payment
from homebuying_review import explain_cases,money
from refresh_homebuying_sources import load_refresh

FIXTURE=ROOT/"data/scenarios/mortgage_file/training_file.json"
OUT=ROOT/"data/processed"
NOTICE="FICTIONAL TRAINING FILE — constructed worksheets, not genuine financial records or a lender approval."
SOURCES={
 "CMHC debt service":"https://www.cmhc-schl.gc.ca/professionals/project-funding-and-mortgage-financing/mortgage-loan-insurance/calculating-gds-tds",
 "OSFI B-20":"https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/residential-mortgage-underwriting-practices-procedures-guideline-2017",
 "Bank of Canada rates":"https://www.bankofcanada.ca/rates/banking-and-financial-statistics/interest-rates-for-new-and-existing-lending-by-chartered-banks/"}

def validate(case,rates):
    if case.get("synthetic") is not True:raise ValueError("Only an explicitly synthetic training file is supported")
    if case["city"]!="Vancouver" or case["province"]!="BC":raise ValueError("This fixed training file is scoped to Vancouver, BC")
    if case["rate_reference_period"]!=rates["period"]:raise ValueError("Review the case before changing the rate vintage")
    ids=[]
    for key,columns in [("income_records",["annual_gross"]),("fund_records",["balance","pledged"]),("debt_records",["monthly_payment"])]:
        if not case[key]:raise ValueError("Missing supporting worksheet")
        for row in case[key]:
            ids.append(row["evidence_id"])
            for col in columns:number(row[col],col)
    if any(r["pledged"]>r["balance"] for r in case["fund_records"]):raise ValueError("Pledged funds exceed the balance")
    if any(r["kind"] not in ["base","one_off_bonus"] for r in case["income_records"]):raise ValueError("Unreviewed income treatment")
    if any(type(r["declared"]) is not bool for r in case["debt_records"]):raise ValueError("Debt flags must be booleans")
    ids += [case[k]["evidence_id"] for k in ["application","cost_worksheet","rate_worksheet","revised_request"]]
    if len(ids)!=len(set(ids)):raise ValueError("Duplicate evidence identifiers")
    for key in ["gross_income","liquid_cash","monthly_debt","annual_property_tax","heating","condo_fee","qualifying_rate_used"]:
        number(case["application"][key],key)
    number(case["application"]["requested_price"],"Requested price",.01)
    number(case["revised_request"]["price"],"Revised price",.01)
    for key in ["heating","condo_fee","home_insurance","maintenance_monthly","closing_allowance","reserve","assessment_ratio"]:
        number(case["cost_worksheet"][key],key)
    if case["cost_worksheet"]["property_tax_rate"]!=CITIES["Vancouver"]["tax_rate"]:raise ValueError("Tax schedule must match the cited historical source")
    if case["rate_worksheet"]["amortization_years"]!=25:raise ValueError("The training request uses 25 years")
    if len({r["control_id"] for r in case["open_evidence"]})!=len(case["open_evidence"]):raise ValueError("Duplicate open controls")

def analyse(case,rates):
    validate(case,rates);app=case["application"];cost=case["cost_worksheet"]
    supported={"gross_income":sum(r["annual_gross"] for r in case["income_records"] if r["kind"]=="base"),
        "liquid_cash":sum(r["balance"]-r["pledged"] for r in case["fund_records"]),
        "monthly_debt":sum(r["monthly_payment"] for r in case["debt_records"]),
        "annual_property_tax":app["requested_price"]*cost["assessment_ratio"]*cost["property_tax_rate"],
        "heating":cost["heating"],"condo_fee":cost["condo_fee"]}
    def buyer(inputs):
        return Buyer("training","Fictional two-earner file",inputs["gross_income"],inputs["liquid_cash"],inputs["monthly_debt"],0,0,
            reserve=cost["reserve"],closing_allowance=cost["closing_allowance"],heating=inputs["heating"],condo_fee=inputs["condo_fee"],
            home_insurance=cost["home_insurance"],maintenance_monthly=cost["maintenance_monthly"])
    def at(price,b,tax_rate):
        return evaluate(price,b,"BC",tax_rate,rates["insured"],rates["uninsured"],assessment_ratio=cost["assessment_ratio"])
    declared,backed=buyer(app),buyer(supported)
    claimed=at(app["requested_price"],declared,app["annual_property_tax"]/app["requested_price"]/cost["assessment_ratio"])
    payment=monthly_payment(claimed["mortgage_principal"],app["qualifying_rate_used"],25)
    housing=payment+app["annual_property_tax"]/12+app["heating"]+.5*app["condo_fee"]
    required=max(housing/.39,(housing+app["monthly_debt"])/.44)*12
    # Seeded application error only: the production evaluate() function is never altered.
    claimed.update(qualifying_rate=app["qualifying_rate_used"],qualifying_payment=payment,housing_costs_for_ratios=housing,
        required_gross_income=required,income_gap=max(0,required-declared.gross_income),income_pass=required-declared.gross_income<=.005,
        gds=housing/(declared.gross_income/12),tds=(housing+declared.monthly_debt)/(declared.gross_income/12))
    corrected=at(app["requested_price"],backed,cost["property_tax_rate"])
    revised=at(case["revised_request"]["price"],backed,cost["property_tax_rate"])
    supported["qualifying_rate_used"]=corrected["qualifying_rate"]
    stages=[]
    for order,(key,label,row,explanation) in enumerate([
        ("submitted","Submitted claim",claimed,"Declared inputs and a deliberately incorrect contract-rate screen. This apparent result is not sign-off."),
        ("corrected","Corrected review",corrected,"Same price. Reconcile recurring income, available funds, all debts, worksheet costs and the qualifying rate."),
        ("revised","Revised request",revised,"Only the hypothetical price changes. Supported finances stay fixed; tax is recalculated using the historical proxy.")]):
        fits=bool(row["cash_pass"] and row["income_pass"])
        row.update(stage_id=key,stage_label=label,stage_order=order,case_id=case["case_id"],synthetic=True,financial_pass=fits,
            external_evidence_verified=False,actual_approval=False,corrected_discrepancies=0 if key=="submitted" else 7,
            open_external_controls=len(case["open_evidence"]),financial_result="Apparent pass (incorrect)" if key=="submitted" and fits else
            "Fits both financial checks" if fits else "Income still short" if row["cash_pass"] else "Cash still short",
            review_outcome="Hold: claim not reconciled" if key=="submitted" else "Hold: external verification remains" if fits else
            "Hold: income exception and external evidence",stage_explanation=explanation,rate_period=rates["period"],notice=NOTICE)
        row["barrier"]="Within modeled limits" if fits else "Income" if row["cash_pass"] else "Cash" if row["income_pass"] else "Both cash and income"
        stages.append(row)
    stages=explain_cases(pd.DataFrame(stages))
    specs=[
        ("Recurring gross income","gross_income","CAD / year","INC-001-A|INC-001-B|INC-001-C",
         "Use recurring base salaries; exclude the isolated bonus under this exercise's conservative treatment. This is not a universal rule that bonuses are ineligible."),
        ("Available purchase cash","liquid_cash","CAD","FND-001-A|FND-001-B",
         "Deduct pledged funds unavailable before closing; count each balance once."),
        ("Other debt payments","monthly_debt","CAD / month","DBT-001-A|DBT-001-B|DBT-001-C",
         "Include the omitted student-loan payment and reconcile all listed obligations."),
        ("Property tax proxy","annual_property_tax","CAD / year","CST-001",
         "Use the historical municipal schedule and stated price-as-assessment proxy. An actual property bill remains necessary."),
        ("Heating","heating","CAD / month","CST-001","Use the supporting estimate; actual heat records or a justified property estimate remain necessary."),
        ("Condo fees","condo_fee","CAD / month","CST-001","Use the full supporting fee; include half in debt-service ratios and the full fee in modeled outgoings."),
        ("Rate used to qualify","qualifying_rate_used","percentage points","RTE-001",
         "Use the greater of contract rate plus two percentage points or 5.25%, rather than the payment's contract rate.")]
    findings=[]
    for order,(label,field,unit,evidence,action) in enumerate(specs,1):
        before=float(app[field]);after=float(supported[field]);difference=after-before
        fmt=lambda n:f"{n:.2f}%" if field=="qualifying_rate_used" else money(n)
        findings.append({"finding_id":f"F-{order:02d}","field":field,"finding":label,"finding_order":order,
            "declared":before,"supported":after,"difference":difference,"unit":unit,"declared_label":fmt(before),"supported_label":fmt(after),
            "difference_label":f"{difference:+.2f} pp" if field=="qualifying_rate_used" else ("+" if difference>=0 else "-")+money(abs(difference)),
            "evidence_ids":evidence,"action":action,"resolution_status":"Corrected in simulation; external verification remains","synthetic":True})
    return stages,pd.DataFrame(findings),supported

def build():
    case=json.loads(FIXTURE.read_text(encoding="utf-8"));manifest,review,rates=load_refresh()
    stages,findings,supported=analyse(case,rates)
    if stages.financial_pass.tolist()!=[True,False,True]:raise ValueError("Review the intended claim/correction/revision story")
    OUT.mkdir(parents=True,exist_ok=True)
    tables={"stages":stages,"findings":findings,"application":pd.DataFrame([case["application"]]),
        "income_records":pd.DataFrame(case["income_records"]),"fund_records":pd.DataFrame(case["fund_records"]),
        "debt_records":pd.DataFrame(case["debt_records"]),"cost_worksheet":pd.DataFrame([case["cost_worksheet"]]),
        "open_evidence":pd.DataFrame(case["open_evidence"])}
    for key,frame in tables.items():
        frame=frame.copy();frame["synthetic"]=True;frame["case_id"]=case["case_id"];tables[key]=frame
        (OUT/("mortgage_file_"+key+".csv")).write_text(frame.to_csv(index=False,lineterminator="\n"),encoding="utf-8",newline="\n")
    with sqlite3.connect(OUT/"mortgage_file.sqlite") as db:
        for key,frame in tables.items():frame.to_sql(key,db,if_exists="replace",index=False)
        db.executescript((ROOT/"sql/mortgage_file_audit.sql").read_text(encoding="utf-8"))
        calculated=pd.read_sql_query("SELECT * FROM supported_finances",db).iloc[0].to_dict()
        for key in ["gross_income","liquid_cash","monthly_debt"]:
            if abs(calculated[key]-supported[key])>1e-7:raise ValueError("Worksheet SQL reconciliation failed")
        check=pd.read_sql_query("SELECT * FROM stage_reconciliation",db)
        if check[[c for c in check if c.endswith("_delta")]].abs().to_numpy().max()>1e-7:raise ValueError("Stage SQL reconciliation failed")
        if pd.read_sql_query("SELECT * FROM finding_reconciliation",db).supported_delta.abs().max()>1e-7:raise ValueError("Evidence lineage failed")
    records=lambda frame:json.loads(frame.to_json(orient="records",double_precision=12))
    payload={"version":1,"case_id":case["case_id"],"synthetic":True,"title":case["title"],"notice":NOTICE,"case":case,
        "stages":records(stages),"findings":records(findings),"open_evidence":case["open_evidence"],"supported_finances":supported,
        "rates":rates,"sources":SOURCES,"summary":{"discrepancies":len(findings),"stages":3,"external_controls_open":len(case["open_evidence"]),
        "outcome":"Financial checks fit after the revised request; actual sign-off stays on hold.",
        "scope":"Only the hypothetical price changes in the revised request. No new income, cash or waived debt is invented.",
        "execution":"Calculated and checked in Kevin's desktop VS Code integrated terminal"}}
    asset=ROOT/"docs/assets/mortgage-file-data.json"
    asset.write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(",",":")),encoding="utf-8",newline="\n")
    write_json(OUT/"mortgage_file_manifest.json",{"synthetic":True,"fixture":"data/scenarios/mortgage_file/training_file.json",
        "fixture_sha256":hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),"asset":"docs/assets/mortgage-file-data.json",
        "asset_sha256":hashlib.sha256(asset.read_bytes()).hexdigest(),"rate_reference_period":rates["period"],
        "official_rate_source_manifest_sha256":hashlib.sha256((ROOT/"data/raw/homebuying_refresh/manifest.json").read_bytes()).hexdigest(),
        "notice":NOTICE,"execution":payload["summary"]["execution"]})
    write_walkthrough(payload)
    print(json.dumps({"mortgage_file":payload["summary"],"stages":records(stages[["stage_id","price","profile_income","profile_cash","monthly_debt","required_gross_income","income_position","financial_result","review_outcome"]])},indent=2))
    return payload

def write_walkthrough(data):
    document="# Can this mortgage file be signed off?\n\n**"+NOTICE+"**\n\n"
    document+="Follow a submitted claim, a corrected review and a revised request. Supporting schedules are constructed worksheets. Agreement with them does not authenticate real records.\n\n"
    document+="## Three stages\n\n| Stage | Price | Gross income / year | Available cash | Debt / month | Income needed / year | Review outcome |\n|---|---:|---:|---:|---:|---:|---|\n"
    for r in data["stages"]:
        document+=f"| {r['stage_label']} | {money(r['price'])} | {money(r['profile_income'])} | {money(r['profile_cash'])} | {money(r['monthly_debt'])} | {money(r['required_gross_income'])} | {r['review_outcome']} |\n"
    document+="\nThe submitted screen deliberately uses the contract rate to qualify. The corrected review uses recurring salary, unpledged funds, all listed debt and supporting cost assumptions. The revised request changes only the hypothetical price. Supported finances stay fixed; the historical tax proxy is recalculated at the new price.\n\n"
    document+="## Findings and resolution trail\n\n| Finding | Application | Mock support | Difference | Worksheet IDs |\n|---|---:|---:|---:|---|\n"
    for r in data["findings"]:document+=f"| {r['finding']} ({r['unit']}) | {r['declared_label']} | {r['supported_label']} | {r['difference_label']} | {r['evidence_ids']} |\n"
    document+="\n"
    for r in data["findings"]:document+=f"- **{r['finding_id']} — {r['finding']}:** {r['action']} Status: {r['resolution_status']}.\n"
    document+="\n## What still prevents sign-off\n\n"
    for r in data["open_evidence"]:document+=f"- **{r['control_id']} — {r['control']}:** {r['needed']}\n"
    document+="\n**Final conclusion:** the revised request fits both modeled financial checks. Keep the file on hold until actual borrower, property and lender evidence is verified and a qualified reviewer signs off. No actual approval, signature or compliance opinion is supplied.\n\n"
    document+="## Inputs and reproduction\n\nThe initial price is a constructed 10%-lower scenario relative to the 2023 Vancouver benchmark, not a current listing. The revised CAD 600,000 price is hypothetical. Costs use the historical tax schedule and a price-as-assessment proxy. September 2026 national rates are not individual offers. Bonus treatment is a conservative exercise assumption, not a universal bank rule.\n\n"
    document+="[Training inputs](../data/scenarios/mortgage_file/training_file.json) · [Saved worksheets and stages](../data/processed) · [Python](../src/mortgage_file_audit.py) · [Independent SQL](../sql/mortgage_file_audit.sql)\n\n"
    for label,url in SOURCES.items():document+=f"- [{label}]({url})\n"
    document+="\nRun src/homebuying_study.py in desktop VS Code to rebuild this exercise with the study. The packet exporter creates an eight-page PDF and ZIP. The website and Power BI display saved results and retain the outstanding evidence checks.\n"
    (ROOT/"docs/mortgage_file_walkthrough.md").write_text(document,encoding="utf-8",newline="\n")
if __name__=="__main__":build()
