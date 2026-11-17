"""Decision-changing audit errors, dated-rate coverage and published-update reconciliations."""
import copy
from dataclasses import replace
from pathlib import Path
import json
import sqlite3
import sys
import numpy as np
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from homebuying_model import PROFILES,evaluate
from homebuying_data import CITIES,RATE_SERIES
from homebuying_updates import error_review
from refresh_homebuying_sources import latest_common_rates,load_refresh
OUT=ROOT/"data/processed"

def fixture_payload(kind,points):
    code=RATE_SERIES[kind]
    return {"seriesDetail":{code:{"label":"Fixed rate, 5 years and over",
        "description":f"Mortgages - Funds advanced - Residential mortgages, {kind}, Total"}},
        "observations":[{"d":month,code:{"v":str(rate)}} for month,rate in points]}

def pair(ins=None,unins=None):
    return {"insured":fixture_payload("insured",ins or [("2026-08-01",4)]),
            "uninsured":fixture_payload("uninsured",unins or [("2026-08-01",4.5)])}

def audit_case(buyer=None,price=500000,insured=4,uninsured=4.5):
    b=buyer or replace(PROFILES[0],liquid_cash=100000)
    row=evaluate(price,b,"BC",.003,insured,uninsured)
    row.update(city="Vancouver",profile=b.id,profile_label=b.name,case_id="test-case",scenario="baseline",scenario_label="Baseline")
    return {r["variant"]:r for r in error_review(row)}

def test_latest_rates_use_common_month_and_exclude_future_points():
    payload=pair([("2026-08-01",4),("2026-09-01",4.1),("2026-12-01",99)],
                 [("2026-08-01",4.5),("2026-12-01",99)])
    assert latest_common_rates(payload,"2026-11-17")=={"period":"2026-08","insured":4,"uninsured":4.5}

def test_no_common_month_is_rejected():
    with pytest.raises(ValueError,match="No common"):
        latest_common_rates(pair([("2026-07-01",4)],[("2026-08-01",4.5)]),"2026-11-17")

def test_duplicate_month_is_rejected():
    with pytest.raises(ValueError,match="Duplicate"):
        latest_common_rates(pair([("2026-08-01",4),("2026-08-01",4.1)]),"2026-11-17")

@pytest.mark.parametrize("value",[-1,float("nan"),float("inf")])
def test_invalid_latest_rate_is_rejected(value):
    with pytest.raises(ValueError,match="Invalid"):
        latest_common_rates(pair([("2026-08-01",value)]),"2026-11-17")

@pytest.mark.parametrize("kind",["insured","uninsured"])
def test_outstanding_or_wrong_insurance_series_cannot_replace_new_lending(kind):
    p=pair();p[kind]["seriesDetail"][RATE_SERIES[kind]]["description"]="Outstanding balances"
    with pytest.raises(ValueError,match="funds-advanced"):
        latest_common_rates(p,"2026-11-17")

def test_official_refreshed_snapshot_identity_and_period():
    manifest,review,rates=load_refresh()
    assert manifest["checked_on"]=="2026-11-17"
    assert review["latest_sales_year"]==2023 and review["property_reference_year"]==2024
    assert rates=={"period":"2026-09","insured":4.15,"uninsured":4.66}
    assert "not re-downloaded" in review["extract_status"]
    assert any(i.get("status")==403 for i in manifest["retrieval_attempts"])

def test_controlled_wrong_rate_creates_a_false_pass_in_the_worked_case():
    frame=pd.read_csv(OUT/"homebuying_calculation_audit.csv")
    g=frame[frame.city.eq("Vancouver")&frame.profile.eq("couple")&frame.scenario.eq("price10")].set_index("variant")
    assert g.loc["correct","required_gross_income"]==pytest.approx(167429.3380878,abs=.001)
    assert g.loc["contract_rate","required_gross_income"]==pytest.approx(141542.6670482,abs=.001)
    assert not bool(g.loc["correct","financial_pass"])
    assert bool(g.loc["contract_rate","false_pass"])
    assert g.loc["contract_rate","income_understated"]==pytest.approx(25886.6710396,abs=.001)

def test_omitted_debt_matters_when_tds_binds():
    b=replace(PROFILES[0],liquid_cash=100000,monthly_debt=2500)
    rows=audit_case(b)
    assert rows["omit_debt"]["required_gross_income"]<rows["correct"]["required_gross_income"]
    assert rows["omit_debt"]["other_debt_used"]==0

def test_no_premium_means_omitting_premium_has_no_effect():
    rows=audit_case(replace(PROFILES[0],liquid_cash=250000))
    assert rows["omit_premium"]["required_gross_income"]==pytest.approx(rows["correct"]["required_gross_income"])
    assert rows["omit_premium"]["income_understated"]==pytest.approx(0)

