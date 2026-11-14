import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from data import OUT

FEATURES = ['dsr', 'change_1', 'change_2', 'change_4', 'income_growth',
            'payment_growth', 'mortgage_share', 'interest_share']
VALIDATION_START = '2007Q1'
HOLDOUT_START = '2019Q1'


def features(panel):
    frame = panel.copy()
    frame['change_1'] = frame['dsr'].diff()
    frame['change_2'] = frame['dsr'].diff(2)
    frame['change_4'] = frame['dsr'].diff(4)
    frame['interest_share'] = 100 * frame['interest'] / frame['payments']
    frame['target'] = frame['dsr'].shift(-1)
    frame['target_change'] = frame['target'] - frame['dsr']
    frame['target_quarter'] = (pd.PeriodIndex(frame['quarter'], freq='Q') + 1).astype(str)
    return frame


def estimator(name):
    if name.startswith('Ridge'):
        return make_pipeline(StandardScaler(), Ridge(alpha=float(name.split()[1])))
    if name == 'Random forest':
        return RandomForestRegressor(n_estimators=160, max_depth=3, min_samples_leaf=8,
                                     random_state=469, n_jobs=2)
    raise ValueError(name)


def prediction(name, train, row):
    if name == 'Persistence':
        return float(row['dsr'].iloc[0])
    if name == 'Recent drift':
        return float(row['dsr'].iloc[0] + row['change_4'].iloc[0] / 4)
    model = estimator(name)
    model.fit(train[FEATURES], train['target_change'])
    return float(row['dsr'].iloc[0] + model.predict(row[FEATURES])[0])


def walk_forward(frame, names, start, end=None):
    records = []
    observed = frame.dropna(subset=FEATURES + ['target'])
    for index, row in observed.iterrows():
        quarter = row['target_quarter']
        if quarter < start or (end is not None and quarter >= end):
            continue
        train = observed.loc[observed['target_quarter'] <= row['quarter']]
        if len(train) < 40:
            raise ValueError('Training window is too short')
        if train.target_quarter.max() >= quarter:
            raise ValueError('Future label entered the training sample')
        for name in names:
            estimate = prediction(name, train, observed.loc[[index]])
            records.append({'origin_quarter': row['quarter'], 'quarter': quarter,
                            'model': name, 'actual': row['target'], 'prediction': estimate,
                            'error': row['target'] - estimate, 'absolute_error': abs(row['target'] - estimate),
                            'n_train': len(train), 'last_train_target': train.target_quarter.max()})
    return pd.DataFrame(records)


def scores(predictions):
    rows = []
    for name, group in predictions.groupby('model'):
        rows.append({'model': name, 'n': len(group), 'mae': group.absolute_error.mean(),
                     'rmse': np.sqrt(np.mean(group.error ** 2)), 'bias': -group.error.mean()})
    return pd.DataFrame(rows).sort_values(['mae','model'])


def block_bootstrap_difference(holdout, selected):
    paired = holdout.pivot(index='quarter', columns='model', values='absolute_error')
    differences = (paired[selected] - paired['Persistence']).to_numpy()
    rng = np.random.default_rng(469)
    n = len(differences)
    starts = rng.integers(0, n, size=(4000, int(np.ceil(n / 4))))
    indices = ((starts[:, :, None] + np.arange(4)) % n).reshape(4000, -1)[:, :n]
    sampled = differences[indices].mean(axis=1)
    return {'mean_difference_pp': float(differences.mean()),
            'lower_95': float(np.quantile(sampled, .025)), 'upper_95': float(np.quantile(sampled, .975)),
            'block_quarters': 4, 'replicates': 4000,
            'interpretation': 'Negative means selected model has lower MAE; short dependent series limits precision.'}


def run_models(panel):
    frame = features(panel)
    names = ['Persistence','Recent drift','Ridge 1','Ridge 10','Ridge 100','Random forest']
    validation = walk_forward(frame, names, VALIDATION_START, HOLDOUT_START)
    ranking = scores(validation)
    selected = ranking.iloc[0]['model']
    finalists = list(dict.fromkeys(['Persistence','Recent drift',selected]))
    holdout = walk_forward(frame, finalists, HOLDOUT_START)
    selected_validation = validation[validation.model == selected]
    ordered_errors = np.sort(selected_validation.absolute_error.to_numpy())
    order = min(int(np.ceil((len(ordered_errors) + 1) * .9)), len(ordered_errors)) - 1
    radius = float(ordered_errors[order])
    chosen = holdout[holdout.model == selected].copy()
    chosen['lower'] = chosen.prediction - radius
    chosen['upper'] = chosen.prediction + radius
    chosen['covered'] = (chosen.actual >= chosen.lower) & (chosen.actual <= chosen.upper)
    sensitivity = []
    for label, mask in [('All holdout quarters', pd.Series(True, index=holdout.index)),
                        ('Excluding 2020Q2 and 2020Q3', ~holdout.quarter.isin(['2020Q2','2020Q3']))]:
        result = scores(holdout.loc[mask]); result['period'] = label; sensitivity.append(result)
    observed = frame.dropna(subset=FEATURES + ['target'])
    latest = frame.tail(1)
    next_value = prediction(selected, observed, latest)
    forecast = {'origin_quarter': latest.quarter.iloc[0], 'quarter': latest.target_quarter.iloc[0],
                'model': selected, 'prediction': next_value, 'lower': next_value-radius, 'upper': next_value+radius,
                'label': 'Next unpublished quarter estimate using revised data; not a live forecast validation'}
    validation.to_csv(OUT/'validation_predictions.csv', index=False)
    ranking.to_csv(OUT/'validation_scores.csv', index=False)
    holdout.to_csv(OUT/'holdout_predictions.csv', index=False)
    scores(holdout).to_csv(OUT/'holdout_scores.csv', index=False)
    chosen.to_csv(OUT/'selected_predictions.csv', index=False)
    pd.concat(sensitivity).to_csv(OUT/'sensitivity_scores.csv', index=False)
    pd.DataFrame([forecast]).to_csv(OUT/'next_estimate.csv', index=False)
    audit = {'selection_period': [validation.quarter.min(), validation.quarter.max()],
             'holdout_period': [holdout.quarter.min(), holdout.quarter.max()],
             'selected_model': selected, 'features': FEATURES,
             'selected_holdout_coverage': float(chosen.covered.mean()), 'interval_radius_pp': radius,
             'nominal_interval': .9, 'bootstrap_mae_difference': block_bootstrap_difference(holdout,selected),
             'limitations': ['Historical series are revised; this is a revised vintage retrospective experiment.',
                            'Quarter t data are published during quarter t+1; this is a next unpublished quarter nowcast.',
                            'Intervals use validation errors of the selected model and have no guaranteed coverage.',
                            'All figures describe national aggregates, not TD customers or default probabilities.']}
    (OUT/'model_audit.json').write_text(json.dumps(audit, indent=2))
    return audit
