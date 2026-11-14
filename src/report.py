import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from data import ROOT, OUT

FIG = ROOT/'reports/figures'
COLORS = ['#176B61','#D38136','#6579A4','#4B5563']


def decompose(p0, p1, i0, i1):
    payments = 50 * (p1-p0) * (1/i0+1/i1)
    income = 50 * (p0+p1) * (1/i1-1/i0)
    return payments, income


def save(fig, name):
    fig.savefig(FIG/name, dpi=170, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def run_report(panel, audit):
    FIG.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,
                         'axes.spines.right':False,'axes.titleweight':'bold','axes.titlepad':16,
                         'axes.labelcolor':'#35444A','text.color':'#152C32','axes.prop_cycle':plt.cycler(color=COLORS)})
    recent = panel[panel.quarter >= '2010Q1'].copy()
    dates = pd.to_datetime(recent.date)
    latest, prior = panel.iloc[-1],panel.iloc[-2]
    payments, income = decompose(prior.payments,latest.payments,prior.income,latest.income)
    contribution = pd.DataFrame({'driver':['Payment growth','Income growth'], 'contribution_pp':[payments,income]})
    contribution.to_csv(OUT/'latest_decomposition.csv',index=False)
    scenario_rows=[]
    for income_shock in [-5, -2, 0, 2, 5]:
        for payment_shock in [0, 5, 10, 15]:
            dsr = 100*latest.payments*(1+payment_shock/100)/(latest.income*(1+income_shock/100))
            scenario_rows.append({'income_change_pct':income_shock,'payment_change_pct':payment_shock,
                                  'scenario_dsr':dsr,'change_pp':dsr-100*latest.payments/latest.income})
    scenarios=pd.DataFrame(scenario_rows);scenarios.to_csv(OUT/'scenarios.csv',index=False)
    fig,axes=plt.subplots(2,1,figsize=(11,7.5),sharex=True,gridspec_kw={'height_ratios':[1.4,1]})
    axes[0].plot(dates,recent.dsr,lw=2.6,label='Total')
    axes[0].plot(dates,recent.mortgage_dsr,lw=2,label='Mortgage')
    axes[0].plot(dates,recent.other_dsr,lw=2,label='Other debt')
    axes[0].set_title('The headline ratio has eased, but mortgages remain a large burden',loc='left')
    axes[0].set_ylabel('Debt payments / income (%)');axes[0].legend(ncol=3,frameon=False)
    axes[0].annotate(f'{latest.dsr:.2f}%',(dates.iloc[-1],latest.dsr),xytext=(-44,12),textcoords='offset points',fontweight='bold')
    axes[1].plot(dates,recent.policy_rate,color=COLORS[3],lw=2)
    axes[1].set_ylabel('Policy rate (%)');axes[1].set_title('Policy rate shown for context, without a causal interpretation',loc='left',fontsize=12)
    for ax in axes: ax.grid(axis='y',alpha=.18)
    fig.text(.125,.01,'Sources: Statistics Canada 11-10-0065-01; Bank of Canada V39079. National aggregates.',fontsize=9)
    fig.tight_layout(rect=(0,.03,1,1));save(fig,'01_household_pressure.png')
    fig,axes=plt.subplots(1,2,figsize=(11,4.5))
    axes[0].bar(contribution.driver,contribution.contribution_pp,color=[COLORS[1],COLORS[0]])
    axes[0].axhline(0,color='#4B5563',lw=.8);axes[0].set_ylabel('Contribution (percentage points)')
    axes[0].set_title(f'Why the ratio changed in {latest.quarter}',loc='left')
    for i,v in enumerate(contribution.contribution_pp): axes[0].text(i,v/2,f'{v:+.3f}',ha='center',color='white',fontweight='bold')
    axes[1].stackplot(dates,recent.interest_dsr,recent.principal_dsr,labels=['Interest','Principal'],colors=COLORS[:2],alpha=.9)
    axes[1].set_ylabel('Share of income (%)');axes[1].set_ylim(bottom=0)
    axes[1].legend(frameon=False,loc='upper left');axes[1].set_title('Interest and principal payments',loc='left')
    fig.tight_layout();save(fig,'02_drivers.png')
    selected=pd.read_csv(OUT/'selected_predictions.csv'); selected_dates=pd.PeriodIndex(selected.quarter,freq='Q').to_timestamp()
    baseline=pd.read_csv(OUT/'holdout_predictions.csv'); baseline=baseline[baseline.model=='Persistence']
    fig,ax=plt.subplots(figsize=(11,5.2))
    ax.fill_between(selected_dates,selected.lower,selected.upper,color=COLORS[0],alpha=.12,label='90% calibration band')
    ax.plot(selected_dates,selected.actual,color='#152C32',lw=2.2,label='Observed')
    ax.plot(selected_dates,selected.prediction,color=COLORS[0],lw=2,label=audit['selected_model'])
    if audit['selected_model']!='Persistence': ax.plot(selected_dates,baseline.prediction,color=COLORS[1],lw=1.5,ls=':',label='Persistence')
    ax.set_title('A difficult test: predicting through the pandemic and rate changes',loc='left')
    ax.set_ylabel('Debt service ratio (%)');ax.legend(frameon=False,ncol=2);ax.grid(axis='y',alpha=.18)
    fig.text(.12,.005,'Revised vintage backtest. The shaded band is calibrated on earlier errors, not guaranteed coverage.',fontsize=9)
    fig.tight_layout(rect=(0,.035,1,1));save(fig,'03_model_backtest.png')
    sensitivity=pd.read_csv(OUT/'sensitivity_scores.csv');fig,ax=plt.subplots(figsize=(9,4.6))
    pivot=sensitivity.pivot(index='model',columns='period',values='mae')
    pivot.plot.barh(ax=ax,color=COLORS[:2]);ax.set_xlabel('Mean absolute error (percentage points)');ax.set_ylabel('')
    ax.set_title('How much do the two largest pandemic quarters affect error?',loc='left');ax.legend(frameon=False,fontsize=9)
    fig.tight_layout();save(fig,'04_model_errors.png')
    grid=scenarios.pivot(index='income_change_pct',columns='payment_change_pct',values='scenario_dsr')
    fig,ax=plt.subplots(figsize=(8,5));im=ax.imshow(grid.values,cmap='YlOrBr',aspect='auto')
    ax.set_xticks(range(len(grid.columns)),[f'+{x}%' for x in grid.columns]);ax.set_yticks(range(len(grid.index)),[f'{x:+}%' for x in grid.index])
    for r in range(len(grid)):
        for c in range(len(grid.columns)): ax.text(c,r,f'{grid.iloc[r,c]:.2f}%',ha='center',va='center',color='white' if grid.iloc[r,c]>16 else '#132C31')
    ax.set_xlabel('Assumed change in total required payments');ax.set_ylabel('Assumed change in income')
    ax.set_title('What if payment growth outpaces income?',loc='left');fig.colorbar(im,ax=ax,label='Debt service ratio (%)')
    fig.text(.12,.005,'Accounting scenarios at the latest quarter. These are assumptions, not interest rate or default predictions.',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,1));save(fig,'05_scenarios.png')
    holdout=pd.read_csv(OUT/'holdout_scores.csv');validation=pd.read_csv(OUT/'validation_scores.csv')
    chosen=holdout.set_index('model').loc[audit['selected_model']];base=holdout.set_index('model').loc['Persistence']
    gain=100*(base.mae-chosen.mae)/base.mae
    forecast=pd.read_csv(OUT/'next_estimate.csv').iloc[0]
    old=panel[panel.quarter=='2019Q4'].iloc[0]
    summary={'latest_quarter':latest.quarter,'latest_dsr':latest.dsr,'qoq_change_pp':latest.dsr-prior.dsr,
             'payment_growth_pct':latest.payment_growth,'income_growth_pct':latest.income_growth,
             'payment_contribution_pp':payments,'income_contribution_pp':income,
             'mortgage_change_since_2019q4_pp':latest.mortgage_dsr-old.mortgage_dsr,
             'other_change_since_2019q4_pp':latest.other_dsr-old.other_dsr,
             'holdout_mae_pp':chosen.mae,'baseline_mae_pp':base.mae,'mae_improvement_pct':gain}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    table='\n'.join(f'| {r.model} | {r.n} | {r.mae:.3f} | {r.rmse:.3f} |' for r in holdout.itertuples())
    conclusion = 'The selected model improved on persistence in the final period.' if gain>0 else 'The selected model did not beat persistence in the final period. Keep persistence as the practical benchmark.'
    report=f'''# Canadian household borrowing pressure

The national debt service ratio fell to **{latest.dsr:.2f}% in {latest.quarter}**, a change of {latest.dsr-prior.dsr:+.2f} percentage points from the previous quarter. Required payments still rose {latest.payment_growth:.2f}%. The ratio fell because income grew faster, at {latest.income_growth:.2f}%.

For a bank analytics team, this supports monitoring payment growth alongside income growth. A falling aggregate ratio does not mean every household is better off or that mortgage renewal pressure has disappeared.

![Household pressure](figures/01_household_pressure.png)

## What changed

The exact accounting decomposition assigns {payments:+.3f} percentage points to payment growth and {income:+.3f} to income growth. Their sum equals the change in the unrounded ratio. This decomposition describes arithmetic, not a causal estimate.

Since 2019Q4, the mortgage component changed by {latest.mortgage_dsr-old.mortgage_dsr:+.2f} percentage points, while other debt changed by {latest.other_dsr-old.other_dsr:+.2f}. The components share the same income denominator and can be added.

![Drivers](figures/02_drivers.png)

## Can a model improve the next quarter estimate?

We used 2007Q1 through 2018Q4 to choose among persistence, recent drift, three ridge settings, and a small random forest. The selected model was **{audit['selected_model']}**. Every prediction is fitted using only preceding labels. The final evaluation covers {audit['holdout_period'][0]} through {audit['holdout_period'][1]} with {int(chosen.n)} predictions.

| Model | Quarters | MAE, percentage points | RMSE, percentage points |
| :--- | ---: | ---: | ---: |
{table}

{conclusion} Its relative MAE improvement was {gain:.1f}%. The paired block bootstrap interval for its MAE minus persistence is [{audit['bootstrap_mae_difference']['lower_95']:.3f}, {audit['bootstrap_mae_difference']['upper_95']:.3f}] percentage points. If the interval includes zero, the sample does not establish a clear advantage. There are only {int(chosen.n)} test quarters, so the evidence is limited.

![Forecast evaluation](figures/03_model_backtest.png)

The calibration band covered {audit['selected_holdout_coverage']:.1%} of final period observations, compared with a nominal 90% target. It is based on earlier errors from the selected model. It is not a guarantee and may miss sudden economic changes.

![Error sensitivity](figures/04_model_errors.png)

The next unpublished quarter, {forecast.quarter}, has a model estimate of {forecast.prediction:.2f}% with a calibration band of {forecast.lower:.2f}% to {forecast.upper:.2f}%. By the snapshot date this quarter has already ended. Treat this as a nowcast using the last published household release, not a claim of advance forecasting.

## Scenario analysis

![Scenario analysis](figures/05_scenarios.png)

Scenarios change required payments and income directly. They do not translate policy rate changes into mortgage payments. That would require balances, renewal dates, loan terms, and borrower data not present in these sources.

## Recommendation

Use this dashboard as an aggregate monitoring tool. Track the debt service ratio together with its payment and income components. Before using it for lending or outreach, validate the patterns with approved portfolio data at the borrower level. Do not use these aggregate results as customer default probabilities.

## Scope and limits

The dataset contains {len(panel)} quarterly national observations from {panel.quarter.iloc[0]} to {latest.quarter}. Dollar amounts are millions of Canadian dollars, seasonally adjusted at annual rates. They must not be described as actual quarterly cash totals. The ratio denominator adds interest back to disposable income.

Historical values can be revised. The experiment uses the current downloaded vintage, not the releases that were actually available at each historical date. Publication delays also mean quarter t household data become available during t+1. A real deployment needs release timestamps and archived vintages. Policy rates are context only and are not used in the primary model. No claim is made about TD's customers, losses, or proprietary models.

## Sources

[Statistics Canada table 11-10-0065-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1110006501), released September 11, 2026. [Debt service methodology](https://www150.statcan.gc.ca/n1/pub/13-605-x/2015006/article/14219-eng.htm). [Bank of Canada Valet](https://www.bankofcanada.ca/valet/docs), series V39079. Download snapshot: November 14, 2026. Source hashes are in data/raw/manifest.json.
'''
    (ROOT/'reports/analysis.md').write_text(report,encoding='utf-8')
    return summary
