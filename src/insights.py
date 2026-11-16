"""Turn the validated outputs into a dated, source-backed decision summary."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def collect(root=ROOT):
    out = root / 'data/processed'
    segments = pd.read_csv(out / 'segment_latest.csv')
    group_quarter = segments.quarter.max()
    latest = segments[segments.quarter == group_quarter].set_index('group')
    assert latest.index.is_unique, 'The insight summary requires one row per household group'
    renter, owner = latest.loc['Renter'], latest.loc['Owner with mortgage']
    national = json.loads((out / 'summary.json').read_text())
    model = json.loads((out / 'model_audit.json').read_text())['selected_model']
    scores = pd.read_csv(out / 'holdout_scores.csv').set_index('model')
    gpu = pd.read_csv(out / 'gpu_comparison.csv').set_index('model')
    predictions = pd.read_csv(out / 'selected_predictions.csv')
    baseline, selected = float(scores.loc['Persistence', 'mae']), float(scores.loc[model, 'mae'])
    neural = float(gpu.loc['GPU neural ensemble', 'mae'])
    gap, pension, saving = float(renter.income_less_consumption), float(renter.pension), float(renter.saving)
    assert abs(gap + pension - saving) <= 2, 'Saving evidence must reconcile before interpretation'
    special_saving = gap < 0 < saving
    income_faster = national['payment_growth_pct'] > 0 and national['income_growth_pct'] > national['payment_growth_pct'] and national['qoq_change_pp'] < 0
    keep_baseline = baseline <= min(selected, neural)
    review_run = json.loads((out / 'audit_experiment.json').read_text())
    review_score = pd.read_csv(out / 'audit_method_comparison.csv').set_index('method').loc['Selected AI reviewer']
    review = {key: float(review_score[key]) for key in ['unsupported_recall', 'false_alarm_rate', 'abstention_rate']}
    review.update({key: review_run[key] for key in ['unique_evaluation_cases', 'common_complete_repetitions']})
    cards = [
        {
            'id': 'groups', 'title': 'Compare different kinds of household pressure',
            'period': f'Household groups | {group_quarter}',
            'evidence': f"Debt / annualized disposable income: mortgage owners {owner.debt_income_pct:.1f}%; renters {renter.debt_income_pct:.1f}%.",
            'meaning': 'Debt relative to income and income relative to consumption measure different kinds of pressure.',
            'action': 'Review leverage and income relative to consumption separately.',
            'metrics': {'mortgage_debt_income_pct': float(owner.debt_income_pct), 'renter_debt_income_pct': float(renter.debt_income_pct)},
            'source': 'data/processed/segment_latest.csv',
            'detail_page': 'Household groups',
        },
        {
            'id': 'saving',
            'title': 'Positive saving can hide an income gap' if special_saving else 'Read saving with its pension adjustment',
            'period': f'Renter average | {group_quarter}',
            'evidence': f'Income less consumption: CAD {gap:+,.0f}. Pension adjustment: CAD {pension:+,.0f}. Net saving: CAD {saving:+,.0f}.',
            'meaning': 'The pension adjustment changes the sign. Positive net saving does not mean income covered consumption.' if special_saving else 'Net saving includes the pension adjustment as well as income less consumption.',
            'action': 'Show all three components before describing household saving.',
            'metrics': {'income': float(renter.income), 'consumption': float(renter.consumption), 'income_less_consumption': gap, 'pension_adjustment': pension, 'net_saving': saving},
            'source': 'data/processed/segment_latest.csv',
            'detail_page': 'Reporting controls',
        },
        {
            'id': 'national',
            'title': 'Payments rose while the ratio fell' if income_faster else 'Read payments and income together',
            'period': f'National payment ratio | {national["latest_quarter"]}',
            'evidence': f"Ratio {national['latest_dsr']:.2f}%. Payments {national['payment_growth_pct']:+.2f}%; income {national['income_growth_pct']:+.2f}% quarter over quarter.",
            'meaning': 'Income grew faster than required payments. The lower ratio does not mean payments fell.' if income_faster else 'The ratio reflects changes in both required payments and income.',
            'action': 'Monitor payment growth alongside income growth.',
            'metrics': {k: national[k] for k in ['latest_dsr', 'qoq_change_pp', 'payment_growth_pct', 'income_growth_pct']},
            'source': 'data/processed/summary.json',
            'detail_page': 'Household pressure',
        },
        {
            'id': 'forecast',
            'title': 'Complex models had higher average error' if keep_baseline else 'Review the model comparison',
            'period': f"Forecast test | {predictions.quarter.min()} to {predictions.quarter.max()}",
            'evidence': f'Average absolute error: previous quarter {baseline:.3f}; {model.lower()} {selected:.3f}; neural {neural:.3f} percentage points.',
            'meaning': 'Lower error is better. The small sample does not establish a clear model advantage; the neural extension is exploratory.',
            'action': 'Keep the previous-quarter forecast as the benchmark.' if keep_baseline else 'Validate on new releases before changing the benchmark.',
            'metrics': {'baseline_mae_pp': baseline, 'selected_model': model, 'selected_mae_pp': selected, 'neural_mae_pp': neural, 'test_quarters': int(scores.loc['Persistence', 'n'])},
            'source': 'data/processed/holdout_scores.csv; data/processed/gpu_comparison.csv',
            'detail_page': 'Model evaluation and GPU experiment',
        },
    ]
    return {
        'group_quarter': group_quarter,
        'national_quarter': national['latest_quarter'],
        'cards': cards,
        'review': review,
        'scope': 'Public household group averages. They support reporting review and investigation, not individual default predictions. Group and national dates differ.',
    }


def render_brief(summary, root):
    import textwrap
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    fig = plt.figure(figsize=(13.6, 9.8), facecolor='#F2F5F4')
    fig.text(.05, .947, 'Four findings. Four next actions.', fontsize=24, weight='bold', color='#183D40')
    fig.text(.05, .91, f"Canadian Household Finance | Groups: {summary['group_quarter']} | National: {summary['national_quarter']}", fontsize=11, color='#52666B')
    for index, card in enumerate(summary['cards']):
        x = .05 if index % 2 == 0 else .52
        y = .515 if index < 2 else .12
        ax = fig.add_axes([x, y, .43, .35])
        ax.set_axis_off()
        ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle='round,pad=0.012,rounding_size=0.018', transform=ax.transAxes, facecolor='white', edgecolor='#D9E5E0', clip_on=False))
        ax.text(.035, .95, textwrap.fill(f"{index + 1}. {card['title']}", 43), va='top', fontsize=13, weight='bold', color='#183D40')
        ax.text(.035, .77, card['period'], va='top', fontsize=9, color='#63747D')
        ax.text(.035, .665, textwrap.fill(card['evidence'], 52), va='top', fontsize=12, color='#183D40', linespacing=1.35)
        ax.text(.035, .39, textwrap.fill(card['meaning'], 65), va='top', fontsize=10, color='#35444A', linespacing=1.3)
        ax.text(.035, .17, textwrap.fill('Next: ' + card['action'], 55), va='top', fontsize=10.5, weight='bold', color='#176B61', linespacing=1.3)
    fig.text(.05, .06, 'Source-backed Python summary. The same findings appear on the opening Power BI page.', fontsize=10, color='#183D40')
    fig.text(.05, .028, 'Group dollars: CAD per household for the quarter. Public averages support investigation, not individual default predictions.', fontsize=9, color='#52666B')
    target = root / 'reports/figures/17_key_insights.png'
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=170, facecolor=fig.get_facecolor())
    plt.close(fig)


def generate(root=ROOT):
    summary = collect(root)
    (root / 'data/processed/key_insights.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    lines = [
        '# What the analysis says and what to do next', '',
        '**Decision:** ' + ' '.join(card['action'] for card in summary['cards']), '',
        f"Group findings use **{summary['group_quarter']}**; the national payment finding uses **{summary['national_quarter']}**. These are separate snapshots.", '',
    ]
    for i, card in enumerate(summary['cards'], 1):
        lines.extend([
            f"## {i}. {card['title']}", '', f"**{card['period']}**", '',
            card['evidence'], '', card['meaning'], '',
            f"**Action:** {card['action']}", '',
            f"**Inspect:** Power BI → {card['detail_page']}. Evidence: `{card['source']}`.", '',
        ])
    lines.extend([
        '## What the AI experiment adds', '',
        f"The saved H100 experiment tests review of deliberately misleading statements against trusted evidence cards. The selected reviewer flagged {summary['review']['unsupported_recall']:.2%} of unsupported evaluation examples, with a {summary['review']['false_alarm_rate']:.2%} false alarm rate on supported examples. These are {summary['review']['unique_evaluation_cases']:,} unique, balanced template cases, with {summary['review']['common_complete_repetitions']} matched repetitions. The result supports a review prototype; it does not establish reliability on arbitrary bank reports. A comprehensive rules baseline and independently reviewed real excerpts are the next validation.", '',
        '## Actions completed in this project', '',
        '- Added this summary and the opening Key insights page, with dates, evidence and a next action for each finding.',
        '- Kept the renter saving components separate and reconciled their accounting identity.',
        '- Compared forecasts with the previous-quarter benchmark and retained the measured result.',
        '- Preserved source snapshots, review exceptions and saved GPU outputs so the results can be checked without another paid run.', '',
        '## What requires further evidence', '',
        'Portfolio validation needs approved borrower data. Live forecasting evaluation needs new releases and archived vintages. General AI review validation needs independently labeled real report wording. The [next-step plan](../docs/next_steps.md) specifies the inputs and acceptance evidence for each.', '',
        summary['scope'], '',
        '[Plain-language walkthrough](../docs/project_walkthrough.md) · [Group findings](segment_findings.md) · [National analysis](analysis.md) · [AI benchmark](audit_benchmark.md)', '',
    ])
    (root / 'reports/key_insights.md').write_text('\n'.join(lines), encoding='utf-8')
    render_brief(summary, root)
    print('Generated four dated insights, their actions and the Python summary figure')
    return summary


if __name__ == '__main__':
    generate()
