import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from models import FEATURES, features


def prepare(panel):
    frame = features(panel)
    observed = frame.dropna(subset=FEATURES + ['target']).copy()
    origins = frame[frame.target_quarter >= '2007Q1'].copy()
    longest = len(observed)
    x, y, masks, query, metadata = [], [], [], [], []
    for _, row in origins.iterrows():
        train = observed[observed.target_quarter <= row.quarter]
        assert len(train) >= 40
        assert train.target_quarter.max() < row.target_quarter
        values = train[FEATURES].to_numpy(float)
        center = values.mean(axis=0)
        scale = np.maximum(values.std(axis=0), 1e-6)
        target = train.target_change.to_numpy(float)
        target_mean = float(target.mean())
        target_scale = float(max(target.std(), 1e-6))
        padded_x = np.zeros((longest, len(FEATURES)))
        padded_y = np.zeros((longest, 1))
        mask = np.zeros((longest, 1))
        padded_x[:len(train)] = (values - center) / scale
        padded_y[:len(train), 0] = (target - target_mean) / target_scale
        mask[:len(train)] = 1
        x.append(padded_x.tolist())
        y.append(padded_y.tolist())
        masks.append(mask.tolist())
        query.append((((row[FEATURES].to_numpy(float) - center) / scale)[None]).tolist())
        metadata.append({'quarter': row.target_quarter, 'origin_quarter': row.quarter,
                         'actual': None if pd.isna(row.target) else float(row.target),
                         'origin_dsr': float(row.dsr), 'target_mean': target_mean,
                         'target_scale': target_scale, 'n_train': len(train),
                         'last_train_target': train.target_quarter.max()})
    return {'x': x, 'y': y, 'mask': masks, 'query': query, 'metadata': metadata,
            'features': FEATURES}


if __name__ == '__main__':
    path = ROOT / 'data/processed/quarterly_panel.csv'
    panel = pd.read_csv(path)
    payload = prepare(panel)
    canonical = panel.to_json(orient='records', double_precision=10).encode()
    payload['source_sha256'] = hashlib.sha256(canonical).hexdigest()
    meta = {key: payload[key] for key in ['metadata', 'features', 'source_sha256']}
    (ROOT / 'experiments/input_metadata.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    (ROOT / 'experiments/input.json').write_text(json.dumps(payload), encoding='utf-8')
    print({'origins': len(payload['metadata']), 'features': FEATURES})
