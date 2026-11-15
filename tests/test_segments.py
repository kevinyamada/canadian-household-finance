import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from segments import checks


def baseline():
    return pd.read_csv(ROOT/'data/processed/segment_latest.csv').query("view == 'Housing tenure'").copy()


def test_clean_current_tenure_rows_pass_controls():
    assert checks(baseline()).passed.all()


def test_controls_detect_seeded_errors():
    original=baseline()
    for column,change,control in [('income',np.nan,'Complete applicable measures'),('income',0,'Positive income denominator'),('saving',100000,'Saving reconciliation'),('assets',0,'Net worth reconciliation'),('debt_income_pct',1,'Published debt ratio reconciliation')]:
        changed=original.copy()
        changed.loc[changed.index[0],column]=change
        result=checks(changed).set_index('control')
        assert not result.loc[control,'passed']
    duplicated=pd.concat([original,original.iloc[[0]]],ignore_index=True)
    assert not checks(duplicated).set_index('control').loc['Unique quarter and group','passed']


def test_segment_comparisons_use_same_quarter_prior_year():
    history=pd.read_csv(ROOT/'data/processed/segment_history.csv')
    latest=pd.read_csv(ROOT/'data/processed/segment_latest.csv')
    prior=str(pd.Period(latest.quarter.iloc[0],freq='Q')-4)
    previous=history[history.quarter==prior].set_index('group')
    np.testing.assert_allclose(latest.debt_income_yoy_pp,latest.debt_income_pct-previous.loc[latest.group,'debt_income_pct'].to_numpy())


def test_pension_adjustment_is_not_income_less_consumption():
    row=baseline().set_index('group').loc['Renter']
    assert row.income_less_consumption == row.income-row.consumption
    assert row.saving == row.income_less_consumption+row.pension
    assert row.income_less_consumption<0<row.saving


def test_source_snapshots_match_manifest():
    import hashlib
    import json
    raw=ROOT/'data/raw/segments'
    manifest=json.loads((raw/'manifest.json').read_text())
    assert len(manifest)==3
    for item in manifest:
        assert hashlib.sha256((raw/(item['table']+'-eng.zip')).read_bytes()).hexdigest()==item['sha256']
    panel=pd.read_csv(ROOT/'data/processed/segment_history.csv')
    assert panel.groupby('quarter')['group'].nunique().eq(39).all()
    assert panel.groupby('group')['quarter'].nunique().eq(24).all()


def test_sql_group_changes_match_python_and_keep_views_separate():
    import sqlite3
    latest=pd.read_csv(ROOT/'data/processed/segment_latest.csv').set_index('group')
    with sqlite3.connect(ROOT/'data/processed/finance.sqlite') as connection:
        sql=pd.read_sql_query('SELECT * FROM segment_yearly_changes WHERE quarter = ?',connection,params=[latest.quarter.iloc[0]]).set_index('group')
        notes=pd.read_sql_query('SELECT * FROM latest_segment_review',connection).set_index('group')
    np.testing.assert_allclose(sql.loc[latest.index,'debt_income_yoy_pp'],latest.debt_income_yoy_pp)
    np.testing.assert_allclose(sql.loc[latest.index,'gap_yoy_dollars'],latest.gap_yoy_dollars)
    assert len(notes)==13
    assert notes.loc['Renter','reporting_note'].startswith('Pension adjustment changes')
