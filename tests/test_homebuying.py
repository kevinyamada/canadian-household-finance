"""Financial boundaries, published examples, source flags and independent reconciliations."""
from dataclasses import replace
from pathlib import Path
import hashlib
import json
import sqlite3
import sys
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from homebuying_model import (Buyer, PROFILES, minimum_down, insurance_premium,
    monthly_payment, balance_after, transfer_tax, affordable_down, evaluate, waiting_cash)
from homebuying_data import published_number, observed_data, annual_rates, verify_manifest, trusted_url
OUT = ROOT / "data/processed"

@pytest.mark.parametrize("rate,payment", [(2.5,1343.90),(2.9,1404.39),(3.4,1482.02),
    (3.8,1545.70),(4.5,1660.42),(4.8,1710.82),(5,1744.81),(5.2,1779.13)])
def test_fcac_published_monthly_examples(rate, payment):
    assert monthly_payment(300000, rate, 25) == pytest.approx(payment, abs=.02)

def test_fcac_four_percent_transposition_is_not_copied_into_model():
    # FCAC's monthly cell says 1,587.06, but its total interest implies 1,578.06.
    # Preserve this source discrepancy rather than changing the financial formula to fit it.
    implied = (300000 + 173418.18) / 300
    assert monthly_payment(300000, 4, 25) == pytest.approx(implied, abs=.02)
    assert abs(monthly_payment(300000, 4, 25) - 1587.06) > 8.9

@pytest.mark.parametrize("years,payment", [(20,1971.38),(30,1601.07)])
def test_fcac_amortization_examples(years, payment):
    assert monthly_payment(300000,5,years) == pytest.approx(payment,abs=.02)

def test_fcac_first_five_years_interest_and_balance():
    monthly = monthly_payment(300000,5,25)
    balance = balance_after(300000,5,25,60)
    assert monthly*60-(300000-balance) == pytest.approx(70211.42,abs=.05)
    assert balance_after(300000,0,25,60) == 240000

@pytest.mark.parametrize("price,down", [(400000,20000),(500000,25000),
    (600000,35000),(1499999,124999.9),(1500000,300000)])
def test_minimum_down_boundaries(price,down):
    assert minimum_down(price) == pytest.approx(down)

@pytest.mark.parametrize("invalid", [-1,0,float("nan"),float("inf")])
def test_invalid_price_rejected(invalid):
    with pytest.raises(ValueError):
        minimum_down(invalid)

@pytest.mark.parametrize("down,rate", [(25000,.04),(50000,.031),(75000,.028),(100000,0)])
def test_insurance_tier_exact_boundaries(down,rate):
    assert insurance_premium(500000,down) == pytest.approx((500000-down)*rate)

def test_insured_thirty_year_surcharge_and_eligibility():
    assert insurance_premium(500000,25000,30)-insurance_premium(500000,25000,25) == pytest.approx(950)
    with pytest.raises(ValueError):
        evaluate(500000,replace(PROFILES[0],first_time=False),"BC",.003,4,4,years=30)

def test_transfer_tax_boundaries_and_condition():
    assert transfer_tax(500000,"BC",True) == (0,8000,8000)
    assert transfer_tax(835000,"BC",True) == (6700,14700,8000)
    assert transfer_tax(849000,"BC",True) == (11460,14980,3520)
    assert transfer_tax(860000,"BC",True) == (15200,15200,0)
    assert transfer_tax(849000,"BC",False) == (14980,14980,0)
    assert transfer_tax(460000,"NS",True) == (6900,6900,0)
    with pytest.raises(ValueError):
        transfer_tax(500000,"ON",True)

@pytest.mark.parametrize("cash", [10000,50000,64000,89000,114000,514000,600000])
def test_cash_budget_at_insurance_cliffs(cash):
    buyer = replace(PROFILES[0],liquid_cash=cash)
    down, feasible = affordable_down(500000,buyer,0,25)
    if feasible:
        assert down+buyer.closing_allowance+buyer.reserve <= cash+1e-6
        assert down == pytest.approx(min(500000,cash-14000))
    else:
        assert down == 25000
        assert cash < 39000

def test_stress_floor_debt_and_reserve_are_distinct():
    b = replace(PROFILES[0],liquid_cash=100000,monthly_debt=2000)
    row = evaluate(500000,b,"BC",.003,2,2)
    assert row["qualifying_rate"] == 5.25
    assert row["required_gross_income"] == pytest.approx(
        max(row["housing_costs_for_ratios"]/.39,(row["housing_costs_for_ratios"]+2000)/.44)*12)
    assert row["cash_spent"]+b.reserve == pytest.approx(b.liquid_cash)
    assert row["tds"] > row["gds"]

