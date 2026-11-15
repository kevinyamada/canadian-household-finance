import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def prepare():
    frame=pd.read_csv(ROOT/'data/processed/segment_history.csv')
    frame=frame[frame.view.isin(['Age','Income','Housing tenure'])].copy()
    rng=np.random.default_rng(469)
    cases=[]
    for row in frame.itertuples():
        evidence={'source':'Statistics Canada DHEA tables 36-10-0662-01, 36-10-0660-01 and 36-10-0664-01',
                  'flow_units':'CAD per household for the quarter','aggregation':'Group averages, not individual household records',
                  'ratio_definition':'Debt balance divided by annualized disposable income, expressed in percent',
                  'saving_definition':'Disposable income plus pension entitlement adjustment minus consumption',
                  'causal_scope':'Descriptive estimates do not establish causal effects',
                  'quarter':row.quarter,'group':row.group,'income':row.income,'consumption':row.consumption,
                  'pension_adjustment':row.pension,'net_saving':row.saving,'debt_to_income_percent':row.debt_income_pct}
        gap=row.income-row.consumption
        pairs={
            'number':(f'Debt to income: {row.debt_income_pct:.1f}%.',f'Debt to income: {row.debt_income_pct+17.3:.1f}%.'),
            'period':(f'These figures describe {row.quarter}.',f'These figures describe {pd.Period(row.quarter,freq="Q")+1}.'),
            'units':(f'Average disposable income was CAD {row.income:.0f} per household for the quarter.',f'Average disposable income was CAD {row.income:.0f} per household per month.'),
            'ratio_definition':('The debt to income figure compares a debt balance with annualized disposable income.','The debt to income figure is the percentage of this quarter\'s income paid to service debt.'),
            'pension':(f'Income less consumption was CAD {gap:.0f}; net saving of CAD {row.saving:.0f} also includes the pension entitlement adjustment.',f'Households had CAD {row.saving:.0f} left from disposable income after consumption, without any pension adjustment.'),
            'individual':('These are group averages, so they do not establish the outcome for every household.',f'Every household in this group has a debt to income ratio of exactly {row.debt_income_pct:.1f}%.'),
            'causality':('This descriptive comparison does not establish that group membership caused the observed financial position.','These figures prove that belonging to this group causes its financial position.')}
        for kind,(supported,unsupported) in pairs.items():
            for label,claim in [(True,supported),(False,unsupported)]:
                text=f'Review excerpt about {row.group} in {row.quarter}: {claim}'
                key=f'{row.quarter}|{row.group}|{kind}|{label}'
                cases.append({'case_id':hashlib.sha256(key.encode()).hexdigest()[:16],
                              'split':'test' if row.quarter>='2024Q1' else 'development',
                              'kind':kind,'supported':label,'evidence':evidence,'claim':text,
                              'python_evidence':f'Income minus consumption = {gap:.0f}. Income plus pension adjustment minus consumption = {row.income+row.pension-row.consumption:.0f}. Debt to income is a stock to annualized income ratio, not debt service. Group means do not identify every household or causal effects.'})
    order=rng.permutation(len(cases))
    cases=[cases[int(i)] for i in order]
    path=ROOT/'experiments/audit_cases.json'
    path.write_text(json.dumps(cases,indent=2),encoding='utf-8')
    print({'cases':len(cases),'test':sum(x['split']=='test' for x in cases),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    return cases

if __name__=='__main__':prepare()
