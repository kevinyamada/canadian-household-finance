"""Export the fictional mortgage-file exercise as an eight-page, clearly labelled packet."""
from pathlib import Path
import hashlib,json,textwrap,zipfile
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from homebuying_data import ROOT
from homebuying_review import money

DEST=ROOT/"reports/mortgage_file"
OUT=ROOT/"data/processed"
def amount(n,digits=0):return f"CAD {n:,.{digits}f}"
def page(title,intro,headers,rows,notes,widths=None):
    fig=plt.figure(figsize=(8.27,11.69),facecolor="white")
    fig.text(.07,.955,"FICTIONAL TRAINING FILE",fontsize=10,color="#a34f41",weight="bold")
    fig.text(.07,.924,title,fontsize=18,color="#1c2d29",weight="bold",va="top")
    fig.text(.07,.865,textwrap.fill(intro,104),fontsize=9,color="#40564f",va="top",linespacing=1.5)
    widths=widths or [1/len(headers)]*len(headers)
    wrap=lambda row:["\n".join(textwrap.fill(part,max(9,int(w*84)),break_long_words=True) for part in str(v).splitlines()) for v,w in zip(row,widths)]
    cells=[wrap(r) for r in rows];labels=wrap(headers)
    line_count=sum(max(c.count("\n")+1 for c in r)+1 for r in [labels,*cells])
    height=min(.55,max(.22,.024*line_count))
    ax=fig.add_axes([.07,.785-height,.86,height]);ax.axis("off")
    table=ax.table(cellText=cells,colLabels=labels,cellLoc="left",colLoc="left",
                   colWidths=widths,bbox=[0,0,1,1])
    table.auto_set_font_size(False);table.set_fontsize(8.2)
    for (r,c),cell in table.get_celld().items():
        cell.set_edgecolor("#d7dfda");cell.set_linewidth(.5);cell.PAD=.08
        if r==0:cell.set_facecolor("#edf2ef");cell.set_text_props(weight="bold",color="#1c2d29")
    fig.text(.07,.785-height-.04,textwrap.fill(notes,110),fontsize=8.1,color="#40564f",va="top",linespacing=1.45)
    fig.text(.07,.065,"Constructed worksheets only. No genuine bank/employer records, customer data, signature or approval.",fontsize=7.4,color="#a34f41")
    fig.text(.07,.043,"TRAINING-MORTGAGE-001 | CAD | Kevin Yamada | Public Canadian guidance; explicit scenario assumptions",fontsize=7.1,color="#54635e")
    return fig

