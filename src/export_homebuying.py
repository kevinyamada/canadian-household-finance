"""Publish annotated figures and a plain-language brief from the locally saved study."""
from pathlib import Path
import hashlib
import json
import textwrap
import zipfile
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/processed"
DEST=ROOT/"reports/figures/homebuying"
INK="#1c2d29";GREEN="#286c5a";BLUE="#396fa1";RUST="#a34f41";AMBER="#b66b38";PAPER="#fafbf8";MUTED="#54635e"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False,
    "axes.spines.left":False,"axes.spines.bottom":False,"axes.labelcolor":INK,"text.color":INK,
    "xtick.color":MUTED,"ytick.color":MUTED,"axes.facecolor":PAPER,"figure.facecolor":PAPER,"svg.fonttype":"none"})
def cash(v):return f"CAD {v:,.0f}"
def clean(ax):
    ax.set_axisbelow(True);ax.grid(axis="x",color="#d7dfda",linewidth=.6);ax.tick_params(length=0)
def frame(title,subtitle,cols=1,rows=1):
    fig,axes=plt.subplots(rows,cols,figsize=(12,7.5),squeeze=False)
    fig.suptitle(title,x=.06,y=.96,ha="left",fontsize=20,fontweight="bold")
    fig.text(.06,.895,subtitle,fontsize=10,color=MUTED,ha="left",va="top",wrap=True)
    fig.subplots_adjust(left=.18,right=.96,top=.80,bottom=.20,wspace=.32,hspace=.5)
    return fig,axes
def note(fig,text):
    fig.text(.06,.12,textwrap.fill(text,150),fontsize=8,color=MUTED,va="top")
    fig.text(.06,.035,"Kevin Yamada | Canadian Household Finance | Official Canadian public sources",fontsize=8,color=MUTED)
