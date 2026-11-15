import hashlib
import json
import sqlite3
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/segments'
OUT=ROOT/'data/processed'
AGES=['Less than 35 years','35 to 44 years','45 to 54 years','55 to 64 years','65 years and over']
INCOMES=['Lowest income quintile','Second income quintile','Third income quintile','Fourth income quintile','Highest income quintile']
TENURES=['Owner with mortgage','Owner without mortgage','Renter']
GROUPS=AGES+INCOMES+TENURES+['All households']+[income+', '+age[0].lower()+age[1:] for income in INCOMES for age in AGES]


def load(table):
    RAW.mkdir(parents=True,exist_ok=True)
    path=RAW/(table+'-eng.zip')
    if not path.exists():
        response=requests.get('https://www150.statcan.gc.ca/n1/en/tbl/csv/'+table+'-eng.zip',timeout=120)
        response.raise_for_status()
        path.write_bytes(response.content)
    return pd.read_csv(zipfile.ZipFile(path).open(table+'.csv'),low_memory=False)


def checks(frame):
    required=['quarter','group','income','consumption','pension','saving','assets','debt','net_worth','debt_income_pct']
    numeric=required[2:]
    common=[c for c in numeric if c not in ['pension','saving']]
    valid=frame[common].notna().all(axis=1)
    applicable=~frame['group'].str.contains('quintile,')
    complete=valid & (~applicable | frame[['pension','saving']].notna().all(axis=1))
    positive=frame.income>0
    out=[]
    def add(name,mask,tolerance):
        out.append({'control':name,'exceptions':int(mask.sum()),'passed':not mask.any(),'tolerance':tolerance})
    add('Unique quarter and group',frame.duplicated(['quarter','group'],keep=False),'No duplicate keys')
    add('Complete applicable measures',~complete,'No missing values')
    add('Positive income denominator',~positive,'Income greater than zero')
    add('Saving reconciliation',valid&applicable&((frame.income+frame.pension-frame.consumption-frame.saving).abs()>2),'CAD 2 rounding allowance per household')
    add('Net worth reconciliation',valid&((frame.assets-frame.debt-frame.net_worth).abs()>2),'CAD 2 rounding allowance per household')
    calculated=100*frame.debt/(4*frame.income)
    rounding=.051+100*.5/(4*frame.income)+100*frame.debt*.5/(4*frame.income**2)
    add('Published debt ratio reconciliation',valid&positive&((calculated-frame.debt_income_pct).abs()>rounding),'0.051 percentage points plus input rounding bounds')
    return pd.DataFrame(out)


