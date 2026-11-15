import gzip
import hashlib
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed'


def verdict(text):
    try:
        match=re.search(r'\{.*\}',text,flags=re.S)
        value=json.loads(match.group(0))['supported'] if match else None
        return value if type(value) is bool else None
    except (ValueError,KeyError):
        return None


def rule(case):
    number=re.search(r'Debt to income: ([\d.]+)%',case['claim'])
    if number:return abs(float(number.group(1))-case['evidence']['debt_to_income_percent'])<=.051
    period=re.search(r'These figures describe (\d{4}Q[1-4])',case['claim'])
    if period:return period.group(1)==case['evidence']['quarter']
    return None


def metrics(frame):
    truth=frame.supported.to_numpy(bool)
    parsed=frame.prediction.to_numpy(object)
    flags=np.array([x is False for x in parsed])
    passes=np.array([x is True for x in parsed])
    valid=flags|passes
    tp=int((flags&~truth).sum());fp=int((flags&truth).sum())
    return {'cases':len(frame),'unsupported_recall':tp/int((~truth).sum()),
            'false_alarm_rate':fp/int(truth.sum()),'abstention_rate':float((~valid).mean()),
            'balanced_accuracy':.5*(tp/int((~truth).sum())+int((passes&truth).sum())/int(truth.sum())),
            'coverage':float(valid.mean()),'accuracy_when_answered':float(((passes&truth)|(flags&~truth)).sum()/valid.sum()) if valid.any() else None,
            'true_positive':tp,'false_positive':fp,'unsupported_cases':int((~truth).sum()),'supported_cases':int(truth.sum())}


def clustered_metrics(frame):
    result=metrics(frame)
    clusters=pd.DataFrame([metrics(g) for _,g in frame.groupby('cluster')])
    rng=np.random.default_rng(469)
    indices=rng.integers(0,len(clusters),size=(5000,len(clusters)))
    for field in ['unsupported_recall','false_alarm_rate']:
        sampled=clusters[field].to_numpy()[indices].mean(axis=1)
        lower,upper=np.quantile(sampled,[.025,.975])
        result[field+'_lower95']=float(lower)
        result[field+'_upper95']=float(upper)
    return result


