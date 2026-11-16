"""Audit what public renter saving figures can support about buying a home."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import sqlite3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
QUESTION = "Why does buying a home still feel out of reach?"
RULE_DATE = "2026-11-16"


def minimum_down_payment(price):
    price = float(price)
    if not math.isfinite(price) or price <= 0:
        raise ValueError("Purchase price must be finite and positive")
    if price >= 1_500_000:
        return .20 * price
    return .05 * min(price, 500_000) + .10 * max(price - 500_000, 0)


def annualize_renter_estimates(history):
    frame = history[history.group.eq("Renter")].copy()
    required = ["income", "consumption", "pension", "saving"]
    if frame.empty or frame[required].isna().any().any():
        raise ValueError("Complete renter accounting measures are required")
    if frame.quarter.duplicated().any():
        raise ValueError("Renter quarters must be unique")
    periods = pd.PeriodIndex(frame.quarter, freq="Q")
    frame["year"] = periods.year
    if not frame.groupby("year").size().eq(4).all():
        raise ValueError("An annual comparison needs four observed quarters per year")
    residual = frame.income + frame.pension - frame.consumption - frame.saving
    if residual.abs().max() > 2:
        raise ValueError("Quarterly saving identity failed its CAD 2 rounding allowance")
    annual = frame.groupby("year", as_index=False)[required].sum()
    annual["quarter_count"] = 4
    annual["income_less_consumption"] = annual.income - annual.consumption
    annual["rounding_residual"] = annual.income + annual.pension - annual.consumption - annual.saving
    return frame.sort_values("quarter"), annual


def purchase_cash_cases():
    rows = []
    for price in [300000, 400000, 500000, 600000, 800000, 1000000, 1250000, 1499999, 1500000, 2000000]:
        for allowance in [1.5, 2.5, 4.0]:
            down = minimum_down_payment(price)
            cost = price * allowance / 100
            rows.append({
                "home_price": price, "home_price_label": f"CAD {price:,.0f}",
                "closing_allowance_pct": allowance, "closing_allowance_label": f"{allowance:g}%", "minimum_down_payment": down,
                "closing_allowance": cost, "upfront_cash_scenario": down + cost,
                "rule_date": RULE_DATE, "price_basis": "Illustrative purchase price, not an observed market price",
                "scope": "Upfront cash only; not mortgage qualification or a complete purchase budget"
            })
    return pd.DataFrame(rows)


def generate(root=ROOT):
    out = root / "data/processed"
    history = pd.read_csv(out / "segment_history.csv")
    quarters, annual = annualize_renter_estimates(history)
    latest, year = quarters.iloc[-1], annual.iloc[-1]
    cases = purchase_cash_cases()
    sample = cases[(cases.home_price == 600000) & (cases.closing_allowance_pct == 2.5)].iloc[0]
    raw = root / "data/raw/housing/boc_affordability_2020_2025.json"
    raw_manifest = json.loads((raw.parent / "manifest.json").read_text())
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == raw_manifest["sha256"]
    payload = json.loads(raw.read_text(encoding="utf-8-sig"))
    context = pd.DataFrame([
        {"quarter": str(pd.Period(row["d"], freq="Q")), "affordability_index": float(row["INDINF_AFFORD_Q"]["v"])}
        for row in payload["observations"] if "INDINF_AFFORD_Q" in row
    ])
    assert set(context.quarter) == set(quarters.quarter), "Keep the affordability context on matched dates"
    rules = json.loads((root / "data/raw/housing/purchase_rules.json").read_text())
    assert rules["as_of"] == RULE_DATE
    latest_context = context[context.quarter == latest.quarter].iloc[0]
    controls = pd.DataFrame([
        {"control":"Unique renter quarters","status":"Pass","evidence":f"{len(quarters)} distinct quarters"},
        {"control":"Complete calendar years","status":"Pass","evidence":f"{len(annual)} years, four observed quarters each"},
        {"control":"Saving identity","status":"Pass","evidence":"Income + pension change - consumption = net saving, within published rounding"},
        {"control":"Annual totals from all quarters","status":"Pass","evidence":"Do not multiply the final quarter by four"},
        {"control":"Household and money units","status":"Pass","evidence":"Per-household nominal CAD; not seasonally adjusted"},
        {"control":"Verified deposit cash","status":"Needs evidence","evidence":"Not observed in these public group averages"},
        {"control":"Mortgage qualification inputs","status":"Needs evidence","evidence":"Gross borrower income, debts, credit, property and loan terms are not observed"}
    ])
    claims = pd.DataFrame([
        {"claim_id":"C1","draft_claim":f"Renters added CAD {latest.saving:,.0f} to down-payment cash in {latest.quarter}.","verdict":"Unsupported","reason":"Reported net saving includes pension entitlements and is not verified cash accumulation.","evidence_ref":"Renter quarterly accounting identity"},
        {"claim_id":"C2","draft_claim":"Annual saving equals four times the final quarter's saving.","verdict":"Incorrect" if abs(4*latest.saving-year.saving)>8 else "Needs context","reason":"Use the four actual quarterly observations; the source is not seasonally adjusted.","evidence_ref":f"Renter annual total {int(year.year)}"},
        {"claim_id":"C3","draft_claim":"Every Canadian renter is unable to buy a home.","verdict":"Unsupported","reason":"A group average cannot identify individual resources, gifts, existing assets or loan eligibility.","evidence_ref":"Population and liquidity limits"},
        {"claim_id":"C4","draft_claim":"Average renter net worth is money available for a deposit.","verdict":"Unsupported","reason":"Net worth is a stock including assets with different liquidity; it is not verified available funds.","evidence_ref":"StatCan wealth definitions"},
        {"claim_id":"C5","draft_claim":"A CAD 600,000 home requires only CAD 30,000 minimum down.","verdict":"Incorrect","reason":"The rule applies 5% to the first CAD 500,000 and 10% to the balance: CAD 35,000.","evidence_ref":f"Purchase rules as of {RULE_DATE}"},
        {"claim_id":"C6","draft_claim":"An improving national housing affordability index proves renters have a deposit.","verdict":"Unsupported","reason":"The index models representative housing costs relative to income; it does not observe a renter's liquid funds.","evidence_ref":"Bank of Canada index definition"},
        {"claim_id":"C7","draft_claim":"Minimum down payment for a CAD 600,000 purchase is CAD 35,000.","verdict":"Supported","reason":"Matches the current price-tier calculation. Closing costs and loan qualification remain separate.","evidence_ref":f"Purchase rules as of {RULE_DATE}"},
        {"claim_id":"C8","draft_claim":"Reported net saving includes the pension-entitlement adjustment.","verdict":"Supported","reason":"The quarterly accounting components reconcile within published rounding.","evidence_ref":"StatCan saving definition"}
    ])
    summary = {
        "question": QUESTION,
        "audit_scope": "Audit whether public renter saving figures support a homebuying-readiness claim.",
        "verdict": "Reported saving does not establish money available for a down payment.",
        "latest_quarter": latest.quarter, "latest_year": int(year.year),
        "annual_income": float(year.income), "annual_consumption": float(year.consumption),
        "annual_income_less_consumption": float(year.income_less_consumption),
        "annual_pension": float(year.pension), "annual_net_saving": float(year.saving),
        "quarterly_income": float(latest.income), "quarterly_consumption": float(latest.consumption),
        "quarterly_income_less_consumption": float(latest.income-latest.consumption),
        "quarterly_pension": float(latest.pension), "quarterly_net_saving": float(latest.saving),
        "annual_years": len(annual), "observed_quarters": len(quarters),
        "illustrative_home_price": int(sample.home_price), "minimum_down_payment": float(sample.minimum_down_payment),
        "closing_allowance_pct": float(sample.closing_allowance_pct), "closing_allowance": float(sample.closing_allowance),
        "upfront_cash_scenario": float(sample.upfront_cash_scenario),
        "affordability_context_quarter": latest_context.quarter,
        "national_affordability_index": float(latest_context.affordability_index),
        "rule_date": RULE_DATE,
        "recommendation": "Verify liquid funds and the purchase budget before making a readiness claim. Do not turn group net saving into a personal buying date.",
        "liquid_funds_observed": False, "customer_eligibility_estimated": False,
        "claim_register_scope": "Eight deliberately drafted claims for an audit demonstration; not errors alleged in published reports.",
        "limitations": [
            "These are averages over changing household groups, not a panel of individual renters.",
            "Consumption contains national-accounts imputations; income less consumption is not bank-account cash flow.",
            "Annual values sum the four published quarterly per-household estimates; minor rounding differences are retained.",
            "Home prices and closing-cost allowances in the cash check are explicit scenarios.",
            "The cash check does not include mortgage approval, all taxes, loan insurance or a complete legal closing statement."
        ]
    }
    if year.saving < 0:
        summary["annual_result"] = f"The sum of reported renter net saving in {int(year.year)} was negative CAD {abs(year.saving):,.0f} per household."
    else:
        summary["annual_result"] = f"The sum of reported renter net saving in {int(year.year)} was CAD {year.saving:,.0f} per household; the measure still does not verify deposit cash."
    annual.to_csv(out/"renter_annual_saving.csv",index=False)
    quarters[["quarter","year","income","consumption","pension","saving","income_less_consumption"]].to_csv(out/"renter_quarterly_saving.csv",index=False)
    cases.to_csv(out/"home_purchase_cash_cases.csv",index=False)
    claims.to_csv(out/"housing_claim_register.csv",index=False)
    controls.to_csv(out/"housing_audit_checks.csv",index=False)
    context.to_csv(out/"housing_affordability_context.csv",index=False)
    (out/"housing_audit_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    with sqlite3.connect(out/"finance.sqlite") as connection:
        connection.executescript((root/"sql/housing_audit.sql").read_text())
        comparison=pd.read_sql_query("SELECT * FROM renter_annual_audit ORDER BY year",connection)
        np.testing.assert_allclose(comparison.reported_net_saving, annual.saving, rtol=0, atol=1e-9)
        np.testing.assert_allclose(comparison.income_less_consumption, annual.income_less_consumption, rtol=0, atol=1e-9)
        cases.to_sql("home_purchase_cash_cases",connection,if_exists="replace",index=False)
        claims.to_sql("housing_claim_register",connection,if_exists="replace",index=False)
    lines = [
        "# Housing-readiness audit", "", "**"+QUESTION+"**", "",
        "## Audit conclusion", "", summary["verdict"], "", summary["annual_result"], "",
        f"In {latest.quarter}, reported renter net saving was CAD {latest.saving:,.0f}, made up of income less consumption of CAD {latest.income-latest.consumption:,.0f} plus a pension adjustment of CAD {latest.pension:,.0f}. A positive quarter does not establish cash available for a home purchase.", "",
        "## What a purchase would need", "",
        f"For an illustrative CAD 600,000 home, the current minimum down payment is CAD {sample.minimum_down_payment:,.0f}. A separately assumed 2.5% closing-cost allowance adds CAD {sample.closing_allowance:,.0f}, for an upfront cash scenario of CAD {sample.upfront_cash_scenario:,.0f}. This is not an observed national home price, complete closing statement or mortgage approval.", "",
        "## The audit action", "", summary["recommendation"], "",
        "The claim register contains deliberately drafted examples. Unsupported interpretations are sent for evidence or correction; no fraud or misstatement by Statistics Canada is alleged.", "",
        "## Limits", "", *["- "+item for item in summary["limitations"]], "",
        "[Claim register](../data/processed/housing_claim_register.csv) · [Purchase scenarios](../data/processed/home_purchase_cash_cases.csv) · [Sources and method](../docs/methodology.md)", ""
    ]
    (root/"reports/housing_audit.md").write_text("\n".join(lines),encoding="utf-8")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(10.5,4.8))
    fig.patch.set_facecolor("#FAFBF8");ax.set_facecolor("#FAFBF8")
    ax.bar(annual.year.astype(str),annual.saving,color=["#34614F" if value>=0 else "#9D5C42" for value in annual.saving])
    ax.axhline(0,color="#65746A",lw=.8)
    ax.set_title("Renter net saving: the full year matters",loc="left",fontsize=18,pad=22,color="#173D36")
    ax.set_ylabel("Sum of quarterly net saving, CAD per household")
    for spine in ["top","right"]:ax.spines[spine].set_visible(False)
    fig.text(.02,.02,"2020–2025 | Public group averages | Includes pension adjustments; not verified down-payment cash",fontsize=10,color="#54635E")
    fig.tight_layout(rect=[0,.06,1,1])
    fig.savefig(root/"reports/figures/19_housing_audit.png",dpi=160,facecolor=fig.get_facecolor())
    plt.close(fig)
    print(json.dumps(summary,indent=2),flush=True)
    return summary


if __name__ == "__main__":
    generate()
