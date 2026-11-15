import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'experiments'))
from summarize_audit import verdict, rule, metrics


def test_invalid_verdict_is_not_an_approval():
    assert verdict('{"supported": true, "reason": "Matches"}') is True
    assert verdict('{"supported": false}') is False
    for value in ['yes','{}','{"supported": "false"}','{"supported": 1}','{"supported": null}']:
        assert verdict(value) is None


def test_rules_only_answer_supported_formats():
    evidence={'debt_to_income_percent':306.1,'quarter':'2025Q4'}
    assert rule({'claim':'Debt to income: 306.1%.','evidence':evidence}) is True
    assert rule({'claim':'Debt to income: 323.4%.','evidence':evidence}) is False
    assert rule({'claim':'These figures describe 2025Q4.','evidence':evidence}) is True
    assert rule({'claim':'These figures describe 2026Q1.','evidence':evidence}) is False
    assert rule({'claim':'Every household has this ratio.','evidence':evidence}) is None


def test_abstentions_reduce_recall_and_remain_separate():
    frame=pd.DataFrame({'supported':[False,False,True,True],
                        'prediction':pd.Series([False,None,False,True],dtype=object)})
    score=metrics(frame)
    assert score['unsupported_recall']==.5
    assert score['false_alarm_rate']==.5
    assert score['abstention_rate']==.25
    assert score['balanced_accuracy']==.5
    assert score['accuracy_when_answered']==pytest.approx(2/3)


def test_selection_uses_development_and_requires_matching_evidence(tmp_path,monkeypatch):
    import gzip
    import hashlib
    import json
    import summarize_audit as module
    cases=[]
    for split,quarter in [('development','2023Q1'),('test','2025Q1')]:
        for supported in [True,False]:
            cases.append({'case_id':split+str(supported),'split':split,'kind':'number','supported':supported,
                          'evidence':{'quarter':quarter,'group':'Example','debt_to_income_percent':100},
                          'claim':'Debt to income: '+('100' if supported else '120')+'%.'})
    for folder in ['experiments/audit_results','data/processed','reports/figures']:
        (tmp_path/folder).mkdir(parents=True)
    (tmp_path/'experiments/audit_cases.json').write_text(json.dumps(cases))
    digest=hashlib.sha256(json.dumps(cases,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    for config in range(8):
        records=[]
        for case in cases:
            prediction=case['supported']
            if (config==0 and case['split']=='development') or (config>=2 and case['split']=='test'):
                prediction=not prediction
            records.append({'case_id':case['case_id'],'repeat':0,'response':json.dumps({'supported':prediction})})
        run={'config':{'model':'Example','prompt':str(config)},'cases_sha256':digest,'complete_repetitions':1,
             'records':records,'elapsed_seconds':2280,'estimated_gpu_cost_usd':2.5,'model_revision':'fixture'}
        with gzip.open(tmp_path/f'experiments/audit_results/config_{config}.json.gz','wt') as handle:
            json.dump(run,handle)
    monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setattr(module,'OUT',tmp_path/'data/processed')
    audit=module.summarize()
    assert audit['selected_config']==1
    comparison=pd.read_csv(tmp_path/'data/processed/audit_method_comparison.csv')
    assert comparison.unsupported_recall.eq(1).all()
    assert comparison.false_alarm_rate.eq(0).all()
    cases[0]['evidence']['debt_to_income_percent']=999
    (tmp_path/'experiments/audit_cases.json').write_text(json.dumps(cases))
    with pytest.raises(AssertionError,match='evidence changed'):
        module.summarize()
