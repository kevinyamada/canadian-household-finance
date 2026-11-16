from pathlib import Path
import json,sqlite3,sys
import numpy as np
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from housing_audit import annualize_renter_estimates, minimum_down_payment, purchase_cash_cases


@pytest.mark.parametrize("price,expected",[(400000,20000),(500000,25000),(500001,25000.1),(600000,35000),(1499999,124999.9),(1500000,300000),(2000000,400000)])
def test_down_payment_tiers_and_insurance_limit_boundary(price,expected):
    assert minimum_down_payment(price)==pytest.approx(expected)


@pytest.mark.parametrize("price",[0,-1,float("nan"),float("inf")])
def test_invalid_purchase_prices_are_rejected(price):
    with pytest.raises(ValueError):minimum_down_payment(price)


def test_annual_renter_total_uses_four_observations_not_latest_quarter_times_four():
    history=pd.read_csv(ROOT/"data/processed/segment_history.csv")
    quarters,annual=annualize_renter_estimates(history)
    latest=quarters.iloc[-1]
    row=annual[annual.year==int(latest.year)].iloc[0]
    assert row.saving==quarters[quarters.year==int(latest.year)].saving.sum()
    assert row.saving==-557
    assert latest.saving==269
    assert row.saving!=4*latest.saving
    np.testing.assert_allclose(annual.income+annual.pension-annual.consumption-annual.saving,annual.rounding_residual)


def test_incomplete_year_and_duplicate_quarter_block_the_annual_audit():
    history=pd.read_csv(ROOT/"data/processed/segment_history.csv")
    quarters=history[history.group=="Renter"]
    with pytest.raises(ValueError,match="four observed quarters"):
        annualize_renter_estimates(quarters.iloc[1:].copy())
    with pytest.raises(ValueError,match="unique"):
        annualize_renter_estimates(pd.concat([quarters,quarters.iloc[[0]]]))


def test_accounting_break_blocks_the_audit():
    history=pd.read_csv(ROOT/"data/processed/segment_history.csv")
    index=history.index[history.group=="Renter"][0]
    history.loc[index,"saving"]+=100
    with pytest.raises(ValueError,match="identity"):
        annualize_renter_estimates(history)


def test_cash_check_separates_rule_minimum_from_assumed_closing_costs():
    cases=purchase_cash_cases()
    example=cases[(cases.home_price==600000)&(cases.closing_allowance_pct==2.5)].iloc[0]
    assert example.minimum_down_payment==35000
    assert example.closing_allowance==15000
    assert example.upfront_cash_scenario==50000
    np.testing.assert_allclose(cases.upfront_cash_scenario,cases.minimum_down_payment+cases.closing_allowance)
    assert cases.price_basis.str.startswith("Illustrative").all()


def test_sql_and_python_annual_audit_agree_and_no_borrower_cash_is_invented():
    annual=pd.read_csv(ROOT/"data/processed/renter_annual_saving.csv")
    with sqlite3.connect(ROOT/"data/processed/finance.sqlite") as c:
        sql=pd.read_sql_query("SELECT * FROM renter_annual_audit ORDER BY year",c)
    np.testing.assert_allclose(sql.reported_net_saving,annual.saving)
    np.testing.assert_allclose(sql.income_less_consumption,annual.income_less_consumption)
    summary=json.loads((ROOT/"data/processed/housing_audit_summary.json").read_text())
    assert summary["liquid_funds_observed"] is False
    assert summary["customer_eligibility_estimated"] is False
    claims=pd.read_csv(ROOT/"data/processed/housing_claim_register.csv").set_index("claim_id")
    assert claims.loc["C3","verdict"]=="Unsupported"
    assert claims.loc["C5","verdict"]=="Incorrect"
    assert claims.loc["C7","verdict"]=="Supported"
    assert "deliberately drafted" in summary["claim_register_scope"]