def test_cash_short_income_is_explicitly_conditional():
    r = evaluate(849000,PROFILES[0],"BC",.0027807,5.125,5.5)
    assert not r["cash_pass"] and not r["income_pass"]
    assert r["down_used"] == r["minimum_down"]
    assert r["income_scope"] == "If minimum cash were available"

def test_cash_purchase_requires_no_mortgage_income():
    r = evaluate(400000,replace(PROFILES[0],liquid_cash=600000),"BC",.003,4,4)
    assert r["mortgage_principal"] == 0
    assert r["required_gross_income"] == 0

@pytest.mark.parametrize("status", [0,2,3,4,5,6,7])
def test_valid_published_quality_flags_are_retained(status):
    assert published_number({"statusCode":status,"securityLevelCode":0,"value":123}) == 123

@pytest.mark.parametrize("status", [1,8,9])
def test_unavailable_or_unreliable_values_stay_missing(status):
    assert published_number({"statusCode":status,"securityLevelCode":0,"value":123}) is None
    assert published_number({"statusCode":0,"securityLevelCode":1,"value":123}) is None

def test_source_policy_and_checksums():
    assert verify_manifest()["sources"]
    assert trusted_url("https://www150.statcan.gc.ca/t1/wds/rest/getCodeSets")
    assert not trusted_url("https://statcan.gc.ca.example.com/data")
    assert not trusted_url("http://www.statcan.gc.ca/data")

def test_source_grains_and_vintage_bridge():
    long,observed,bridge = observed_data()
    assert len(observed) == 12 and not observed.duplicated(["city","year"]).any()
    assert set(observed.loc[observed.year.eq(2020),"geography_vintage"]) == {2016}
    assert set(observed.loc[observed.year.ge(2021),"geography_vintage"]) == {2021}
    assert len(bridge) == 6
    assert len(observed.csd.unique()) == 3
    assert set(observed.city) == {"Vancouver","Victoria","Halifax"}
    assert observed.loc[(observed.city=="Vancouver") & (observed.year==2023),"buyer_median_sale_price"].item() == 849000
    # Never replace the published median of ratios with the ratio of medians.
    row = observed.loc[(observed.city=="Victoria") & (observed.year==2023)].iloc[0]
    assert row.published_median_price_income_ratio != pytest.approx(row.buyer_median_sale_price/row.buyer_family_median_income)

def test_rates_are_complete_funds_advanced_series():
    rates = annual_rates()
    assert len(rates) == 12 and rates.months.eq(12).all()
    assert set(rates.series) == {"V122667780","V122667786"}
    assert rates.loc[(rates.year==2023)&(rates.kind=="insured"),"rate"].item() == pytest.approx(5.125)

def test_all_cases_reconcile_in_independent_sql():
    with sqlite3.connect(OUT/"homebuying.sqlite") as db:
        rows = pd.read_sql_query("SELECT * FROM case_reconciliation",db)
        baseline = pd.read_sql_query("SELECT * FROM latest_baseline",db)
    assert len(rows) >= 468 and len(baseline)==9
    assert rows.required_income_delta.abs().max() < 1e-7
    assert rows.cash_target_delta.abs().max() < 1e-7
    assert int((baseline.cash_pass.eq(1)&baseline.income_pass.eq(0)).sum()) == 4

def test_shapley_components_sum_to_the_observed_input_comparison():
    frame = pd.read_csv(OUT/"homebuying_decomposition.csv")
    for city,group in frame.groupby("city"):
        assert len(group)==3
        assert group.contribution_cad.sum()+group.start_gap_cad.iloc[0] == pytest.approx(group.end_gap_cad.iloc[0],abs=1e-7)

def test_program_money_is_not_counted_twice():
    frame = pd.read_csv(OUT/"homebuying_programs.csv")
    fhsa = frame[frame.program.str.startswith("FHSA")]
    assert np.allclose(fhsa.liquid_cash_after-fhsa.liquid_cash_before,fhsa.fhsa_contribution*.30)
    hbp = frame[frame.program.str.startswith("HBP")]
    assert np.allclose(hbp.liquid_cash_after-hbp.liquid_cash_before,hbp.hbp_draw)
    assert np.allclose(hbp.hbp_future_annual_repayment,hbp.hbp_draw/15)