def export():
    DEST.mkdir(parents=True,exist_ok=True)
    (ROOT/"work").mkdir(exist_ok=True)
    data=json.loads((ROOT/"docs/assets/mortgage-file-data.json").read_text(encoding="utf-8"))
    case=data["case"];stages=data["stages"];findings=data["findings"];app=case["application"];cost=case["cost_worksheet"]
    correct=stages[1];revised=stages[2];pages=[]
    pages.append(page("Can this file be signed off?",
        "One fixed Vancouver training file. Follow the claim, reconcile seven discrepancies, then assess a separately revised request. None of the worksheets authenticates real evidence.",
        ["Stage","Price","Gross income / year","Income needed / year","Financial result"],
        [[r["stage_label"],money(r["price"]),money(r["profile_income"]),money(r["required_gross_income"]),r["financial_result"]] for r in stages],
        "Outcome: hold. The revised request fits both modeled financial checks, but six external-evidence controls remain open. Financial fit is separate from verified borrower, property and lender evidence.",[.20,.17,.19,.19,.25]))
    pages.append(page("APP-001 | Submitted application",
        "Applicant A and Applicant B are fictional labels. The request and calculation below deliberately contain issues for the exercise. This is not a bank application form.",
        ["Declared input","Submitted claim"],
        [["Purchase price",money(app["requested_price"])],["Gross income / year",money(app["gross_income"])],
         ["Liquid cash",money(app["liquid_cash"])],["Other debt / month",money(app["monthly_debt"])],
         ["Property tax / year",amount(app["annual_property_tax"],2)],["Heat / month",money(app["heating"])],
         ["Condo fees / month",money(app["condo_fee"])],["Rate used to qualify",f'{app["qualifying_rate_used"]:.2f}% — intentionally incorrect']],
        "The price is a hypothetical 10%-lower scenario from the preserved 2023 Vancouver benchmark, not a current property listing. A seeded qualifying-rate mistake is part of the submitted claim.",[.52,.48]))
    pages.append(page("INC-001 | Income worksheet",
        "Constructed income schedule. The exercise includes recurring base salary and excludes an isolated bonus whose sustainable recurrence is not established.",
        ["Worksheet ID","Applicant / type","Annual gross","Exercise treatment"],
        [[r["evidence_id"],r["applicant"]+" / "+r["kind"].replace("_"," "),money(r["annual_gross"]),"Include recurring base" if r["kind"]=="base" else "Exclude one-off amount"] for r in case["income_records"]],
        "Base salary total used: "+money(correct["profile_income"])+". Declared income included the one-off bonus. This conservative treatment is explicit; it is not a claim that all bonus income is ineligible. Actual income/employment and normalization criteria still require independent verification.",[.20,.29,.20,.31]))
    pages.append(page("FND-001 | Funds worksheet",
        "Constructed source-of-funds schedule. Only funds assumed available before closing enter the modeled cash budget. Ownership and actual availability remain unverified.",
        ["Worksheet ID","Account","Balance","Pledged / unavailable","Counted"],
        [[r["evidence_id"],r["account"],money(r["balance"]),money(r["pledged"]),money(r["balance"]-r["pledged"])] for r in case["fund_records"]],
        "Available funds used: "+money(correct["profile_cash"])+". Deduct the pledged amount once. The model retains a separate "+money(cost["reserve"])+" reserve and "+money(cost["closing_allowance"])+" closing allowance. No new gift, savings or borrowed down-payment funds are invented.",[.18,.24,.19,.20,.19]))
    pages.append(page("DBT-001 | Debt worksheet",
        "Constructed recurring obligations. The application declared only the first two payments. The review includes the omitted third obligation in TDS.",
        ["Worksheet ID","Obligation","Monthly payment","Declared?"],
        [[r["evidence_id"],r["obligation"],money(r["monthly_payment"]),"Yes" if r["declared"] else "No — discrepancy"] for r in case["debt_records"]],
        "Monthly debt used after reconciliation: "+money(correct["monthly_debt"])+". This worksheet is not a credit-bureau report. An authorized review of a real credit file and all actual obligations remains open.",[.21,.36,.20,.23]))
    pages.append(page("CST-001 / RTE-001 | Costs and rate",
        "Constructed cost and rate worksheets. The tax schedule is historical and uses price as an assessment proxy. National mortgage rates are reference observations, not an individual commitment.",
        ["Input","Amount","Basis"],
        [["Property tax at original request",amount(correct["annual_property_tax"],2),"2023 rate x price proxy"],
         ["Property tax at revised request",amount(revised["annual_property_tax"],2),"Same rate; lower price proxy"],
         ["Heating / month",money(cost["heating"]),"Constructed cost estimate"],
         ["Condo fees / month",money(cost["condo_fee"]),"Half enters GDS/TDS; full fee in outgoings"],
         ["Contract benchmark",f'{correct["contract_rate"]:.2f}%',data["rates"]["period"]+" insured national rate"],
         ["Correct qualifying rate",f'{correct["qualifying_rate"]:.2f}%',"max(contract + 2 points, 5.25%)"],
         ["Amortization","25 years","Exercise assumption"]],
        "A real review requires the actual tax bill, costs, valuation, rate commitment and applicable criteria. Existing program eligibility is assumed for calculation only. Home insurance and maintenance are separately assumed at CAD 100 each per month.",[.37,.23,.40]))
    pages.append(page("Findings | Seven discrepancies",
        "Compare APP-001 with the constructed supporting schedules. Amount differences are supported minus declared; rates use percentage points. Reconcile values before accepting a pass label.",
        ["Finding","Application","Mock support","Difference","Worksheet IDs"],
        [[r["finding"]+"\n"+r["unit"],r["declared_label"],r["supported_label"],r["difference_label"],r["evidence_ids"].replace("|","\n")] for r in findings],
        "All seven numerical discrepancies are corrected in the reviewed stage. Agreement with a mock schedule is not external verification. Full action descriptions and calculation lineage are retained in the CSVs, JSON inputs, Python, SQL and walkthrough.",[.24,.16,.16,.17,.27]))
    pages.append(page("Resolution | Hold pending evidence",
        "The lower-price request changes only the hypothetical price to "+money(revised["price"])+". Recurring income, available cash and debt stay unchanged. Both financial checks fit; actual sign-off remains on hold.",
        ["Open control","What is still required"],
        [[r["control"],r["needed"]] for r in data["open_evidence"]],
        "Reviewer conclusion: do not equate a corrected calculation with an authenticated loan file. Obtain actual evidence, apply the lender's criteria and document an independent review. This exercise supplies no actual decision, signature, default estimate or compliance opinion.",[.31,.69]))
    pdf=DEST/"MortgageFile-Audit-Pack.pdf"
    with PdfPages(pdf) as book:
        for i,fig in enumerate(pages,1):
            fig.text(.89,.043,f"{i} / {len(pages)}",fontsize=7.1,ha="right",color="#54635e")
            if i in [1,7,8]:fig.savefig(ROOT/f"work/mortgage_file_packet_page_{i:02d}.png",dpi=120)
            book.savefig(fig);plt.close(fig)
    readme="""# Fictional mortgage-file audit packet

**FICTIONAL TRAINING FILE.** These are constructed application/support worksheets, not genuine financial records or a lender approval.

The eight-page PDF contains the application, income, funds, debt and cost/rate schedules, seven findings and the resolution with six external-evidence controls still open.

[Open the packet](MortgageFile-Audit-Pack.pdf) · [Walkthrough and resolution](../../docs/mortgage_file_walkthrough.md) · [Scenario inputs](../../data/scenarios/mortgage_file/training_file.json)

The original price is a constructed scenario based on a 2023 benchmark. September 2026 national rates and the historical tax schedule remain explicit assumptions and context. Passing the financial screen is separate from actual evidence verification.
"""
    (DEST/"README.md").write_text(readme,encoding="utf-8",newline="\n")
    files=[pdf,DEST/"README.md",ROOT/"docs/mortgage_file_walkthrough.md",ROOT/"data/scenarios/mortgage_file/training_file.json",
           ROOT/"src/mortgage_file_audit.py",ROOT/"sql/mortgage_file_audit.sql",*OUT.glob("mortgage_file_*.csv")]
    manifest={"synthetic":True,"notice":data["notice"],"pages":8,"assets":[{"file":str(p.relative_to(ROOT)).replace("\\","/"),
        "sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size} for p in files],"execution":"Exported in desktop VS Code"}
    (DEST/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8",newline="\n")
    with zipfile.ZipFile(ROOT/"work/MortgageFile-Audit-Pack.zip","w",zipfile.ZIP_DEFLATED) as archive:
        for p in [*files,DEST/"manifest.json"]:archive.write(p,str(p.relative_to(ROOT)).replace("\\","/"))
    print("Exported eight-page fictional mortgage-file PDF and ZIP.",flush=True)
    return manifest
if __name__=="__main__":export()