def run():
    source={t:load(t) for t in ['36100662','36100660','36100664']}
    maps={
        '36100662':('Income, consumption and savings',{'Household disposable income':'income','Household final consumption expenditure (HFCE)':'consumption','Change in pension entitlements':'pension','Household net saving':'saving'}),
        '36100660':('Wealth',{'Total assets':'assets','Total liabilities':'debt','Net worth (wealth)':'net_worth'}),
        '36100664':('Net worth indicators (wealth)',{'Debt to disposable income ratio':'debt_income_pct'})}
    result=None
    for table,(dimension,names) in maps.items():
        df=source[table]
        df=df[(df.GEO=='Canada')&(df.REF_DATE>='2020-01')&df[dimension].isin(names)&df.Characteristics.isin(GROUPS)].copy()
        if 'Statistics' in df:
            df=df[df.Statistics=='Value per household']
            assert (df.UOM=='Dollars').all() and (df.SCALAR_FACTOR=='units').all()
        else:
            assert (df.UOM=='Percent').all()
        assert not df.duplicated(['REF_DATE','Characteristics',dimension]).any()
        wide=df.pivot(index=['REF_DATE','Characteristics'],columns=dimension,values='VALUE').rename(columns=names).reset_index()
        if result is not None:
            keys=['REF_DATE','Characteristics']
            assert set(map(tuple,result[keys].to_numpy()))==set(map(tuple,wide[keys].to_numpy())), 'Source table keys do not match'
        result=wide if result is None else result.merge(wide,on=['REF_DATE','Characteristics'],validate='one_to_one',how='inner')
    result=result.rename(columns={'Characteristics':'group'})
    result['quarter']=pd.PeriodIndex(result.REF_DATE,freq='Q').astype(str)
    result['income_less_consumption']=result.income-result.consumption
    result['gap_pct_income']=100*result.income_less_consumption/result.income
    result['view']=np.select([result.group.isin(AGES),result.group.isin(INCOMES),result.group.isin(TENURES),result.group.str.contains('quintile,')],['Age','Income','Housing tenure','Income and age'],default='Other')
    result=result[result.view.ne('Other')|result.group.eq('All households')].copy()
    audit=checks(result)
    exceptions=result[(result.assets-result.debt-result.net_worth).abs()>2].copy()
    exceptions['reconciliation_difference']=exceptions.assets-exceptions.debt-exceptions.net_worth
    exceptions['review_note']='Small source reconciliation difference; retain for review, not evidence of fraud.'
    exceptions.to_csv(OUT/'segment_reconciliation_exceptions.csv',index=False)
    blocking=audit[audit.control.ne('Net worth reconciliation')]
    if not blocking.passed.all() or (exceptions.reconciliation_difference.abs()>10).any():
        raise ValueError(audit.to_string(index=False))
    latest=result.quarter.max()
    current=result[result.quarter==latest].copy()
    old=result[result.quarter==str(pd.Period(latest,freq='Q')-4)][['group','debt_income_pct','income_less_consumption']].rename(columns={'debt_income_pct':'debt_income_prior_year','income_less_consumption':'gap_prior_year'})
    current=current.merge(old,on='group',validate='one_to_one')
    current['debt_income_yoy_pp']=current.debt_income_pct-current.debt_income_prior_year
    current['gap_yoy_dollars']=current.income_less_consumption-current.gap_prior_year
    current['pension_changes_sign']=(current.income_less_consumption<0)&(current.saving>=0)
    with sqlite3.connect(OUT/'finance.sqlite') as connection:
        result.to_sql('segment_history',connection,if_exists='replace',index=False)
        audit.to_sql('segment_controls',connection,if_exists='replace',index=False)
        connection.executescript((ROOT/'sql/segments.sql').read_text())
    result.to_csv(OUT/'segment_history.csv',index=False)
    current.to_csv(OUT/'segment_latest.csv',index=False)
    audit.to_csv(OUT/'segment_controls.csv',index=False)
    flags=current[current.pension_changes_sign][['quarter','group','income','consumption','income_less_consumption','pension','saving']]
    flags.to_csv(OUT/'segment_interpretation_flags.csv',index=False)
    manifest=[{'table':t,'url':'https://www150.statcan.gc.ca/n1/en/tbl/csv/'+t+'-eng.zip','sha256':hashlib.sha256((RAW/(t+'-eng.zip')).read_bytes()).hexdigest(),'latest_quarter':latest} for t in source]
    (RAW/'manifest.json').write_text(json.dumps(manifest,indent=2))
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(1,2,figsize=(12,5))
    tenure=current.set_index('group').loc[TENURES]
    labels=['Owners with mortgage','Owners without mortgage','Renters']
    axs[0].barh(labels,tenure.debt_income_pct,color='#176B61')
    axs[0].invert_yaxis();axs[0].set_xlabel('Published debt to annualized disposable income (%)')
    axs[0].set_title('Where is leverage concentrated?',loc='left')
    for i,v in enumerate(tenure.debt_income_pct):axs[0].text(v+3,i,f'{v:.1f}%',va='center')
    axs[0].set_xlim(0,tenure.debt_income_pct.max()*1.2)
    positions=np.arange(3)
    axs[1].barh(positions-.18,tenure.income_less_consumption,height=.35,label='Income less consumption',color='#D38136')
    axs[1].barh(positions+.18,tenure.saving,height=.35,label='Net saving including pension adjustment',color='#6579A4')
    axs[1].set_yticks(positions,labels);axs[1].invert_yaxis();axs[1].axvline(0,color='#444444',lw=.7)
    axs[1].set_xlabel('CAD per household in the quarter');axs[1].set_title('Does income cover consumption?',loc='left')
    axs[1].legend(loc='lower right',fontsize=8,frameon=False)
    fig.suptitle(f'Household pressure has more than one form | {latest}',x=.02,ha='left',fontsize=15)
    fig.text(.02,.02,'Group averages, not individual outcomes. Consumption includes imputations; this is not a cash flow or default model.',fontsize=9)
    fig.tight_layout(rect=[0,.05,1,.94]);fig.savefig(ROOT/'reports/figures/11_segment_pressure.png',dpi=170);plt.close(fig)
    print(current[current.group.isin(TENURES+AGES)][['group','debt_income_pct','income_less_consumption','pension','saving','debt_income_yoy_pp']].to_string(index=False))
    print(audit.to_string(index=False))
    return result,current,audit

if __name__=='__main__':run()