def export():
    DEST.mkdir(parents=True,exist_ok=True)
    cases=pd.read_csv(OUT/"homebuying_cases.csv")
    observed=pd.read_csv(OUT/"homebuying_observed.csv")
    history=pd.read_csv(OUT/"homebuying_history.csv")
    waiting=pd.read_csv(OUT/"homebuying_waiting.csv")
    programs=pd.read_csv(OUT/"homebuying_programs.csv")
    decomp=pd.read_csv(OUT/"homebuying_decomposition.csv")
    base=cases[cases.year.eq(2023)&cases.scenario.eq("baseline")].copy()
    base["city"]=pd.Categorical(base.city,["Vancouver","Victoria","Halifax"],ordered=True)
    base["profile"]=pd.Categorical(base.profile,["single","couple","deposit"],ordered=True)
    base=base.sort_values(["city","profile"])
    figures=[]
    fig,axs=frame("A down payment does not settle the income question.",
        "Nine hypothetical buyers at 2023 first-time-buyer transaction benchmarks; rules reviewed November 16, 2026.",cols=2)
    labels=[f"{r.city} | {r.profile_label}" for r in base.itertuples()]
    y=np.arange(9)
    for ax,available,required,title in [(axs[0,0],"profile_cash","cash_target","Cash available vs minimum target"),
                                       (axs[0,1],"profile_income","required_gross_income","Annual gross income vs modeled requirement")]:
        ax.barh(y-.16,base[available]/1000,height=.28,color=GREEN,label="Profile amount")
        ax.barh(y+.16,base[required]/1000,height=.28,color=BLUE,label="Required amount")
        ax.set_yticks(y,labels if available=="profile_cash" else [""]*9)
        ax.invert_yaxis();ax.set_xlabel("CAD thousands");ax.set_title(title,loc="left",fontsize=11);clean(ax)
    handles, legends = axs[0,0].get_legend_handles_labels()
    fig.legend(handles, legends, loc="upper left", bbox_to_anchor=(.18,.855), ncol=2, fontsize=9, frameon=False)
    note(fig,"Four examples have enough cash but insufficient income under the screen. This is not a population estimate. Cash target includes minimum down, net transfer tax, CAD 4,000 closing allowance and CAD 10,000 reserve. Available cash above costs/reserve reduces the loan. Where cash is short, income is conditional on first having minimum cash. Sources: Statistics Canada 46-10-0099-01; Bank of Canada V122667780/786; CMHC and municipal/provincial rules.")
    figures.append(("01_cash_and_income","Cash and income",fig))
    fig,axs=frame("Prices and rates raised the income hurdle.",
        "Minimum-down comparison; observed buyer-family income provides context, not a verified borrower's qualifying income.",cols=3)
    for ax,city in zip(axs[0],["Vancouver","Victoria","Halifax"]):
        g=history[history.city.eq(city)].sort_values("year")
        for col,color,label in [("required_gross_income",BLUE,"Modeled income needed"),("buyer_family_median_income",GREEN,"Observed buyer-family median")]:
            ax.plot(g.year.iloc[1:],g[col].iloc[1:]/1000,color=color,marker="o",label=label)
            ax.plot(g.year.iloc[:2],g[col].iloc[:2]/1000,color=color,linestyle="--",marker="o")
        ax.set_title(city,loc="left");ax.set_xticks([2020,2021,2022,2023],["2020*","2021","2022","2023"])
        ax.set_ylim(0,250);ax.set_ylabel("Annual gross income (CAD thousands)");ax.grid(axis="y",color="#d7dfda",linewidth=.6)
    axs[0,0].legend(fontsize=7,loc="upper left")
    note(fig,"Sources: Statistics Canada 46-10-0062-01 (2020*) and 46-10-0099-01 (2021-2023); Bank of Canada annual arithmetic means of 12 monthly funds-advanced fixed 5-year-and-over rates. Dashed segment marks the 2016/2021 geography-vintage boundary. Current mortgage rules and the 2023 tax schedule are held fixed; this does not reconstruct historical approvals. Properties and buyer mix can change.")
    figures.append(("02_income_hurdle_history","Income hurdle over time",fig))
    fig,axs=frame("Which change clears the Vancouver example?",
        "Two earners: CAD 150,000 gross income, CAD 100,000 liquid cash, CAD 500 monthly existing debt.",cols=1)
    selected=["baseline","price10","price20","rate1","cash25","income20","amort30","hbp"]
    g=cases[cases.city.eq("Vancouver")&cases.profile.eq("couple")&cases.year.eq(2023)].set_index("scenario").loc[selected]
    ax=axs[0,0]
    ax.barh(np.arange(len(g)),g.income_gap/1000,color=[GREEN if v=="Within modeled limits" else BLUE for v in g.barrier])
    ax.set_yticks(np.arange(len(g)),g.scenario_label);ax.invert_yaxis();ax.set_xlim(0,47)
    for i,r in enumerate(g.itertuples()):
        ax.text(max(.5,r.income_gap/1000+.5),i,"Within modeled limits" if r.income_gap<.01 else cash(r.income_gap),va="center",fontsize=9)
    ax.set_xlabel("Annual gross-income shortfall (CAD thousands)");clean(ax)
    fig.subplots_adjust(left=.32)
    note(fig,"Each change is applied separately to the same 2023 price/rate baseline with current rules. A 20% lower purchase price clears both modeled checks in this example; the other displayed changes leave an income shortfall. The HBP case moves CAD 40,000 of existing, separately assumed RRSP assets into purchase cash and requires future repayment. No price/rate forecast or loan approval is made.")
    figures.append(("03_what_changes_the_result","What changes the result",fig))
    fig,axs=frame("Income growth offset only part of the pressure.",
        "2021 to 2023: contribution to the change in modeled income needed minus observed buyer-family median income.",cols=3)
    for ax,city in zip(axs[0],["Vancouver","Victoria","Halifax"]):
        g=decomp[decomp.city.eq(city)].set_index("factor").loc[["price","rates","income"]]
        ax.barh(["Price","Mortgage rates","Buyer-family income"],g.contribution_cad/1000,color=[RUST,RUST,GREEN])
        ax.axvline(0,color=INK,linewidth=.7);ax.set_title(city,loc="left");ax.set_xlim(-25,35)
        for i,v in enumerate(g.contribution_cad):
            ax.text(v/1000+(.5 if v>=0 else -.5),i,f"{v/1000:+.1f}",ha="left" if v>=0 else "right",va="center",fontsize=9)
        ax.invert_yaxis();ax.set_xlabel("CAD thousands");clean(ax)
    note(fig,"An exact three-input Shapley calculation averages all six replacement orders so the price, rate and income contributions reconcile to the total change. This is an accounting decomposition of selected inputs, not causal attribution. Rules and property-tax schedule are held fixed. Median buyer-family income is contextual; a median is not a matched borrower's income. See homebuying_decomposition.csv and methodology.")
    figures.append(("04_price_rate_income","Price, rates and income",fig))
    fig,axs=frame("Buyer measures help, with different trade-offs.",
        "Vancouver two-earner example; all comparisons are conditional on eligibility.",cols=2)
    g=programs[programs.city.eq("Vancouver")&programs.profile.eq("couple")]
    labels=["BC transfer relief","30-year amortization","HBP existing RRSP","FHSA after one year*"]
    y=np.arange(4)
    ax=axs[0,0]; ax.barh(y,g.required_income_before/1000,height=.5,color="#d7dfda",label="Before")
    ax.scatter(g.required_income_after/1000,y,color=BLUE,zorder=3,label="After")
    ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlabel("Required annual gross income (CAD thousands)");ax.set_xlim(0,210);ax.legend(fontsize=8);clean(ax)
    ax=axs[0,1]
    thirty=g[g.program.eq("30-year amortization")].iloc[0]
    ax.bar(["25 years","30 years"],[thirty.monthly_payment_before,thirty.monthly_payment_after],color=[BLUE,GREEN])
    ax.set_ylabel("Contractual monthly mortgage payment (CAD)")
    for i,v in enumerate([thirty.monthly_payment_before,thirty.monthly_payment_after]):ax.text(i,v+50,cash(v),ha="center",fontsize=10)
    ax.set_ylim(0,5800)
    ax.text(.02,.90,f"First five years' interest:\n{cash(thirty.five_year_interest_before)} vs {cash(thirty.five_year_interest_after)}",transform=ax.transAxes,fontsize=9)
    note(fig,"BC relief reduces transfer tax; 30 years lowers payments but increases insured premium and first-five-year interest. HBP uses existing RRSP wealth (CAD 40,000 here), with future repayments. *FHSA compares two cases after identical 12-month saving: CAD 16,000 contributed from that saving is counted once; only an assumed 30% refund adds CAD 4,800. No free funds or guaranteed refund is assumed. All four comparisons retain an income shortfall in this example.")
    figures.append(("05_buyer_measures","Buyer measures",fig))
    fig,axs=frame("Saving longer helps only if the target does not outrun it.",
        "Vancouver two-earner illustration: save CAD 2,000/month initially; annual rent growth 3%; income and mortgage rates fixed.")
    ax=axs[0,0];baseline=base[(base.city=="Vancouver")&(base.profile=="couple")].iloc[0]
    for growth,color,label in [(-.05,GREEN,"Price falls 5% per year"),(0,BLUE,"Price stays flat"),(.05,RUST,"Price rises 5% per year")]:
        g=waiting[waiting.city.eq("Vancouver")&waiting.profile.eq("couple")&waiting.annual_price_growth.eq(growth)&waiting.annual_rent_growth.eq(.03)].sort_values("months")
        ax.plot([0,*g.months],[baseline.required_gross_income/1000,*list(g.required_gross_income/1000)],color=color,marker="o",label=label)
    ax.axhline(150,color=INK,linestyle="--",label="Fixed profile income")
    ax.set_xticks([0,12,24],["Baseline","12 months","24 months"]);ax.set_ylim(130,215)
    ax.set_ylabel("Required annual gross income (CAD thousands)");ax.legend(fontsize=9,loc="upper left");ax.grid(axis="y",color="#d7dfda",linewidth=.6)
    note(fig,"Price changes are hypothetical paths, not forecasts or probabilities. Higher rent reduces the initially stated net saving; cash earns zero interest. Closing costs and loan-insurance tiers are recalculated at each price. Starting point is the 2023 transaction benchmark with rules reviewed November 16, 2026. This is a sensitivity study, not a recommendation to buy or wait.")
    figures.append(("06_waiting_to_buy","Waiting to buy",fig))
    limits=pd.read_csv(OUT/"homebuying_price_limits.csv")
    fig,axs=frame("What price fits the buyer's starting finances?",
        "Baseline income, cash, rates and reserve held fixed. Bars are financial-screen limits; dashed line is the observed 2023 benchmark.",cols=3)
    for ax,city in zip(axs[0],["Vancouver","Victoria","Halifax"]):
        g=limits[limits.city.eq(city)].set_index("profile").loc[["single","couple","deposit"]]
        ax.barh(["Single earner","Two earners","Larger deposit"],g.maximum_price/1000,color=BLUE,height=.45)
        price=g.benchmark_price.iloc[0]
        ax.axvline(price/1000,color=RUST,linestyle="--",linewidth=1.5)
        ax.set_title(city,loc="left");ax.set_xlim(0,1000);ax.set_xlabel("Purchase price (CAD thousands)")
        ax.invert_yaxis();clean(ax)
        for i,v in enumerate(g.maximum_price):
            ax.text(v/1000+8,i,f"{v/1000:,.0f}k",va="center",fontsize=9)
    fig.subplots_adjust(left=.13,wspace=.50)
    note(fig,"The search isolates transfer-tax, insurance-premium and insured/uninsured-rate boundaries rather than assuming one globally smooth relationship. Exact whole-dollar thresholds and additional cash needed at each benchmark are in homebuying_price_limits.csv. Buyer finances and costs are assumptions. This is not a market-price forecast, a safe spending recommendation or lender approval. Sources: Statistics Canada, Bank of Canada, CMHC and government tax schedules; see methodology.")
    figures.append(("07_price_limits","Price limits from starting finances",fig))
    latest=pd.read_csv(OUT/"homebuying_latest_rates.csv")
    fig,axs=frame("Newer rates help. The income hurdle can remain.",
        "Same 2023 purchase price, property-tax schedule and buyer finances; newer monthly national rates replace the 2023 annual benchmark.",cols=3)
    for ax,city in zip(axs[0],["Vancouver","Victoria","Halifax"]):
        g=latest[latest.city.eq(city)].set_index("profile").loc[["single","couple","deposit"]]
        y=np.arange(3)
        ax.barh(y-.16,g.baseline_required_income/1000,height=.28,color="#a7b7b0",label="2023 annual rates")
        ax.barh(y+.16,g.required_gross_income/1000,height=.28,color=BLUE,label=str(g.rate_period.iloc[0])+" monthly rates")
        ax.set_yticks(y,["Single earner","Two earners","Larger deposit"]);ax.invert_yaxis()
        ax.set_title(city,loc="left");ax.set_xlim(0,220);ax.set_xlabel("Income needed (CAD thousands)");clean(ax)
    axs[0,0].legend(fontsize=7,loc="lower right");fig.subplots_adjust(left=.13,wspace=.55)
    period=str(latest.rate_period.iloc[0])
    note(fig,"Latest rate period: "+period+". Bank of Canada funds-advanced fixed 5-year-and-over series V122667780/786. Monthly rates are not annual averages or borrower offers. The latest reviewed Statistics Canada buyer release still uses 2023 transactions and income. This isolates rates and does not measure current-market affordability. Profile income, cash, historical tax schedule and other costs stay fixed.")
    figures.append(("08_latest_rates","Newer rates on the same purchase",fig))
    errors=pd.read_csv(OUT/"homebuying_calculation_audit.csv")
    g=errors[errors.city.eq("Vancouver")&errors.profile.eq("couple")&errors.scenario.eq("price10")].sort_values("variant_order")
    fig,axs=frame("The wrong qualifying rate can create a false pass.",
        "Worked audit: Vancouver, two earners, price 10% lower (CAD 764,100), CAD 150,000 gross income, unchanged purchase cash.")
    ax=axs[0,0]
    labels=["Correct calculation","Contract rate used to qualify","Other debt omitted","Tax, heat and condo costs omitted","Financed premium omitted"]
    colors=[BLUE,*[RUST if bool(v) else "#a7b7b0" for v in g.false_pass.iloc[1:]]]
    ax.barh(np.arange(5),g.required_gross_income/1000,color=colors,height=.5)
    ax.axvline(150,color=INK,linestyle="--",label="Profile income: CAD 150,000")
    ax.set_yticks(np.arange(5),labels);ax.invert_yaxis();ax.set_xlim(0,195)
    for i,row in enumerate(g.itertuples()):
        ax.text(row.required_gross_income/1000+1,i,f"{row.required_gross_income/1000:,.1f}k"+(" / false pass" if row.false_pass else ""),va="center",fontsize=9,bbox={"facecolor":PAPER,"edgecolor":"none","pad":2})
    ax.set_xlabel("Annual gross income needed (CAD thousands)");clean(ax);fig.legend(*ax.get_legend_handles_labels(),loc="upper left",bbox_to_anchor=(.33,.855),fontsize=9,frameon=False)
    fig.subplots_adjust(left=.33)
    note(fig,"Each incorrect row introduces one deliberate calculation error; the cash position is held fixed. The correct qualifying rate uses the contract rate plus 2 percentage points or 5.25%, whichever is higher. A false pass means the flawed calculation fits both checks while the correct one does not. These are defined examples, not observed errors at TD or any other lender, and not a bank error-rate estimate. Sources: CMHC debt-service guidance and OSFI B-20.")
    figures.append(("09_calculation_audit","A calculation mistake that changes the result",fig))
    file_stages=pd.read_csv(OUT/"mortgage_file_stages.csv").sort_values("stage_order")
    fig,axs=frame("Correct the file before changing the request.",
        "FICTIONAL TRAINING FILE: application, supporting worksheets and prices are constructed examples; no genuine borrower evidence.")
    ax=axs[0,0];y=np.arange(3)
    ax.barh(y-.16,file_stages.profile_income/1000,height=.28,color=GREEN,label="Income stated / supported")
    ax.barh(y+.16,file_stages.required_gross_income/1000,height=.28,color=BLUE,label="Income required by the stage")
    ax.set_yticks(y,["Submitted claim*","Corrected review","Revised request"]);ax.invert_yaxis()
    ax.set_xlim(0,200);ax.set_xlabel("Annual gross income (CAD thousands)");clean(ax)
    for i,r in enumerate(file_stages.itertuples()):
        ax.text(max(r.profile_income,r.required_gross_income)/1000+2,i,r.financial_result,va="center",fontsize=9)
    fig.legend(*ax.get_legend_handles_labels(),loc="upper left",bbox_to_anchor=(.18,.855),ncol=2,fontsize=9,frameon=False)
    note(fig,"*The submitted screen deliberately uses the contract rate and unreconciled inputs. Seven discrepancies change recurring income to CAD 135,000, usable cash to CAD 85,000, debt to CAD 750/month and the qualifying rate to 6.15%. The revised request changes only the hypothetical price to CAD 600,000, with tax recalculated using the historical proxy. Both financial checks then fit, while six actual-evidence controls remain open. All stages remain on hold. The worksheet packet supplies no real credit decision, signature or approval.")
    figures.append(("10_mortgage_file_review","The complete fictional file review",fig))
    assets=[]
    pdf=DEST/"HomebuyingBarriers-Figures.pdf"
    with PdfPages(pdf) as book:
        for stem,title,fig in figures:
            for ext in ["png","svg"]:
                path=DEST/f"{stem}.{ext}"
                fig.savefig(path,dpi=180,metadata={"Creator":"Kevin Yamada | Local VS Code Python"})
                if ext == "svg":
                    path.write_text("\n".join(line.rstrip() for line in path.read_text(encoding="utf-8").splitlines())+"\n", encoding="utf-8", newline="\n")
                assets.append({"file":path.name,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"bytes":path.stat().st_size})
            book.savefig(fig);plt.close(fig)
    assets.append({"file":pdf.name,"sha256":hashlib.sha256(pdf.read_bytes()).hexdigest(),"bytes":pdf.stat().st_size})
    manifest={"price_year":2023,"rule_date":"2026-11-16","assets":assets,
              "execution":"Exported with matplotlib in Kevin's desktop VS Code"}
    (DEST/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8",newline="\n")
    gallery="# Homebuying barriers: figure gallery\n\nTen figures answer one question: is the down payment really the biggest obstacle?\n\n2023 transaction benchmarks; mortgage and tax rules reviewed November 16, 2026. Buyer profiles are hypothetical, not population estimates or loan approvals.\n\n"
    for stem,title,_ in figures:
        gallery+=f"## {title}\n\n![{title}]({stem}.png)\n\n[PNG]({stem}.png) · [Editable SVG]({stem}.svg)\n\n"
    gallery+="[Ten-page PDF](HomebuyingBarriers-Figures.pdf) · [Source tables](../../../data/processed) · [Methodology](../../../docs/homebuying_methodology.md)\n"
    (DEST/"README.md").write_text(gallery,encoding="utf-8",newline="\n")
    from export_mortgage_file import export as export_training_packet
    export_training_packet()
    archive=ROOT/"work/HomebuyingBarriers-Figures.zip"
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as z:
        for path in DEST.iterdir():
            if path.is_file():z.write(path,"figures/"+path.name)
        for path in [*OUT.glob("homebuying_*.csv"),*OUT.glob("mortgage_file_*.csv")]:z.write(path,"data/"+path.name)
        packet=ROOT/"reports/mortgage_file/MortgageFile-Audit-Pack.pdf"
        z.write(packet,"notes/"+packet.name)
        for path in [ROOT/"docs/homebuying_methodology.md",ROOT/"reports/homebuying_findings.md",ROOT/"docs/bank_audit_case.md",ROOT/"reports/calculation_review.md",ROOT/"reports/source_refresh.md",ROOT/"reports/mortgage_calculation_audit.md",ROOT/"docs/interview_brief.md",ROOT/"docs/mortgage_file_walkthrough.md"]:
            if path.exists():z.write(path,"notes/"+path.name)
    print(f"Published ten PNG/SVG pairs, ten-page PDF and ZIP: {archive}",flush=True)
    return manifest
if __name__=="__main__":export()