def test_cash_short_cannot_be_counted_as_a_false_pass():
    rows=audit_case(replace(PROFILES[0],liquid_cash=1000,gross_income=1000000))
    assert all(not r["cash_pass"] and not r["financial_pass"] and not r["false_pass"] for r in rows.values())

def test_cash_purchase_requires_no_mortgage_income_in_every_variant():
    rows=audit_case(replace(PROFILES[0],liquid_cash=800000))
    assert all(r["required_gross_income"]==0 and not r["false_pass"] for r in rows.values())

def test_deliberate_omissions_do_not_raise_required_income():
    rows=pd.read_csv(OUT/"homebuying_calculation_audit.csv")
    assert len(rows)==585 and rows.case_id.nunique()==117
    assert not rows.duplicated(["case_id","variant"]).any()
    assert (rows.required_gross_income<=rows.correct_required_income+1e-7).all()
    assert rows.loc[rows.false_pass,"cash_pass"].all()
    correct=rows[rows.variant.eq("correct")]
    assert np.allclose(correct.required_gross_income,correct.correct_required_income,rtol=0,atol=1e-7)
    assert not correct.false_pass.any()

def test_all_audit_rows_reconcile_to_separate_sql_expressions():
    with sqlite3.connect(OUT/"homebuying.sqlite") as db:
        rows=pd.read_sql_query("SELECT * FROM calculation_audit_reconciliation",db)
    assert len(rows)==585
    assert rows.required_income_delta.abs().max()<1e-7
    assert rows.false_pass_delta.eq(0).all()

def test_newer_rates_do_not_change_price_cash_or_cost_assumptions():
    latest=pd.read_csv(OUT/"homebuying_latest_rates.csv").set_index(["city","profile"])
    base=pd.read_csv(OUT/"homebuying_cases.csv")
    base=base[base.year.eq(2023)&base.scenario.eq("baseline")].set_index(["city","profile"])
    assert len(latest)==9 and latest.rate_period.eq("2026-09").all()
    for column in ["price","profile_cash","profile_income","annual_property_tax","mortgage_principal","heating","condo_fee"]:
        assert np.allclose(latest.sort_index()[column],base.sort_index()[column],rtol=0,atol=1e-7)
    assert latest.scope.str.contains("Not observed current affordability").all()
    assert set(latest.contract_rate)=={4.15,4.66}

def test_newer_rate_price_limits_pass_and_next_dollar_fails():
    frame=pd.read_csv(OUT/"homebuying_latest_rate_limits.csv")
    buyers={b.id:b for b in PROFILES}
    for row in frame.itertuples():
        spec=CITIES[row.city]
        args=(buyers[row.profile],spec["province"],spec["tax_rate"],4.15,4.66)
        limit=evaluate(row.maximum_price,*args)
        beyond=evaluate(row.maximum_price+1,*args)
        assert limit["cash_pass"] and limit["income_pass"]
        assert not(beyond["cash_pass"] and beyond["income_pass"])
        assert row.maximum_price_display<=row.maximum_price

def test_saved_updates_match_website_payload():
    payload=json.loads((ROOT/"docs/assets/homebuying-data.json").read_text(encoding="utf-8"))
    assert len(payload["latest_rate_cases"])==9 and len(payload["calculation_audit"])==585
    assert payload["source_freshness"]["current_rate_sensitivity_not_current_market"]
    audit=pd.read_csv(OUT/"homebuying_calculation_audit.csv").set_index(["case_id","variant"]).sort_index()
    web=pd.DataFrame(payload["calculation_audit"]).set_index(["case_id","variant"]).sort_index()
    assert np.allclose(audit.required_gross_income,web.required_gross_income,rtol=0,atol=1e-7)

def test_powerbi_new_imports_match_saved_results():
    import base64
    import re
    model=json.loads((ROOT/"powerbi/HomebuyingBarriers.SemanticModel/model.bim").read_text(encoding="utf-8"))["model"]
    tables={t["name"]:t for t in model["tables"]}
    for name,file,keys,columns in [
        ("LatestRates","homebuying_latest_rates.csv",["city","profile"],["price","monthly_mortgage","required_gross_income","income_gap"]),
        ("LatestRateLimits","homebuying_latest_rate_limits.csv",["city","profile"],["maximum_price","maximum_price_display"]),
        ("CalculationAudit","homebuying_calculation_audit.csv",["case_id","variant"],["required_gross_income","income_understated","false_pass"])]:
        expression="\n".join(tables[name]["partitions"][0]["source"]["expression"])
        encoded=re.search(r'Binary.FromText\("([^"]+)"',expression).group(1)
        actual=pd.DataFrame(json.loads(base64.b64decode(encoded))).set_index(keys).sort_index()
        expected=pd.read_csv(OUT/file).set_index(keys).sort_index()
        assert list(actual.index)==list(expected.index)
        for column in columns:
            assert np.allclose(actual[column].astype(float),expected[column].astype(float),rtol=0,atol=1e-7)
