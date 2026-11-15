"""Check that the published review experiment still uses the frozen source evidence."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_benchmark_evidence_matches_statcan_panel():
    cases = json.loads((ROOT / 'experiments/audit_cases.json').read_text(encoding='utf-8'))
    manifest = json.loads((ROOT / 'experiments/audit_run_manifest.json').read_text())
    digest = hashlib.sha256(json.dumps(cases, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert digest == manifest['cases_sha256']
    assert len({case['case_id'] for case in cases}) == len(cases)
    panel = pd.read_csv(ROOT / 'data/processed/segment_history.csv').set_index(['quarter', 'group'])
    values = [('income', 'income'), ('consumption', 'consumption'),
              ('pension_adjustment', 'pension'), ('net_saving', 'saving'),
              ('debt_to_income_percent', 'debt_income_pct')]
    for case in cases:
        evidence = case['evidence']
        row = panel.loc[(evidence['quarter'], evidence['group'])]
        for key, column in values:
            assert evidence[key] == row[column], (case['case_id'], key)
        year = int(evidence['quarter'][:4])
        assert case['split'] == ('development' if year <= 2023 else 'test')


def test_reported_reviewer_selection_and_counts_match_saved_scores():
    audit = json.loads((ROOT / 'data/processed/audit_experiment.json').read_text())
    scores = pd.read_csv(ROOT / 'data/processed/audit_model_scores.csv')
    ranked = scores[scores['split'] == 'development'].sort_values(
        ['balanced_accuracy', 'config_id'], ascending=[False, True])
    selected = int(ranked.iloc[0].config_id)
    assert selected == audit['selected_config']
    chosen = scores[(scores.config_id == selected) & (scores['split'] == 'test')].iloc[0]
    comparison = pd.read_csv(ROOT / 'data/processed/audit_method_comparison.csv').set_index('method')
    reported = comparison.loc['Selected AI reviewer']
    assert reported['cases'] == audit['unique_evaluation_cases'] * audit['common_complete_repetitions']
    for metric in ['unsupported_recall', 'false_alarm_rate', 'abstention_rate', 'true_positive', 'false_positive']:
        assert np.isclose(reported[metric], chosen[metric])
    assert reported['true_positive'] <= reported['unsupported_cases']
    assert reported['false_positive'] <= reported['supported_cases']
