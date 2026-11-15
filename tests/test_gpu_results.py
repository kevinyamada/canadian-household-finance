import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed'


def test_gpu_selection_and_comparison_are_reproducible():
    audit = json.loads((OUT / 'gpu_audit.json').read_text())
    ranking = pd.read_csv(OUT / 'gpu_validation_scores.csv')
    predictions = pd.read_csv(OUT / 'gpu_predictions.csv')
    scores = pd.read_csv(OUT / 'gpu_comparison.csv').set_index('model')
    selected = int(ranking.sort_values(['validation_mae', 'config_id']).iloc[0].config_id)
    assert selected == audit['selected_config']
    validation = predictions[predictions.period == 'Validation']
    test = predictions[predictions.period == 'Retrospective test']
    assert validation.quarter.max() < test.quarter.min()
    assert (predictions.last_train_target <= predictions.origin_quarter).all()
    assert (predictions.origin_quarter < predictions.quarter).all()
    assert len(test) == 30
    np.testing.assert_allclose(np.abs(test.actual - test.prediction).mean(), scores.loc['GPU neural ensemble', 'mae'])
    np.testing.assert_allclose(np.abs(test.actual - test.baseline).mean(), scores.loc['Persistence', 'mae'])
    np.testing.assert_allclose(np.abs(validation.actual - validation.prediction).mean(), ranking.set_index('config_id').loc[selected, 'validation_mae'])


def test_gpu_prediction_mean_matches_saved_seed_outputs():
    audit = json.loads((OUT / 'gpu_audit.json').read_text())
    metadata = json.loads((ROOT / 'experiments/input_metadata.json').read_text())
    meta = pd.DataFrame(metadata['metadata'])
    panel = pd.read_csv(OUT / 'quarterly_panel.csv')
    assert hashlib.sha256(panel.to_json(orient='records', double_precision=10).encode()).hexdigest() == metadata['source_sha256']
    batches = audit['common_seeds_per_config'] // 8
    raw = np.load(ROOT / f"experiments/results/config_{audit['selected_config']}.npz")['predictions'][:batches].astype(float)
    values = raw.transpose(1, 0, 2).reshape(len(meta), -1)
    expected = meta.origin_dsr + meta.target_mean + values.mean(axis=1) * meta.target_scale
    result = pd.read_csv(OUT / 'gpu_predictions.csv')
    assert result.quarter.tolist() == meta.quarter.tolist()
    np.testing.assert_allclose(result.prediction, expected, atol=1e-10, rtol=0)


def test_gpu_cost_and_device_records_match_completed_workers():
    audit = json.loads((OUT / 'gpu_audit.json').read_text())
    records = [json.loads((ROOT / f'experiments/results/config_{i}.json').read_text()) for i in range(8)]
    assert all('H100' in r['gpu'] for r in records)
    assert all(1150 <= r['elapsed_seconds'] < 1180 for r in records)
    np.testing.assert_allclose(sum(r['elapsed_seconds'] for r in records) * .001097, audit['main_estimated_gpu_cost_usd'])
    assert audit['main_estimated_gpu_cost_usd'] >= 10
