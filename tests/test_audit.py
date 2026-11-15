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
