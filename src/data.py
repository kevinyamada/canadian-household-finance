from pathlib import Path
import hashlib
import json
import sqlite3
import zipfile
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
OUT = ROOT / 'data/processed'
AS_OF = '2026-11-14'
SOURCES = {
    '11100065-eng.zip': 'https://www150.statcan.gc.ca/n1/en/tbl/csv/11100065-eng.zip',
    'policy_rate.json': 'https://www.bankofcanada.ca/valet/observations/V39079/json?start_date=1990-01-01&end_date=2026-11-13'
}
COLUMNS = {
    'Debt service ratio': 'dsr',
    'Mortgage debt service ratio': 'mortgage_dsr',
    'Non-mortgage debt service ratio': 'other_dsr',
    'Debt service ratio, interest only': 'interest_dsr',
    'Equals: disposable income before payment of interest': 'income',
    'Disposable income ': 'disposable_income',
    'Total debt payments': 'payments',
    'Mortgage debt payments': 'mortgage_payments',
    'Non-mortgage debt payments': 'other_payments',
    'Total interest paid': 'interest',
    'Total obligated payments of principal': 'principal',
    'Mortgage interest paid': 'mortgage_interest',
    'Non-mortgage interest paid': 'other_interest'
}

def download(refresh=False):
    RAW.mkdir(parents=True, exist_ok=True)
    records = []
    for name, url in SOURCES.items():
        path = RAW / name
        if refresh or not path.exists():
            response = requests.get(url, timeout=90)
            response.raise_for_status()
            path.write_bytes(response.content)
        records.append({'file': name, 'url': url, 'snapshot_date': AS_OF,
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size})
    (RAW / 'manifest.json').write_text(json.dumps(records, indent=2))

def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(RAW / '11100065-eng.zip') as archive:
        raw = pd.read_csv(archive.open('11100065.csv'))
        (RAW / '11100065_metadata.csv').write_bytes(archive.read('11100065_MetaData.csv'))
    selected = raw[(raw['GEO'] == 'Canada') &
                   (raw['Seasonal adjustment'] == 'Seasonally adjusted at annual rates') &
                   raw['Estimates'].isin(COLUMNS)].copy()
    if selected.duplicated(['REF_DATE', 'Estimates']).any():
        raise ValueError('Duplicate quarter and indicator')
    if selected['VALUE'].isna().any() or selected['STATUS'].notna().any():
        raise ValueError('Missing or flagged StatCan observation requires review')
    dollars = selected['UOM'] == 'Dollars'
    if not selected.loc[dollars, 'SCALAR_FACTOR'].eq('millions').all():
        raise ValueError('Unexpected dollar scale')
    wide = selected.pivot(index='REF_DATE', columns='Estimates', values='VALUE').rename(columns=COLUMNS)
    wide.index = pd.to_datetime(wide.index).to_period('Q')
    wide.index.name = 'quarter'
    wide = wide.sort_index()
    if not wide.index.equals(pd.period_range(wide.index.min(), wide.index.max(), freq='Q', name='quarter')):
        raise ValueError('Missing quarter')
    if wide.isna().any().any():
        raise ValueError('Incomplete indicator panel')
    ratio_error = (100 * wide['payments'] / wide['income'] - wide['dsr']).abs().max()
    component_error = (wide['payments'] - wide['mortgage_payments'] - wide['other_payments']).abs().max()
    interest_error = (wide['payments'] - wide['principal'] - wide['interest']).abs().max()
    if ratio_error > 0.0051 or component_error > 1 or interest_error > 1:
        raise ValueError('Debt accounting identities failed')
    policy_json = json.loads((RAW / 'policy_rate.json').read_text())
    policy = pd.DataFrame([{'date': x['d'], 'policy_rate': float(x['V39079']['v'])}
                           for x in policy_json['observations'] if 'V39079' in x])
    policy = policy[policy['date'] <= '2026-11-13']
    policy['quarter'] = pd.to_datetime(policy['date']).dt.to_period('Q').astype(str)
    policy_quarterly = policy.groupby('quarter', as_index=False).agg(policy_rate=('policy_rate', 'last'),
                    policy_business_days=('policy_rate', 'size'), policy_last_date=('date', 'max'))
    policy.to_csv(OUT / 'policy_daily.csv', index=False)
    panel = wide.reset_index()
    panel['quarter'] = panel['quarter'].astype(str)
    panel['date'] = pd.PeriodIndex(panel['quarter'], freq='Q').to_timestamp().strftime('%Y-%m-%d')
    panel['income_growth'] = panel['income'].pct_change() * 100
    panel['payment_growth'] = panel['payments'].pct_change() * 100
    panel['mortgage_share'] = panel['mortgage_payments'] / panel['payments'] * 100
    panel['principal_dsr'] = panel['dsr'] - panel['interest_dsr']
    with sqlite3.connect(OUT / 'finance.sqlite') as db:
        panel.to_sql('household', db, index=False, if_exists='replace')
        policy_quarterly.to_sql('policy', db, index=False, if_exists='replace')
        db.executescript((ROOT / 'sql/analysis.sql').read_text())
        panel = pd.read_sql_query('SELECT * FROM quarterly_panel ORDER BY quarter', db)
        pd.read_sql_query('SELECT * FROM recent_changes', db).to_csv(OUT / 'recent_changes.csv', index=False)
    panel.to_csv(OUT / 'quarterly_panel.csv', index=False)
    selected[['Estimates','VECTOR','UOM','SCALAR_FACTOR']].drop_duplicates().rename(columns={'Estimates':'indicator','VECTOR':'vector','UOM':'unit','SCALAR_FACTOR':'scale'}).to_csv(OUT/'data_dictionary.csv',index=False)
    quality = {'raw_rows': len(raw), 'selected_rows': len(selected), 'quarters': len(panel),
               'start': panel.quarter.iloc[0], 'end': panel.quarter.iloc[-1], 'duplicate_keys': 0,
               'missing_core_values': 0, 'max_dsr_rounding_error_pp': float(ratio_error),
               'max_payment_component_error_millions': float(component_error),
               'max_principal_interest_error_millions': float(interest_error),
               'policy_missing_quarters': int(panel.policy_rate.isna().sum()),
               'policy_use': 'Context only; never backfilled into the primary forecast',
               'source_vintage': AS_OF}
    (OUT / 'quality.json').write_text(json.dumps(quality, indent=2))
    return panel
