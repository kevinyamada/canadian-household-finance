import json
from pathlib import Path
import shutil
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from insights import collect


@pytest.fixture
def snapshot(tmp_path):
    target = tmp_path / 'data/processed'
    target.mkdir(parents=True)
    for name in ['segment_latest.csv', 'summary.json', 'model_audit.json', 'holdout_scores.csv',
                 'gpu_comparison.csv', 'selected_predictions.csv', 'audit_experiment.json',
                 'audit_method_comparison.csv']:
        shutil.copy2(ROOT / 'data/processed' / name, target / name)
    return tmp_path


def test_insight_numbers_and_dates_match_their_source_snapshots():
    summary = collect()
    cards = {card['id']: card for card in summary['cards']}
    source = pd.read_csv(ROOT / 'data/processed/segment_latest.csv').set_index('group')
    renter = source.loc['Renter']
    national = json.loads((ROOT / 'data/processed/summary.json').read_text())
    assert cards['saving']['metrics']['income'] == renter.income
    assert cards['saving']['metrics']['consumption'] == renter.consumption
    assert cards['saving']['metrics']['net_saving'] == pytest.approx(
        cards['saving']['metrics']['income_less_consumption'] + cards['saving']['metrics']['pension_adjustment'])
    assert str(renter.quarter) in cards['saving']['period']
    assert national['latest_quarter'] in cards['national']['period']
    assert cards['national']['metrics']['payment_growth_pct'] == national['payment_growth_pct']
    assert cards['groups']['metrics']['mortgage_debt_income_pct'] == source.loc['Owner with mortgage'].debt_income_pct


def test_saving_interpretation_changes_when_the_income_gap_changes(snapshot):
    path = snapshot / 'data/processed/segment_latest.csv'
    frame = pd.read_csv(path)
    index = frame.index[frame.group == 'Renter'][0]
    frame.loc[index, ['income', 'income_less_consumption', 'saving']] += 1000
    frame.to_csv(path, index=False)
    card = next(c for c in collect(snapshot)['cards'] if c['id'] == 'saving')
    assert card['metrics']['income_less_consumption'] > 0
    assert 'hide an income gap' not in card['title']
    assert 'does not mean income covered' not in card['meaning']
    assert card['metrics']['net_saving'] == frame.loc[index, 'saving']


def test_trend_and_model_actions_change_with_contrary_evidence(snapshot):
    path = snapshot / 'data/processed/summary.json'
    national = json.loads(path.read_text())
    national.update(payment_growth_pct=-1, income_growth_pct=-2, qoq_change_pp=.1)
    path.write_text(json.dumps(national))
    model = json.loads((snapshot / 'data/processed/model_audit.json').read_text())['selected_model']
    path = snapshot / 'data/processed/holdout_scores.csv'
    scores = pd.read_csv(path)
    scores.loc[scores.model == model, 'mae'] = .1
    scores.to_csv(path, index=False)
    cards = {c['id']: c for c in collect(snapshot)['cards']}
    assert 'Payments rose while the ratio fell' != cards['national']['title']
    assert 'Income grew faster' not in cards['national']['meaning']
    assert 'Keep the previous-quarter' not in cards['forecast']['action']
    assert cards['forecast']['metrics']['selected_mae_pp'] == .1


def test_supporting_summary_and_housing_opening_page_match_the_evidence():
    assert json.loads((ROOT / 'data/processed/key_insights.json').read_text()) == collect()
    audit = json.loads((ROOT / 'data/processed/housing_audit_summary.json').read_text())
    pages = ROOT / 'powerbi/HouseholdFinance.Report/definition/pages'
    metadata = json.loads((pages / 'pages.json').read_text())
    assert metadata['pageOrder'] == ['conclusion', 'saving', 'purchase']
    assert metadata['activePageName'] == 'conclusion'
    content = '\n'.join(path.read_text(encoding='utf-8') for path in (pages / 'conclusion').rglob('visual.json'))
    assert audit['question'] in content
    assert audit['verdict'] in content
    assert 'Four findings' not in content
