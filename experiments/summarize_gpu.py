import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed'


def paired_interval(difference, block):
    rng = np.random.default_rng(469)
    n = len(difference)
    starts = rng.integers(0, n, size=(5000, int(np.ceil(n / block))))
    indices = ((starts[:, :, None] + np.arange(block)) % n).reshape(5000, -1)[:, :n]
    means = difference[indices].mean(axis=1)
    return [float(x) for x in np.quantile(means, [.025, .975])]


def summarize():
    metadata = json.loads((ROOT / 'experiments/input_metadata.json').read_text())
    panel = pd.read_csv(OUT / 'quarterly_panel.csv')
    canonical = panel.to_json(orient='records', double_precision=10).encode()
    assert hashlib.sha256(canonical).hexdigest() == metadata['source_sha256'], 'Source vintage changed; rerun the experiment deliberately'
    meta = pd.DataFrame(metadata['metadata'])
    results = [json.loads((ROOT / f'experiments/results/config_{i}.json').read_text()) for i in range(8)]
    assert all(r['source_sha256'] == metadata['source_sha256'] for r in results)
    batches = min(r['complete_batches'] for r in results)
    seeds = batches * 8
    validation = (meta.quarter < '2019Q1').to_numpy()
    test = ((meta.quarter >= '2019Q1') & meta.actual.notna()).to_numpy()
    actual = meta.actual.to_numpy(float)
    predictions, rankings, seed_rows = {}, [], []
    for i, result in enumerate(results):
        raw = np.load(ROOT / f'experiments/results/config_{i}.npz')['predictions'][:batches].astype(float)
        values = raw.transpose(1, 0, 2).reshape(len(meta), seeds)
        values = meta.origin_dsr.to_numpy()[:, None] + meta.target_mean.to_numpy()[:, None] + values * meta.target_scale.to_numpy()[:, None]
        assert np.isfinite(values).all()
        predictions[i] = values
        estimate = values.mean(axis=1)
        c = result['config']
        rankings.append({'config_id': i, **c, 'seeds': seeds,
                         'validation_mae': np.abs(actual[validation] - estimate[validation]).mean()})
        for seed in range(seeds):
            seed_rows.append({'config_id': i, 'seed_index': seed,
                              'validation_mae': np.abs(actual[validation] - values[validation, seed]).mean(),
                              'test_mae': np.abs(actual[test] - values[test, seed]).mean()})
    ranking = pd.DataFrame(rankings).sort_values(['validation_mae', 'config_id'])
    selected = int(ranking.iloc[0].config_id)
    estimates = predictions[selected].mean(axis=1)
    chosen = meta.copy()
    chosen['prediction'] = estimates
    chosen['baseline'] = chosen.origin_dsr
    errors = np.sort(np.abs(actual[validation] - estimates[validation]))
    rank = min(int(np.ceil((len(errors) + 1) * .9)), len(errors)) - 1
    radius = float(errors[rank])
    chosen['lower'] = estimates - radius
    chosen['upper'] = estimates + radius
    chosen['seed_p10'] = np.quantile(predictions[selected], .1, axis=1)
    chosen['seed_p90'] = np.quantile(predictions[selected], .9, axis=1)
    chosen['period'] = np.where(validation, 'Validation', np.where(test, 'Retrospective test', 'Next unpublished quarter'))
    chosen.to_csv(OUT / 'gpu_predictions.csv', index=False)
    ranking.to_csv(OUT / 'gpu_validation_scores.csv', index=False)
    pd.DataFrame(seed_rows).to_csv(OUT / 'gpu_seed_scores.csv', index=False)
    original = pd.read_csv(OUT / 'holdout_predictions.csv')
    forest = original[original.model == 'Random forest'].set_index('quarter').loc[meta.loc[test, 'quarter'], 'prediction'].to_numpy()
    candidates = {'Persistence': meta.loc[test, 'origin_dsr'].to_numpy(),
                  'Original random forest': forest, 'GPU neural ensemble': estimates[test]}
    records = []
    for name, pred in candidates.items():
        error = actual[test] - pred
        true_increase = actual[test] - meta.loc[test, 'origin_dsr'].to_numpy() >= .1
        flag = pred - meta.loc[test, 'origin_dsr'].to_numpy() >= .1
        records.append({'model': name, 'n': int(test.sum()), 'mae': np.abs(error).mean(),
                        'rmse': np.sqrt(np.mean(error ** 2)), 'flagged_quarters': int(flag.sum()),
                        'true_worsening_quarters': int(true_increase.sum()),
                        'true_positive': int((flag & true_increase).sum()),
                        'precision': float((flag & true_increase).sum() / flag.sum()) if flag.any() else None,
                        'recall': float((flag & true_increase).sum() / true_increase.sum())})
    scores = pd.DataFrame(records)
    scores.to_csv(OUT / 'gpu_comparison.csv', index=False)
    chosen.loc[test].to_csv(OUT / 'gpu_backtest.csv', index=False)
    difference = np.abs(actual[test] - estimates[test]) - np.abs(actual[test] - candidates['Persistence'])
    coverage = float(((actual[test] >= chosen.loc[test, 'lower']) & (actual[test] <= chosen.loc[test, 'upper'])).mean())
    smoke_path = ROOT / 'experiments/results/smoke.json'
    smoke = json.loads(smoke_path.read_text()) if smoke_path.exists() else None
    cost = sum(r['estimated_gpu_cost_usd'] for r in results)
    total = cost + (smoke['estimated_gpu_cost_usd'] if smoke else 0)
    seed_table = pd.DataFrame(seed_rows)
    seed_mae = seed_table[seed_table.config_id == selected].test_mae
    gpu_score = scores[scores.model == 'GPU neural ensemble'].iloc[0]
    persistence = scores[scores.model == 'Persistence'].iloc[0]
    improvement = 100 * (persistence.mae - gpu_score.mae) / persistence.mae
    audit = {'selected_config': selected, 'configuration': results[selected]['config'],
             'selection_metric': '2007Q1 to 2018Q4 ensemble MAE only', 'common_seeds_per_config': seeds,
             'completed_fits': sum(r['complete_batches'] * 8 * len(meta) for r in results),
             'matched_fits_used': len(results) * seeds * len(meta),
             'test_quarters': int(test.sum()), 'test_mae': float(gpu_score.mae),
             'persistence_mae': float(persistence.mae), 'relative_mae_improvement_pct': float(improvement),
             'coverage_90_band': coverage, 'calibration_radius_pp': radius,
             'mae_difference_pp': float(difference.mean()),
             'block4_interval': paired_interval(difference, 4), 'block8_interval': paired_interval(difference, 8),
             'individual_seed_test_mae_p10_p90': [float(x) for x in seed_mae.quantile([.1, .9])],
             'source_sha256': metadata['source_sha256'],
             'gpu_devices': [r['gpu'] for r in results],
             'worker_elapsed_seconds': [r['elapsed_seconds'] for r in results],
             'main_estimated_gpu_cost_usd': cost, 'including_smoke_estimated_gpu_cost_usd': total,
             'cost_basis': 'Runtime times published H100 rate 0.001097 USD per second; excludes startup, image build, CPU, RAM and billing adjustments. This is an estimate, not an invoice.',
             'experiment_status': 'Exploratory extension designed after the original test was observed; not a new untouched holdout.'}
    (OUT / 'gpu_audit.json').write_text(json.dumps(audit, indent=2))
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={'width_ratios': [1, 1.3]})
    axes[0].barh(scores.model, scores.mae, color=['#D38136', '#6579A4', '#176B61'])
    axes[0].set_xlabel('MAE, percentage points')
    axes[0].set_title('Does complexity improve the estimate?', loc='left')
    axes[0].invert_yaxis()
    for i, value in enumerate(scores.mae):
        axes[0].text(value + .003, i, f'{value:.3f}', va='center')
    axes[0].set_xlim(0, scores.mae.max() * 1.2)
    dates = pd.PeriodIndex(meta.loc[test, 'quarter'], freq='Q').to_timestamp()
    axes[1].plot(dates, actual[test], color='#176B61', label='Observed')
    axes[1].plot(dates, estimates[test], color='#D38136', label='Neural ensemble')
    axes[1].fill_between(dates, chosen.loc[test, 'lower'], chosen.loc[test, 'upper'], color='#D38136', alpha=.15, label='90% empirical band')
    axes[1].set_ylabel('Debt service ratio (%)')
    axes[1].set_title('Retrospective comparison, 2019Q1 to 2026Q2', loc='left')
    axes[1].legend(frameon=False, fontsize=8)
    fig.suptitle('Modal GPU experiment: a model must earn its complexity', x=.02, ha='left', fontsize=15)
    fig.text(.02, .015, 'Revised historical data. Exploratory extension. Seed variation measures training instability, not borrower risk.', fontsize=9)
    fig.tight_layout(rect=[0, .045, 1, .94])
    fig.savefig(ROOT / 'reports/figures/09_gpu_experiment.png', dpi=170)
    plt.close(fig)
    conclusion = ('The neural ensemble had lower MAE than persistence in this retrospective comparison. That is evidence to investigate further, not enough to replace the benchmark in production.' if improvement > 0 else 'The neural ensemble did not beat persistence on MAE. The additional GPU computation does not justify replacing the simple benchmark.')
    rows = '\n'.join(f'| {r.model} | {r.mae:.3f} | {r.rmse:.3f} |' for r in scores.itertuples())
    report = f'''# Does a GPU neural model improve household pressure monitoring?

The business question is whether a more complex model adds useful information beyond the last published debt service ratio. A retail banking analyst needs a reliable monitoring signal, not a complicated model for its own sake.

{conclusion}

## Results

| Model | MAE, percentage points | RMSE, percentage points |
| :--- | ---: | ---: |
{rows}

The selected neural ensemble changed MAE by {improvement:.1f}% relative to persistence, where a positive number means improvement. Its paired MAE difference was {difference.mean():.3f} percentage points. The descriptive 95% block bootstrap interval was [{audit['block4_interval'][0]:.3f}, {audit['block4_interval'][1]:.3f}] using four quarter blocks and [{audit['block8_interval'][0]:.3f}, {audit['block8_interval'][1]:.3f}] using eight quarter blocks. These short sample diagnostics do not establish future performance.

![GPU model comparison](figures/09_gpu_experiment.png)

The empirical 90% band covered {coverage:.1%} of the 30 retrospective test quarters. It was calibrated using validation errors, which were also used for model selection. It has no guaranteed coverage.

## What ran on Modal

Eight H100 workers evaluated two hidden widths, two weight decay settings and two training lengths. Each model has two tanh hidden layers and predicts the next quarter change from the same eight features as the original analysis. AdamW uses learning rate 0.003. Widths are 32 and 64, weight decay is 0.01 and 0.1, and training lasts 250 or 750 epochs. This is a small exploratory grid, not an exhaustive model search.

Training windows are expanded through time. Each window has its own training only normalization and independent network parameters. Batched matrix multiplication lets the GPU fit many independent windows and seeds at once. The original data still contain only 146 quarters; parallel training does not create new observations.

The workers completed {audit['completed_fits']:,} individual network fits. For a fair comparison, every configuration uses the same first {seeds:,} random seed replicates, or {audit['matched_fits_used']:,} matched fits across 79 origins. The configuration was selected using ensemble MAE in 2007Q1 to 2018Q4. Later errors were not used to choose it. The selected configuration is {audit['configuration']}.

The 10th to 90th percentile of individual seed test MAE was {audit['individual_seed_test_mae_p10_p90'][0]:.3f} to {audit['individual_seed_test_mae_p10_p90'][1]:.3f}. That range measures sensitivity to initialization. It is not a confidence interval for the economy. The reported ensemble averages predictions across matched seeds.

## A concrete monitoring check

As an illustrative sensitivity check, a worsening quarter means a debt service ratio increase of at least 0.10 percentage points. A flag means the model predicts an increase at least that large. This threshold was specified before the GPU results and is not a bank approved policy. Precision and recall, including raw counts, are saved in gpu_comparison.csv. Persistence cannot anticipate an increase because it predicts no change. No financial loss or customer outcome is estimated from this check.

## Cost and limits

Measured main worker runtime implies approximately US${cost:.2f} in H100 usage, or US${total:.2f} including the saved successful smoke test. The first smoke attempt also used about 30 GPU seconds before its result serialization failed. This estimate uses Modal's published US$0.001097 per GPU second and excludes startup, image building, CPU and memory. It is not a verified invoice. The run used a fixed compute allowance requested for this experiment; it is not a claim that this dataset needs that spend. Future refreshes can use the saved results without launching GPUs.

Each main worker has a 1,150 second work budget, a 1,180 second execution timeout, zero retries and a short scale down window. The repeated seed experiment stops by time, not by whether an attractive result appears. Partially trained batches are discarded. The source data digest, device names, runtime, settings and complete seed predictions are saved in the repository.

This experiment was designed after the original 2019 to 2026 test result was known. Its later period is therefore an exploratory retrospective comparison, not a fresh untouched test. Revised historical values and publication delays remain limitations. A future prospective evaluation using archived releases would be needed before relying on the model in a live workflow. No causal effect, borrower default probability or TD portfolio performance is claimed.

[Modal pricing](https://modal.com/pricing) · [Experiment code](../experiments/gpu_benchmark.py) · [Audit](../data/processed/gpu_audit.json)
'''
    (ROOT / 'reports/gpu_experiment.md').write_text(report, encoding='utf-8')
    print(json.dumps(audit, indent=2))
    return audit


if __name__ == '__main__':
    summarize()
