"""Build a portable, imported ten-page Power BI project from the saved desktop study."""
from pathlib import Path
import json
import shutil
from datetime import datetime
import pandas as pd
import build_powerbi as b

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/processed"; BI=ROOT/"powerbi"
REPORT=BI/"HomebuyingBarriers.Report";MODEL=BI/"HomebuyingBarriers.SemanticModel"
PAGES=[("answer","Start here"),("cash","Cash and income"),("changes","What helps"),("limits","Price limits"),
       ("latest","Latest rates"),("history","Over time"),("waiting","Waiting to buy"),("audit","Bank audit"),("calculation_audit","Calculation audit"),("file_review","File review")]
MONEY='"CAD "#,0;("CAD "#,0)'

def frame(name):
    data=pd.read_csv(OUT/name).fillna("")
    for c in data.select_dtypes(include="bool"):data[c]=data[c].astype(int)
    return data

def proj(t,c,kind="Column"):
    p=b.projection(t,c,kind)
    p["displayName"]={"city":"City","profile_label":"Buyer example","scenario_label":"Change",
        "cash_target":"Cash target + reserve","profile_cash":"Profile cash","cash_gap":"Cash shortfall",
        "profile_income":"Profile gross income","required_gross_income":"Income needed/year",
        "income_gap":"Income shortfall/year","barrier":"Modeled result","year":"Year","months":"Months",
        "factor":"Input","contribution_cad":"Contribution (CAD)","program":"Buyer measure",
        "required_income_after":"Income needed after/year","monthly_payment_after":"Monthly payment after",
        "five_year_interest_after":"First-five-year interest after","control":"Review objective",
        "status":"Review result","result":"Calculation / assumption","evidence_needed":"Evidence still needed",
        "buyer_family_median_income":"Observed buyer-family median","review_conclusion":"Review conclusion",
        "cash_position_label":"Cash vs minimum","income_position_label":"Income vs requirement/year","result_label":"Financial screen",
        "Cash position":"Cash vs minimum","Income position":"Income vs requirement",
        "metric_1_label":"Measure affected","metric_1_before":"Before","metric_1_after":"After",
        "benchmark_price":"2023 benchmark price","maximum_price_display":"Price within both checks",
        "additional_cash_display":"Extra cash at benchmark","total_cash_to_fit_at_benchmark":"Total cash needed at benchmark",
        "baseline_required_income":"Income needed: 2023 rates","baseline_monthly_mortgage":"Payment: 2023 rates",
        "stage_label":"Review stage","financial_result":"Financial result","finding":"Input","declared_label":"Application","supported_label":"Mock support","difference_label":"Difference","evidence_ids":"Worksheet IDs",
        "variant_label":"Calculation","income_understated":"Income understated/year","decision_label":"Audit result",
        "contract_rate":"Contract rate (%)","qualifying_rate":"Qualifying rate (%)",
        "price_growth_label":"Hypothetical price path","rent_growth_label":"Rent growth"}.get(c,c)
    return p

def text(p,name,x,y,w,h,content,size=13):b.text(p,name,x,y,w,h,content,size)
def table(p,name,x,y,w,h,title,t,cols):
    b.visual(p,name,"tableEx",x,y,w,h,title,{"Values":[proj(t,c,k) if isinstance(c,str) else c for c,k in [(v,"Column") if isinstance(v,str) else v for v in cols]]},
             objects={"total":[{"properties":{"totals":b.literal(False)}}]})
def slicer(p,name,x,w,t,c,title):
    b.visual(p,name,"slicer",x,125,w,120,title,{"Values":[proj(t,c)]},
             objects={"selection":[{"properties":{"singleSelect":b.literal(True),"selectAllCheckboxEnabled":b.literal(False)}}]})
def header(p,title,subtitle):
    text(p,"header",24,12,1232,62,title,25)
    text(p,"subtitle",24,80,1232,38,subtitle,12)
def foot(p,content):
    text(p,"scope",24,662,1232,52,content,10)