def summarize():
    cases=json.loads((ROOT/'experiments/audit_cases.json').read_text(encoding='utf-8'))
    by_id={c['case_id']:c for c in cases}
    runs=[json.loads(gzip.decompress((ROOT/f'experiments/audit_results/config_{i}.json.gz').read_bytes())) for i in range(8)]
    digest=hashlib.sha256(json.dumps(cases,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert all(r['cases_sha256']==digest for r in runs),'Case evidence changed after inference'
    repeats=min(r['complete_repetitions'] for r in runs)
    assert repeats>=1,'All configurations must finish the whole benchmark at least once'
    rows=[]
    for i,run in enumerate(runs):
        for record in run['records']:
            if record['repeat']>=repeats:continue
            case=by_id[record['case_id']]
            rows.append({'config_id':i,'model':run['config']['model'],'prompt':run['config']['prompt'],
                         'case_id':case['case_id'],'repeat':record['repeat'],'split':case['split'],
                         'kind':case['kind'],'supported':case['supported'],'prediction':verdict(record['response']),
                         'response':record['response'],'cluster':case['evidence']['quarter']+'|'+case['evidence']['group']})
    records=pd.DataFrame(rows)
    records['prediction']=pd.Series([r['prediction'] for r in rows],dtype=object)
    assert not records.duplicated(['config_id','case_id','repeat']).any()
    for _,group in records.groupby(['config_id','repeat']):assert set(group.case_id)==set(by_id)
    summaries=[]
    for (config,split),group in records.groupby(['config_id','split']):
        summaries.append({'config_id':config,'model':group.model.iloc[0],'prompt':group.prompt.iloc[0],'split':split,**metrics(group)})
    summary=pd.DataFrame(summaries)
    development=summary[summary.split=='development'].sort_values(['balanced_accuracy','config_id'],ascending=[False,True])
    selected=int(development.iloc[0].config_id)
    chosen=records[(records.config_id==selected)&(records.split=='test')].copy()
    baseline=chosen.copy()
    baseline['prediction']=pd.Series([rule(by_id[c]) for c in chosen.case_id],index=baseline.index,dtype=object)
    hybrid=chosen.copy()
    hybrid['prediction']=pd.Series([rule(by_id[c]) if rule(by_id[c]) is not None else p for c,p in zip(chosen.case_id,chosen.prediction)],index=hybrid.index,dtype=object)
    comparison=pd.DataFrame([{'method':'Exact checks only',**clustered_metrics(baseline)},
                             {'method':'Selected AI reviewer',**clustered_metrics(chosen)},
                             {'method':'Exact checks plus AI',**clustered_metrics(hybrid)}])
    by_type=pd.DataFrame([{'kind':kind,**metrics(group)} for kind,group in chosen.groupby('kind')])
    summary.to_csv(OUT/'audit_model_scores.csv',index=False)
    comparison.to_csv(OUT/'audit_method_comparison.csv',index=False)
    by_type.to_csv(OUT/'audit_error_types.csv',index=False)
    records.to_csv(OUT/'audit_verdicts.csv.gz',index=False,compression='gzip')
    incorrect=chosen[chosen.apply(lambda r:type(r.prediction) is not bool or r.prediction!=r.supported,axis=1)].drop_duplicates('case_id').head(30)
    examples=[{**by_id[r.case_id],'model_response':r.response,'model_prediction':r.prediction} for r in incorrect.itertuples()]
    (ROOT/'reports/audit_review_examples.json').write_text(json.dumps(examples,indent=2),encoding='utf-8')
    seed_scores=[]
    for (config,repeat),group in records[records.split=='test'].groupby(['config_id','repeat']):
        seed_scores.append({'config_id':config,'repeat':repeat,**metrics(group)})
    pd.DataFrame(seed_scores).to_csv(OUT/'audit_repeat_scores.csv',index=False)
    audit={'cases_sha256':digest,'selected_config':selected,'model':runs[selected]['config'],'common_complete_repetitions':repeats,
           'unique_evaluation_cases':sum(c['split']=='test' for c in cases),
           'main_estimated_gpu_cost_usd':sum(r['estimated_gpu_cost_usd'] for r in runs),
           'discarded_tail_responses':[len(r['records'])-repeats*len(cases) for r in runs],
           'worker_elapsed_seconds':[r['elapsed_seconds'] for r in runs],
           'model_revisions':[r['model_revision'] for r in runs],
           'limitation':'Controlled templates and balanced simulated errors, not real audit prevalence or fraud labels.'}
    (OUT/'audit_experiment.json').write_text(json.dumps(audit,indent=2))
    fig,axs=plt.subplots(1,2,figsize=(11,4.8))
    axs[0].barh(comparison.method,comparison.unsupported_recall*100,color=['#6579A4','#D38136','#176B61'])
    axs[0].set_xlim(0,105);axs[0].set_xlabel('Unsupported claims flagged (%)');axs[0].invert_yaxis()
    axs[1].barh(comparison.method,comparison.false_alarm_rate*100,color=['#6579A4','#D38136','#176B61'])
    axs[1].set_xlabel('Supported claims incorrectly flagged (%)');axs[1].invert_yaxis()
    maximum=max(1,float(comparison.false_alarm_rate.max()*100)*1.3)
    axs[1].set_xlim(0,maximum)
    for i,row in enumerate(comparison.itertuples()):
        axs[0].text(row.unsupported_recall*100+.6,i,f'{row.unsupported_recall:.1%}',va='center',fontsize=9)
        axs[1].text(row.false_alarm_rate*100+maximum*.02,i,f'{row.false_alarm_rate:.2%}',va='center',fontsize=9)
    fig.suptitle('Reporting review: detection and false alarms',x=.02,ha='left',fontsize=15)
    fig.text(.02,.02,'Controlled StatCan excerpts. Exact checks abstain outside their supported formats. Repeated answers are not new cases.',fontsize=8)
    fig.tight_layout(rect=[0,.06,1,.94]);fig.savefig(ROOT/'reports/figures/12_audit_benchmark.png',dpi=170);plt.close(fig)
    lines='\n'.join(f'| {r.method} | {r.unsupported_recall:.2%} | {r.false_alarm_rate:.2%} | {r.abstention_rate:.2%} |' for r in comparison.itertuples())
    report=f'''# Can AI help review financial reporting?

The selected configuration was {audit['model']}, chosen using development results only. Evaluation uses {audit['unique_evaluation_cases']:,} unique supported and deliberately corrupted excerpts from 2024 and 2025 StatCan group data, with {repeats} matched generation repetitions.

| Method | Unsupported claim recall | False alarm rate | Abstention rate |
| :--- | ---: | ---: | ---: |
{lines}

![Detection and false alarms](figures/12_audit_benchmark.png)

Exact checks cover explicit ratio numbers and period statements; they send other wording for review. Their accuracy on answered cases and coverage are reported separately in audit_method_comparison.csv. A hybrid uses exact checks where applicable and the selected AI reviewer elsewhere. Invalid AI responses are abstentions, not approvals. Descriptive 95% intervals in the comparison CSV resample source quarter and group clusters, keeping related templates and repetitions together. These intervals describe the constructed benchmark, not unseen real audit work.

Use deterministic checks for facts they can validate directly. Treat AI flags as review suggestions that need a person to resolve them. The benchmark does not establish that AI can replace an auditor. Review examples of wrong or invalid model answers in audit_review_examples.json.

The source data are real Statistics Canada estimates. The incorrect excerpts are deliberately generated and labeled. Seven error families cover numbers, periods, units, ratio meaning, pension adjustments, individual claims and causality. Error prevalence is balanced by design, so precision would differ in real reports. Templates repeat across years; this is not a test of arbitrary new writing, and repeated generations do not increase the number of independent cases. The exact baseline is deliberately narrow. Rules could be written for all seven known templates, so beating this baseline does not prove that an LLM is necessary or better than a comprehensive rules system. A useful next validation would use independently reviewed real report excerpts and an expanded rules baseline.

The main workers imply US${audit['main_estimated_gpu_cost_usd']:.2f} in GPU usage from runtime at the published H100 rate. CPU model preparation, storage, setup, smoke tests and other charges are additional. This is an estimate, not an invoice. Saved outputs can be summarized without another paid run.

[Protocol](../docs/audit_protocol.md) · [Code](../experiments/modal_audit.py) · [Evaluation by error type](../data/processed/audit_error_types.csv)
'''
    (ROOT/'reports/audit_benchmark.md').write_text(report,encoding='utf-8')
    print(comparison.to_string(index=False));print(json.dumps(audit,indent=2))
    return audit

if __name__=='__main__':summarize()
