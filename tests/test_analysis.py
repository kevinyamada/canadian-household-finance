import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from data import OUT
from models import FEATURES, features, prediction
from report import decompose

@pytest.fixture
def panel():
    return pd.read_csv(OUT/'quarterly_panel.csv')


def test_accounting_and_rounding(panel):
    np.testing.assert_allclose(100*panel.payments/panel.income,panel.dsr,atol=.0051,rtol=0)
    np.testing.assert_allclose(panel.payments,panel.interest+panel.principal,atol=1,rtol=0)
    np.testing.assert_allclose(panel.payments,panel.mortgage_payments+panel.other_payments,atol=1,rtol=0)


def test_one_row_per_complete_quarter(panel):
    periods=pd.PeriodIndex(panel.quarter,freq='Q')
    assert periods.is_unique
    assert periods.equals(pd.period_range(periods.min(),periods.max(),freq='Q'))
    assert panel[['dsr','income','payments']].notna().all().all()


def test_rate_join_does_not_duplicate_or_use_future_dates(panel):
    available=panel.dropna(subset=['policy_last_date'])
    assert pd.PeriodIndex(available.policy_last_date,freq='Q').equals(pd.PeriodIndex(available.quarter,freq='Q'))
    assert panel.quarter.is_unique


def test_decomposition_closes_for_increase_and_decrease():
    for p0,p1,i0,i1 in [(100,112,1000,1020),(100,95,1000,900),(100,100,1000,1000)]:
        a,b=decompose(p0,p1,i0,i1)
        assert a+b==pytest.approx(100*p1/i1-100*p0/i0)


def test_forecast_never_trains_on_future_labels():
    for name in ['validation_predictions.csv','holdout_predictions.csv']:
        result=pd.read_csv(OUT/name)
        assert (result.last_train_target<=result.origin_quarter).all()
        assert (result.origin_quarter<result.quarter).all()
        assert result.groupby('model').quarter.nunique().eq(result.groupby('model').size()).all()
    validation=pd.read_csv(OUT/'validation_predictions.csv')
    holdout=pd.read_csv(OUT/'holdout_predictions.csv')
    assert validation.quarter.max()<holdout.quarter.min()


def test_future_perturbation_cannot_change_past_prediction(panel):
    first=features(panel)
    index=panel.index[panel.quarter=='2018Q4'][0]
    changed=panel.copy()
    changed.loc[changed.index>index,['dsr','income','payments']]*=20
    second=features(changed)
    pd.testing.assert_series_equal(first.loc[index,FEATURES],second.loc[index,FEATURES])
    a=first.dropna(subset=FEATURES+['target'])
    b=second.dropna(subset=FEATURES+['target'])
    a=a[a.target_quarter<=first.loc[index,'quarter']]
    b=b[b.target_quarter<=second.loc[index,'quarter']]
    pd.testing.assert_frame_equal(a[FEATURES+['target_change']],b[FEATURES+['target_change']])
    assert prediction('Ridge 10',a,first.loc[[index]])==pytest.approx(prediction('Ridge 10',b,second.loc[[index]]))


def test_selection_uses_validation_not_final_scores():
    validation=pd.read_csv(OUT/'validation_scores.csv')
    audit=json.loads((OUT/'model_audit.json').read_text())
    assert audit['selected_model']==validation.sort_values(['mae','model']).iloc[0].model


def test_scenario_zero_shock_and_monotonicity(panel):
    scenarios=pd.read_csv(OUT/'scenarios.csv')
    base=scenarios[(scenarios.income_change_pct==0)&(scenarios.payment_change_pct==0)].iloc[0]
    assert base.scenario_dsr==pytest.approx(100*panel.payments.iloc[-1]/panel.income.iloc[-1])
    assert base.change_pp==pytest.approx(0)
    for _,group in scenarios.groupby('income_change_pct'):
        assert (group.sort_values('payment_change_pct').scenario_dsr.diff().dropna()>0).all()
    for _,group in scenarios.groupby('payment_change_pct'):
        assert (group.sort_values('income_change_pct').scenario_dsr.diff().dropna()<0).all()


def test_persistence_is_previous_observation(panel):
    result=pd.read_csv(OUT/'holdout_predictions.csv')
    result=result[result.model=='Persistence'].merge(panel[['quarter','dsr']],left_on='origin_quarter',right_on='quarter',validate='one_to_one')
    np.testing.assert_allclose(result.prediction,result.dsr)