def build():
    b.BI=BI;b.REPORT=REPORT;b.MODEL=MODEL
    if REPORT.exists() or MODEL.exists():
        backup=ROOT/".powerbi_cache_backup"/("homebuying_"+datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        backup.mkdir(parents=True)
        for path in [REPORT,MODEL]:
            if path.exists():shutil.move(str(path),str(backup/path.name))
    cases=frame("homebuying_cases.csv");cases=cases[cases.year.eq(2023)].copy()
    order=["baseline","price10","price20","rate1","cash25","income20","amort30","hbp","no_relief","no_reserve","assess75","assess125","costs_high"]
    cases["scenario_order"]=cases.scenario.map({name:i for i,name in enumerate(order)})
    baseline=cases[cases.scenario.eq("baseline")].copy()
    compare=cases[cases.scenario.isin(["baseline","price10","price20","rate1","cash25","income20","amort30","hbp"])].copy()
    history=frame("homebuying_history.csv")
    programs=frame("homebuying_programs.csv");programs=programs[programs.applicable.eq(1)]
    limits=frame("homebuying_price_limits.csv")
    waiting=frame("homebuying_waiting.csv")
    waiting["price_growth_label"]=waiting.annual_price_growth.map({-.05:"Price -5%/year",0:"Flat prices",.05:"Price +5%/year"})
    waiting["rent_growth_label"]=waiting.annual_rent_growth.map({0:"0%",.03:"3%",.06:"6%"})
    audit=frame("homebuying_bank_audit.csv");controls=frame("homebuying_controls.csv")
    latest=frame("homebuying_latest_rates.csv")
    latest_limits=frame("homebuying_latest_rate_limits.csv")
    errors=frame("homebuying_calculation_audit.csv")
    errors["scenario_order"]=errors.scenario.map({name:i for i,name in enumerate(order)})
    file_stages=frame("mortgage_file_stages.csv");file_findings=frame("mortgage_file_findings.csv")
    decomp=frame("homebuying_decomposition.csv")
    summary=json.loads((OUT/"homebuying_summary.json").read_text(encoding="utf-8"))
    profiles=pd.DataFrame(summary["profiles"])[["id","name","gross_income","liquid_cash","monthly_debt"]].rename(columns={"id":"profile","name":"profile_label"})
    markets=pd.DataFrame({"city":summary["cities"]})
    tables=[]
    measures=[b.measure(label,f'IF(HASONEVALUE(\'Cases\'[case_id]), MAX(\'Cases\'[{col}]))',MONEY) for label,col in [
        ("Cash target","cash_target"),("Available cash","profile_cash"),("Cash shortfall","cash_gap"),("Cash position","cash_position"),
        ("Income needed","required_gross_income"),("Profile income","profile_income"),("Income shortfall","income_gap"),("Income position","income_position"),
        ("Monthly outgoings","modeled_monthly_outgoings"),("Mortgage payment","monthly_mortgage")]]
    measures.append(b.measure("Selected result",'IF(HASONEVALUE(\'Cases\'[case_id]), SELECTEDVALUE(\'Cases\'[result_label]), "Choose one city, buyer and scenario")',""))
    for m in measures:
        if m["name"] in ["Cash position","Income position"]:
            m["formatString"]='"+CAD "#,0;"-CAD "#,0;"CAD 0"'
    sources=[("Markets",markets,None),("Profiles",profiles,None),("Cases",cases,measures),
             ("Baseline",baseline,None),("Comparisons",compare,None),
             ("History",history,[b.measure("Modeled income needed","MAX(\'History\'[required_gross_income])",MONEY),b.measure("Observed buyer-family income","MAX(\'History\'[buyer_family_median_income])",MONEY)]),
             ("Programs",programs,None),("Waiting",waiting,[b.measure("Required gross income","MAX(\'Waiting\'[required_gross_income])",MONEY)]),
             ("Audit",audit,None),("Controls",controls,None),("Decomposition",decomp,None),("Limits",limits,None),
             ("LatestRates",latest,None),("LatestRateLimits",latest_limits,None),("CalculationAudit",errors,None),("FileStages",file_stages,None),("FileFindings",file_findings,None)]
    for name,df,ms in sources:
        t=b.table(name,df,ms)
        for c in t["columns"]:
            col=c["name"]
            if c["dataType"] in ["double","int64"]:
                if any(k in col for k in ["income","cash","payment","interest","price","down","tax","mortgage","reserve","balance","contribution_cad"]) and not any(k in col for k in ["rate","pct","ratio","pass","growth","year","months"]):
                    c["formatString"]=MONEY
                elif col in ["year","months"]:c["formatString"]="0"
                if col.startswith("metric_") and (col.endswith("_before") or col.endswith("_after")):
                    c["formatString"]=MONEY
        if name=="Cases":
            next(c for c in t["columns"] if c["name"]=="scenario_label")["sortByColumn"]="scenario_order"
        if name=="CalculationAudit":
            next(c for c in t["columns"] if c["name"]=="variant_label")["sortByColumn"]="variant_order"
            next(c for c in t["columns"] if c["name"]=="scenario_label")["sortByColumn"]="scenario_order"
        if name=="FileStages":next(c for c in t["columns"] if c["name"]=="stage_label")["sortByColumn"]="stage_order"
        if name=="FileFindings":next(c for c in t["columns"] if c["name"]=="finding")["sortByColumn"]="finding_order"
        tables.append(t)
    rel=[]
    for name,df,_ in sources:
        if name not in ["Markets","Profiles"] and "city" in df:
            rel.append({"name":name+"_city","fromTable":name,"fromColumn":"city","toTable":"Markets","toColumn":"city","crossFilteringBehavior":"oneDirection"})
        if name not in ["Profiles","History"] and "profile" in df:
            rel.append({"name":name+"_profile","fromTable":name,"fromColumn":"profile","toTable":"Profiles","toColumn":"profile","crossFilteringBehavior":"oneDirection"})
    b.write(MODEL/"model.bim",{"name":"HomebuyingBarriers","compatibilityLevel":1600,"model":{
        "culture":"en-US","defaultPowerBIDataSourceVersion":"powerBI_V3","sourceQueryCulture":"en-CA",
        "tables":tables,"relationships":rel,"annotations":[{"name":"PBI_QueryOrder","value":json.dumps([t["name"] for t in tables])}]}})
    b.write(MODEL/"definition.pbism",{"version":"1.0","settings":{}})
    b.write(REPORT/"definition.pbir",{"$schema":b.BASE+"item/report/definitionProperties/2.0.0/schema.json","version":"4.0","datasetReference":{"byPath":{"path":"../HomebuyingBarriers.SemanticModel"}}})
    b.write(BI/"HomebuyingBarriers.pbip",{"$schema":b.BASE+"pbip/pbipProperties/1.0.0/schema.json","version":"1.0","artifacts":[{"report":{"path":"HomebuyingBarriers.Report"}}],"settings":{"enableAutoRecovery":True}})
    report=json.loads((BI/"HouseholdFinance.Report/definition/report.json").read_text(encoding="utf-8"))
    b.write(REPORT/"definition/report.json",report)
    b.write(REPORT/"definition/version.json",{"$schema":b.BASE+"item/report/definition/versionMetadata/1.0.0/schema.json","version":"2.0.0"})
    theme=json.loads((BI/"theme.json").read_text(encoding="utf-8"));theme["name"]="Homebuying Barriers"
    b.write(REPORT/"StaticResources/RegisteredResources/HouseholdTheme.json",theme)
    pages=REPORT/"definition/pages"
    b.write(pages/"pages.json",{"$schema":b.BASE+"item/report/definition/pagesMetadata/1.0.0/schema.json","pageOrder":[p for p,_ in PAGES],"activePageName":"answer"})
    for name,label in PAGES:
        b.write(pages/name/"page.json",{"$schema":b.BASE+"item/report/definition/page/1.0.0/schema.json","name":name,"displayName":label,"displayOption":"FitToPage","width":1280,"height":720,
             "objects":{"background":[{"properties":{"color":{"solid":{"color":b.literal("#F2F5F4")}},"transparency":b.literal(0)}}]}})
    header("answer","Why does buying a home still feel out of reach?","Question: Is the down payment really the biggest obstacle to buying a home?")
    text("answer","answer",24,125,1232,88,"Four of nine examples have enough cash.\nTheir income still falls short.",21)
    table("answer","baseline",24,227,1232,300,"Nine hypothetical buyers | latest comparable transaction benchmark: 2023","Baseline",
          ["city","profile_label","cash_target","profile_cash","required_gross_income","profile_income","barrier"])
    text("answer","bank",24,548,1232,85,"Banking audit: a cash-ready claim is not enough to sign off a mortgage file. Recalculate debt service and verify income, funds, debts, property costs and eligibility.",17)
    foot("answer","Observed: 2023 first-time-buyer city transaction medians and national rate benchmarks. Assumed: buyer finances and property costs. Rules reviewed Nov 16, 2026. Illustrations, not population estimates, current listings or approvals.")
    header("cash","Which hurdle binds: cash or income?","Choose one city, one buyer and one scenario. Amounts are nominal CAD; income is annual gross.")
    slicer("cash","city",24,260,"Markets","city","City")
    slicer("cash","profile",307,330,"Profiles","profile_label","Buyer example")
    slicer("cash","scenario",660,595,"Cases","scenario_label","Change one assumption")
    table("cash","cash-values",24,260,1232,110,"Purchase cash including the stated emergency reserve","Cases",
          [("Available cash","Measure"),("Cash target","Measure"),("Cash position","Measure")])
    table("cash","income-values",24,393,1232,110,"Income under the stress-test screen","Cases",
          [("Profile income","Measure"),("Income needed","Measure"),("Income position","Measure"),("Selected result","Measure")])
    table("cash","payments",24,524,1232,100,"Monthly contract payment and modeled outgoings","Cases",[("Mortgage payment","Measure"),("Monthly outgoings","Measure")])
    foot("cash","Positive position is above the requirement; negative is short. Extra cash reduces the loan while the reserve stays aside. The income check is conditional on having minimum cash if funds are short. Actual lender criteria and verified evidence remain necessary.")
    header("changes","What changes the result?","Each sensitivity changes one baseline assumption. Buyer measures are conditional on eligibility.")
    slicer("changes","city",24,350,"Markets","city","City");slicer("changes","profile",398,400,"Profiles","profile_label","Buyer example")
    text("changes","note",824,118,430,105,"Keep price, rates, income and cash separate. A change helps only if the remaining constraint is also resolved.",14)
    table("changes","compare",24,247,1232,240,"One change at a time","Comparisons",["scenario_label","cash_position_label","income_position_label","result_label"])
    table("changes","programs",24,508,1232,136,"The main effect of each buyer measure | before and after","Programs",["program","metric_1_label","metric_1_before","metric_1_after","required_income_after"])
    foot("changes","HBP moves existing RRSP assets; it is not new wealth and requires future repayment. FHSA compares identical 12-month saving with only an assumed 30% tax refund added. Thirty-year insured resale case assumes first-time eligibility and includes the premium surcharge.")
    header("history","Why did the income hurdle rise?","Minimum-down market comparison, 2020–2023. Buyer-family income is context, not borrower eligibility.")
    slicer("history","city",24,350,"Markets","city","City")
    text("history","vintage",399,119,855,105,"Dashed 2020 context on the website marks the 2016/2021 geography boundary. Current mortgage rules and the 2023 tax schedule are held fixed. Changing property and buyer mix limits comparison.",13)
    b.visual("history","trend","lineChart",24,248,790,385,"Annual gross income (CAD)",{
        "Category":[proj("History","year")],"Y":[proj("History","Modeled income needed","Measure"),proj("History","Observed buyer-family income","Measure")]},b.field("History","year"))
    table("history","contributions",841,248,413,275,"2021–2023 change: input contributions","Decomposition",["factor","contribution_cad"])
    text("history","decomp-note",841,540,413,99,"Contributions reconcile exactly across all six replacement orders. This is a descriptive decomposition of required income minus buyer-family median income, not a causal estimate.",11)
    foot("history","Statistics Canada 46-10-0062-01 (2020) and 46-10-0099-01 (2021–2023); Bank of Canada funds advanced, fixed five years and over. Annual arithmetic mean of 12 monthly averages. No current offered rate or 2026 price is implied.")
    header("waiting","Does waiting to save bring the home closer?","Hypothetical price paths: -5%, 0%, +5% per year. Income and rates stay fixed; no probabilities.")
    slicer("waiting","city",24,310,"Markets","city","City");slicer("waiting","profile",357,410,"Profiles","profile_label","Buyer example")
    slicer("waiting","rent",790,465,"Waiting","rent_growth_label","Annual rent growth")
    b.visual("waiting","paths","lineChart",24,248,1232,385,"Gross income needed after more time saving (CAD)",{
        "Category":[proj("Waiting","months")],"Series":[proj("Waiting","price_growth_label")],"Y":[proj("Waiting","Required gross income","Measure")]},b.field("Waiting","months"))
    foot("waiting","12/24 months from the 2023 benchmark. Incremental rent reduces initially stated net saving; cash earns zero interest. Home prices, minimum down, transfer tax and loan insurance are recalculated. This is not a forecast or a recommendation to buy or wait.")
    header("audit","Would this mortgage file pass a first review?","Fictional borrower. Distinguish a checked calculation from verified evidence before sign-off.")
    slicer("audit","city",24,350,"Markets","city","City");slicer("audit","profile",398,400,"Profiles","profile_label","Buyer example")
    text("audit","hold",824,118,430,110,"Review outcome: hold pending evidence.\nA modeled income exception also needs resolution. No baseline case is labeled a verified approval.",14)
    table("audit","workpaper",24,248,1232,385,"Audit working paper | selected baseline case","Audit",["control","status","result","evidence_needed"])
    foot("audit","Public OSFI B-20 informs documentation and independent review. CMHC-style 39%/44% screen is a comparison, not TD policy or a universal uninsured lender limit. Python/SQL arithmetic agrees; income, funds, debts, valuation, costs and eligibility remain unverified.")
    header("limits","What purchase price fits the starting finances?","Baseline only. Choose one city and buyer; rates, costs and the emergency reserve stay fixed.")
    slicer("limits","city",24,350,"Markets","city","City");slicer("limits","profile",398,400,"Profiles","profile_label","Buyer example")
    text("limits","explanation",824,118,430,110,"Two alternatives: change the purchase price, or bring more cash while keeping the benchmark price and starting income.",14)
    table("limits","price-limit",24,263,1232,124,"Keep starting cash and income: a purchase price within both financial checks","Limits",["benchmark_price","profile_cash","profile_income","maximum_price_display"])
    table("limits","cash-limit",24,420,1232,124,"Alternatively, keep the benchmark price and income: cash needed","Limits",["benchmark_price","profile_cash","total_cash_to_fit_at_benchmark","additional_cash_display"])
    text("limits","meaning",24,566,1232,70,"Cash includes down payment, closing allowance and the stated reserve. The alternatives are calculated separately. Actual borrower records, property costs and lender policy still need review.",15)
    foot("limits","Prices are rounded down and extra cash up to CAD 1,000. Based on 2023 price/rate benchmarks and rules reviewed Nov 16, 2026. This is a financial-screen limit, not a comfortable-spending budget or mortgage approval.")
    fresh=json.loads((OUT/"homebuying_source_freshness.json").read_text(encoding="utf-8"))
    header("latest","Do newer mortgage rates solve the income hurdle?","Same 2023 price, tax schedule and buyer finances. Change only the mortgage-rate benchmark.")
    slicer("latest","city",24,350,"Markets","city","City");slicer("latest","profile",398,400,"Profiles","profile_label","Buyer example")
    text("latest","period",824,118,430,110,"Latest common rate month: "+fresh["rate_period"]+"\nInsured "+format(fresh["insured_rate"],".2f")+"%; uninsured "+format(fresh["uninsured_rate"],".2f")+"%. Sources checked "+fresh["checked_on"]+".",14)
    table("latest","income-comparison",24,263,1232,124,"Annual gross income: matched baseline vs newer-rate scenario","LatestRates",["baseline_required_income","required_gross_income","income_position_label","result_label"])
    table("latest","payment-comparison",24,420,1232,110,"Contract monthly payment: same purchase price and cash","LatestRates",["baseline_monthly_mortgage","monthly_mortgage","contract_rate","qualifying_rate"])
    table("latest","price-comparison",24,554,1232,82,"Financial-screen price limit under the newer-rate scenario","LatestRateLimits",["maximum_price_display"])
    foot("latest","Rate sensitivity, not observed current affordability. The latest reviewed StatsCan release still uses 2023 buyer transactions/income. Newer monthly national rates are not an annual mean or an individual offer. Historical tax schedule and profile assumptions remain fixed.")
    header("calculation_audit","Could a calculation mistake change the decision?","Compare the correct calculation with four deliberately flawed variants. Each error is introduced separately.")
    slicer("calculation_audit","city",24,260,"Markets","city","City")
    slicer("calculation_audit","profile",307,330,"Profiles","profile_label","Buyer example")
    slicer("calculation_audit","scenario",660,595,"CalculationAudit","scenario_label","Audit this saved scenario")
    table("calculation_audit","error-comparison",24,263,1232,345,"Correct and deliberately flawed income screens","CalculationAudit",["variant_label","required_gross_income","income_understated","decision_label"])
    text("calculation_audit","worked-example",24,614,1232,38,"Try Vancouver / Two earners / Price 10% lower: using the contract rate to qualify creates a false pass.",12)
    foot("calculation_audit","False pass: the flawed result fits both financial checks while the correct one does not. Cash stays unchanged. Demonstrations are not observed bank mistakes or a bank error rate. Actual borrower evidence, property costs and lender/insurer policy still require review.")
    header("file_review","Can this mortgage file be signed off?","FICTIONAL TRAINING FILE. Constructed application and worksheets; no genuine borrower evidence or lender approval.")
    table("file_review","stages",24,130,1232,182,"One file: submitted claim, corrected review and a separate lower-price request","FileStages",["stage_label","price","profile_income","required_gross_income","financial_result"])
    table("file_review","findings",24,334,1232,264,"Seven discrepancies reconciled to the mock worksheets","FileFindings",["finding","declared_label","supported_label","difference_label","evidence_ids"])
    text("file_review","outcome",24,612,1232,43,"Final review: HOLD. The CAD 600,000 request fits both financial checks; six external-evidence controls remain open.",14)
    foot("file_review","The revised request changes only the hypothetical price; supported finances stay fixed and the historical tax proxy is recalculated. Original price: 2023 scenario; rate reference: Sep 2026. Mock worksheet agreement is not authentic evidence or sign-off. See the eight-page training packet.")
    # Structural checks before opening the native application.
    model_tables={t["name"]:{c["name"] for c in t["columns"]}|{m["name"] for m in t.get("measures",[])} for t in tables}
    def walk(value):
        if isinstance(value,dict):
            for kind in ["Column","Measure"]:
                if kind in value:
                    f=value[kind];entity=f["Expression"]["SourceRef"]["Entity"]
                    assert f["Property"] in model_tables[entity],(entity,f["Property"])
            for v in value.values():walk(v)
        elif isinstance(value,list):
            for v in value:walk(v)
    for path in REPORT.rglob("*.json"):walk(json.loads(path.read_text(encoding="utf-8")))
    (ROOT/"work/homebuying_powerbi_build.json").write_text(json.dumps({"passed":True,"pages":[label for _,label in PAGES],"tables":len(tables),"case_rows":len(cases),"portable_import":True},indent=2),encoding="utf-8")
    print("Built portable ten-page Power BI project:",BI/"HomebuyingBarriers.pbip",flush=True)
if __name__=="__main__":build()
