import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments'))
from prepare_gpu import prepare


def test_gpu_inputs_only_use_observed_training_labels():
    panel = pd.read_csv(ROOT / 'data/processed/quarterly_panel.csv')
    result = prepare(panel)
    for index, row in enumerate(result['metadata']):
        assert row['last_train_target'] <= row['origin_quarter'] < row['quarter']
        mask = np.array(result['mask'][index]).flatten().astype(bool)
        x = np.array(result['x'][index])
        y = np.array(result['y'][index])
        assert mask.sum() == row['n_train']
        np.testing.assert_allclose(x[mask].mean(axis=0), 0, atol=1e-10)
        np.testing.assert_allclose(y[mask].mean(), 0, atol=1e-10)
        assert (x[~mask] == 0).all()
        assert (y[~mask] == 0).all()


def test_future_data_do_not_change_gpu_inputs_at_past_origin():
    panel = pd.read_csv(ROOT / 'data/processed/quarterly_panel.csv')
    first = prepare(panel)
    changed = panel.copy()
    columns = ['dsr', 'payments', 'income', 'interest', 'income_growth', 'payment_growth', 'mortgage_share']
    changed.loc[changed.quarter > '2018Q4', columns] *= 17
    second = prepare(changed)
    index = next(i for i, row in enumerate(first['metadata']) if row['origin_quarter'] == '2018Q4')
    for key in ['x', 'y', 'mask', 'query']:
        np.testing.assert_array_equal(first[key][index], second[key][index])
