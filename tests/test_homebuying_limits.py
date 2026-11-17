"""Review the reported zeros and check thresholds against exhaustive independent searches."""
from dataclasses import replace
from pathlib import Path
import sys
import sqlite3
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from homebuying_model import Buyer,PROFILES,evaluate
from homebuying_limits import maximum_price,minimum_cash_for_income
from homebuying_review import money,position
from homebuying_data import CITIES,annual_rates
OUT=ROOT/"data/processed"

def small_buyer():
    return Buyer("small","Exhaustive search fixture",600,500,0,0,0,reserve=0,closing_allowance=0,
                 heating=0,condo_fee=0,home_insurance=0,maintenance_monthly=0)

@pytest.mark.parametrize("insured,uninsured",[(1,15),(4,5),(8,2)])
def test_price_limit_matches_every_whole_dollar_in_a_small_complete_domain(insured,uninsured):
    buyer=small_buyer()
    args=(buyer,"NS",.003,insured,uninsured)
    feasible=[p for p in range(1,10001) if (lambda r:r["cash_pass"] and r["income_pass"])(evaluate(p,*args))]
    result=maximum_price(*args)
    assert result==max(feasible)
    if (insured,uninsured)==(1,15):
        # A cheaper insured rate creates a disconnected feasible set.
        # A global monotonic bisection can miss the later feasible interval.
        assert any(b-a>1 for a,b in zip(feasible[:-1],feasible[1:]))

@pytest.mark.parametrize("insured,uninsured",[(1,15),(4,5),(8,2)])
def test_minimum_cash_matches_every_whole_dollar_in_small_domain(insured,uninsured):
    buyer=small_buyer();price=3000
    feasible=[]
    for cash in range(195,3046):
        r=evaluate(price,replace(buyer,liquid_cash=cash),"NS",.003,insured,uninsured)
        if r["cash_pass"] and r["income_pass"]:feasible.append(cash)
    assert minimum_cash_for_income(price,buyer,"NS",.003,insured,uninsured)==min(feasible)

def test_no_price_when_funds_do_not_cover_fixed_costs():
    assert maximum_price(replace(PROFILES[0],liquid_cash=13000),"BC",.003,4,4) is None

def test_cash_and_income_positions_explain_a_zero_shortfall():
    cases=pd.read_csv(OUT/"homebuying_cases.csv")
    g=cases[cases.city.eq("Vancouver")&cases.profile.eq("couple")&cases.year.eq(2023)].set_index("scenario")
    assert g.loc["baseline","cash_gap"]==0
    assert g.loc["cash25","cash_gap"]==0
    assert g.loc["baseline","cash_position"]==14640
    assert g.loc["cash25","cash_position"]==39640
    assert g.loc["price20","income_position"]==pytest.approx(2629.9862140467)
    assert g.loc["cash25","mortgage_principal"]<g.loc["baseline","mortgage_principal"]
    assert g.loc["baseline","cash_position_label"]=="CAD 14,640 above"
    assert g.loc["price20","income_position_label"]=="CAD 2,630 above"

def test_small_nonzero_values_do_not_display_as_zero():
    assert money(.5)=="CAD 0.50"
    assert position(-.1,"minimum")=="CAD 0.10 short"
    assert position(0,"minimum")=="Meets minimum"

def test_every_saved_baseline_threshold_and_rounded_display():
    limits=pd.read_csv(OUT/"homebuying_price_limits.csv")
    rates=annual_rates().pivot(index="year",columns="kind",values="rate")
    profiles={p.id:p for p in PROFILES}
    for r in limits.itertuples():
        buyer=profiles[r.profile];city=CITIES[r.city]
        args=(buyer,city["province"],city["tax_rate"],rates.loc[r.year,"insured"],rates.loc[r.year,"uninsured"])
        fits=evaluate(r.maximum_price,*args)
        beyond=evaluate(r.maximum_price+1,*args)
        assert fits["cash_pass"] and fits["income_pass"]
        assert not (beyond["cash_pass"] and beyond["income_pass"])
        previous=evaluate(r.benchmark_price,replace(buyer,liquid_cash=r.total_cash_to_fit_at_benchmark-1),*args[1:])
        enough=evaluate(r.benchmark_price,replace(buyer,liquid_cash=r.total_cash_to_fit_at_benchmark),*args[1:])
        assert enough["cash_pass"] and enough["income_pass"]
        assert not (previous["cash_pass"] and previous["income_pass"])
        assert r.maximum_price_display<=r.maximum_price
        displayed=evaluate(r.maximum_price_display,*args)
        assert displayed["cash_pass"] and displayed["income_pass"]
        assert r.additional_cash_display>=r.additional_cash_to_fit

def test_extended_sql_reconciliation_covers_positions_loans_and_monthly_costs():
    with sqlite3.connect(OUT/"homebuying.sqlite") as db:
        frame=pd.read_sql_query("SELECT * FROM case_reconciliation",db)
    columns=[c for c in frame if c.endswith("_delta")]
    assert len(columns)==8 and len(frame)==468
    assert frame[columns].abs().to_numpy().max()<1e-7

def test_programs_display_the_measure_they_change():
    programs=pd.read_csv(OUT/"homebuying_programs.csv")
    thirty=programs[programs.program.eq("30-year amortization")]
    assert thirty.metric_1_label.eq("Monthly mortgage payment").all()
    assert (thirty.metric_1_after<thirty.metric_1_before).all()
    hbp=programs[programs.program.eq("HBP existing RRSP")]
    assert np.allclose(hbp.metric_1_after-hbp.metric_1_before,hbp.hbp_draw)
    halifax_bc=programs[programs.city.eq("Halifax")&programs.program.eq("BC transfer relief")]
    assert not halifax_bc.applicable.any()
    assert halifax_bc.cash_explanation.str.startswith("Not applicable").all()

def test_independent_amortization_and_budget_review_passes():
    review=pd.read_csv(OUT/"homebuying_review_checks.csv")
    assert len(review)>=13 and review.status.eq("Pass").all()
    assert review.check.str.contains("Independent 60-month").sum()==2
    assert (review.max_absolute_error<=review.tolerance).all()