def test_waiting_cash_and_rent_sensitivity():
    for buyer in PROFILES:
        assert waiting_cash(buyer,12,0)==buyer.liquid_cash+12*buyer.monthly_saving
        assert waiting_cash(buyer,24,.06)<waiting_cash(buyer,24,0)
    cases = pd.read_csv(OUT/"homebuying_waiting.csv")
    assert len(cases)==162
    same=cases[(cases.city=="Vancouver")&(cases.profile=="couple")&(cases.months==12)&cases.annual_rent_growth.eq(0)]
    assert same.sort_values("annual_price_growth").required_gross_income.is_monotonic_increasing

def test_precomputed_website_payload_matches_hash_and_case_grain():
    manifest=json.loads((OUT/"homebuying_asset_manifest.json").read_text())
    asset=ROOT/manifest["file"]
    assert hashlib.sha256(asset.read_bytes()).hexdigest()==manifest["sha256"]
    payload=json.loads(asset.read_text())
    keys=[r["case_id"] for r in payload["cases"]]
    assert len(keys)==len(set(keys))
    assert all(r["assumed_buyer"] for r in payload["cases"])
    assert all(0<=m["x"]<=payload["map"]["width"] for m in payload["map"]["markers"])
    assert all(0<=m["y"]<=payload["map"]["height"] for m in payload["map"]["markers"])


def test_bank_audit_never_treats_missing_evidence_as_approval():
    audit=pd.read_csv(OUT/"homebuying_bank_audit.csv")
    assert len(audit)==72 and len(audit.case_id.unique())==9
    assert audit.review_conclusion.str.startswith("Hold:").all()
    assert (audit.status=="Evidence missing").sum()==45
    pair=audit[audit.city.eq("Vancouver")&audit.profile.eq("couple")]
    assert pair.loc[pair.control.eq("Purchase cash"),"status"].item()=="Modeled pass"
    assert pair.loc[pair.control.eq("Debt-service screen"),"status"].item()=="Modeled exception"

def test_later_rates_are_explicitly_replayed_against_old_prices():
    replay=pd.read_csv(OUT/"homebuying_rate_replay.csv")
    assert len(replay)==9
    assert replay.price_year.eq(2023).all() and replay.rate_year.eq(2025).all()
    assert replay.scope.str.contains("not observed 2025 affordability").all()
    assert replay.income_reduction.gt(0).all()

def test_published_figures_have_ten_pages_and_valid_hashes():
    from pypdf import PdfReader
    folder=ROOT/"reports/figures/homebuying"
    manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["assets"])==21
    for item in manifest["assets"]:
        assert hashlib.sha256((folder/item["file"]).read_bytes()).hexdigest()==item["sha256"]
    assert len(PdfReader(folder/"HomebuyingBarriers-Figures.pdf").pages)==10

def test_native_report_source_is_portable_and_has_ten_pages():
    folder=ROOT/"powerbi/HomebuyingBarriers.Report/definition/pages"
    pages=json.loads((folder/"pages.json").read_text(encoding="utf-8"))
    assert pages["pageOrder"]==["answer","cash","changes","limits","latest","history","waiting","audit","calculation_audit","file_review"]
    assert pages["activePageName"]=="answer"
    source=(ROOT/"powerbi/HomebuyingBarriers.SemanticModel/model.bim").read_text(encoding="utf-8")
    assert "Binary.FromText" in source and "File.Contents" not in source and "C:\\\\" not in source
    model=json.loads(source)["model"]
    assert {t["name"] for t in model["tables"]}>={"Cases","History","Programs","Waiting","Audit","Markets","Profiles"}


def test_powerbi_imported_case_values_and_relationship_grains():
    import base64
    import re
    model=json.loads((ROOT/"powerbi/HomebuyingBarriers.SemanticModel/model.bim").read_text(encoding="utf-8"))["model"]
    frames={}
    for table in model["tables"]:
        expression="\n".join(table["partitions"][0]["source"]["expression"])
        encoded=re.search(r'Binary.FromText\("([^"]+)"',expression).group(1)
        frames[table["name"]]=pd.DataFrame(json.loads(base64.b64decode(encoded)))
    expected=pd.read_csv(OUT/"homebuying_cases.csv")
    expected=expected[expected.year.eq(2023)].set_index("case_id").sort_index()
    actual=frames["Cases"].set_index("case_id").sort_index()
    assert list(expected.index)==list(actual.index)
    for column in ["cash_target","required_gross_income","income_gap","mortgage_principal"]:
        assert np.allclose(expected[column],actual[column],rtol=0,atol=1e-7)
    for relation in model["relationships"]:
        source=frames[relation["fromTable"]][relation["fromColumn"]]
        target=frames[relation["toTable"]][relation["toColumn"]]
        assert not target.duplicated().any()
        assert set(source)<=set(target),relation["name"]
