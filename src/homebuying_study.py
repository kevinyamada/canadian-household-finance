"""Compare deposit and income constraints with official data and explicit buyer cases."""
from dataclasses import asdict, replace
from pathlib import Path
from itertools import permutations
import argparse
import gzip
import hashlib
import json
import math
import sqlite3
import numpy as np
import pandas as pd
from pyproj import Transformer

from homebuying_data import ROOT, RAW, CITIES, RATE_SERIES, RULE_SOURCES, observed_data, annual_rates, verify_manifest, write_json
from homebuying_model import Buyer, PROFILES, evaluate, waiting_cash, RULE_DATE
from homebuying_review import explain_cases, explain_programs, price_limits, independent_review, write_review_report

OUT = ROOT / "data/processed"
ASSETS = ROOT / "docs/assets"
PROFILE_ASSETS = {
    "single": {"existing_rrsp_outside_liquid_cash": 20000, "eligible_participants": 1},
    "couple": {"existing_rrsp_outside_liquid_cash": 40000, "eligible_participants": 2},
    "deposit": {"existing_rrsp_outside_liquid_cash": 30000, "eligible_participants": 1},
}
SCENARIOS = [
    ("baseline", "Baseline"),
    ("price10", "Price 10% lower"),
    ("price20", "Price 20% lower"),
    ("rate1", "Mortgage rate 1 point lower"),
    ("cash25", "CAD 25,000 more cash"),
    ("income20", "Gross income 20% higher"),
    ("amort30", "30-year amortization"),
    ("no_relief", "No BC first-time tax relief"),
    ("no_reserve", "No emergency reserve"),
    ("assess75", "Assessment is 75% of price"),
    ("assess125", "Assessment is 125% of price"),
    ("costs_high", "Higher heat and condo fees"),
    ("hbp", "HBP: draw existing RRSP funds"),
]
COLORS = {"Cash": "#b66b38", "Income": "#396fa1", "Both cash and income": "#a34f41", "Within modeled limits": "#286c5a"}

def records(frame):
    return json.loads(frame.to_json(orient="records", double_precision=12))

def save_csv(path, frame):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frame.to_csv(index=False, lineterminator="\n"), encoding="utf-8", newline="\n")

def case_for(city, price, buyer, insured, uninsured, scenario="baseline"):
    spec = CITIES[city]
    years, assessment, relief, all_cash = 25, 1.0, True, True
    if scenario == "price10":
        price *= .90
    elif scenario == "price20":
        price *= .80
    elif scenario == "rate1":
        insured, uninsured = max(0, insured - 1), max(0, uninsured - 1)
    elif scenario == "cash25":
        buyer = replace(buyer, liquid_cash=buyer.liquid_cash + 25000)
    elif scenario == "income20":
        buyer = replace(buyer, gross_income=buyer.gross_income * 1.20)
    elif scenario == "amort30":
        years = 30
    elif scenario == "no_relief":
        relief = False
    elif scenario == "no_reserve":
        buyer = replace(buyer, reserve=0)
    elif scenario == "assess75":
        assessment = .75
    elif scenario == "assess125":
        assessment = 1.25
    elif scenario == "costs_high":
        buyer = replace(buyer, heating=buyer.heating + 100, condo_fee=buyer.condo_fee + 250)
    elif scenario == "hbp":
        asset = PROFILE_ASSETS[buyer.id]
        withdrawal = min(asset["existing_rrsp_outside_liquid_cash"], 60000 * asset["eligible_participants"])
        buyer = replace(buyer, liquid_cash=buyer.liquid_cash + withdrawal)
    elif scenario != "baseline":
        raise ValueError("Unknown scenario")
    result = evaluate(price, buyer, spec["province"], spec["tax_rate"], insured, uninsured,
                      years=years, assessment_ratio=assessment, relief=relief, use_all_cash=all_cash)
    result.update(city=city, csd=spec["csd"], profile=buyer.id, profile_label=buyer.name,
                  scenario=scenario, scenario_label=dict(SCENARIOS)[scenario],
                  tax_basis=spec["tax_basis"], color=COLORS[result["barrier"]])
    return result

def projected_markers(map_data):
    geometry = json.loads(gzip.decompress((ROOT / "data/raw/site_visuals/provinces_2021_3347.json.gz").read_bytes()))
    all_points = np.vstack([np.asarray(r, dtype=float)[:, :2] for f in geometry["features"] for r in f["geometry"]["rings"]])
    lo, hi = all_points.min(axis=0), all_points.max(axis=0)
    width, height, pad = map_data["width"], map_data["height"], 16
    scale = min((width - 2*pad)/(hi[0]-lo[0]), (height - 2*pad)/(hi[1]-lo[1]))
    offset = np.array([(width-(hi[0]-lo[0])*scale)/2, (height-(hi[1]-lo[1])*scale)/2])
    transform = Transformer.from_crs("EPSG:4326", "EPSG:3347", always_xy=True)
    points = []
    for city, spec in CITIES.items():
        body = json.loads((RAW / ("geoname_"+city+".json")).read_text())
        province = "59" if spec["province"] == "BC" else "12"
        item = next(i for i in body["items"] if i["name"] == city and i["province"]["code"] == province and i["status"]["code"] == "official")
        x, y = transform.transform(item["longitude"], item["latitude"])
        x, y = (x-lo[0])*scale+offset[0], (hi[1]-y)*scale+offset[1]
        points.append({"city": city, "x": round(float(x), 2), "y": round(float(y), 2),
                       "longitude": item["longitude"], "latitude": item["latitude"], "official_id": item["id"]})
    return points

def decomposition(city, observed, rates):
    old = observed[(observed.city == city) & (observed.year == 2021)].iloc[0]
    new = observed[(observed.city == city) & (observed.year == 2023)].iloc[0]
    reference = Buyer("reference", "Minimum-down comparison", 100000, 0, 0, 0, 0)
    start = {"price": old.buyer_median_sale_price, "rates": rates.loc[2021], "income": old.buyer_family_median_income}
    end = {"price": new.buyer_median_sale_price, "rates": rates.loc[2023], "income": new.buyer_family_median_income}
    def value(inputs):
        row = case_for(city, inputs["price"], reference, inputs["rates"]["insured"], inputs["rates"]["uninsured"])
        return row["required_gross_income"] - inputs["income"]
    contributions = {key: 0 for key in start}
    for order in permutations(start):
        current = dict(start)
        before = value(current)
        for key in order:
            current[key] = end[key]
            after = value(current)
            contributions[key] += (after-before)/6
            before = after
    first, last = value(start), value(end)
    if abs(first + sum(contributions.values()) - last) > 1e-7:
        raise ValueError("Historical decomposition did not reconcile")
    return [{"city": city, "factor": key, "contribution_cad": value_, "start_gap_cad": first, "end_gap_cad": last,
             "scope": "Descriptive 2021–2023 comparison to buyer-family income; current rules and tax schedule held fixed; not causal or borrower eligibility"}
            for key, value_ in contributions.items()]

def generate():
    verify_manifest()
    long, observed, bridge = observed_data()
    annual = annual_rates()
    rate_lookup = annual.pivot(index="year", columns="kind", values="rate")
    latest_year = int(observed[observed.table.eq("46100099")].year.max())
    all_cases, history, waiting, programs = [], [], [], []
    for item in observed.itertuples():
        year, city, price = int(item.year), item.city, float(item.buyer_median_sale_price)
        insured, uninsured = rate_lookup.loc[year, ["insured", "uninsured"]]
        reference = Buyer("reference", "Minimum-down comparison", 100000, 0, 0, 0, 0)
        historical = case_for(city, price, reference, insured, uninsured)
        history.append({**historical, "year": year, "table": item.table, "geography_vintage": int(item.geography_vintage),
                        "buyer_family_median_income": float(item.buyer_family_median_income),
                        "published_price_income_ratio": float(item.published_median_price_income_ratio),
                        "observed_buyer_count": float(item.first_time_buyers)})
        for buyer in PROFILES:
            for scenario, label in SCENARIOS:
                row = case_for(city, price, buyer, insured, uninsured, scenario)
                row.update(year=year, case_id=f"{city}|{buyer.id}|{year}|{scenario}", price_source_table=item.table,
                           geography_vintage=int(item.geography_vintage), assumed_buyer=True)
                # Bar coordinates are prepared here; the browser only displays saved values.
                for metric, available, needed in [("cash", row["profile_cash"], row["cash_target"]), ("income", row["profile_income"], row["required_gross_income"])]:
                    maximum = max(available, needed, 1)
                    row[metric+"_available_pct"] = available/maximum*100
                    row[metric+"_needed_pct"] = needed/maximum*100
                all_cases.append(row)
            if year != latest_year:
                continue
            base = case_for(city, price, buyer, insured, uninsured)
            no_relief = case_for(city, price, buyer, insured, uninsured, "no_relief")
            thirty = case_for(city, price, buyer, insured, uninsured, "amort30")
            hbp = case_for(city, price, buyer, insured, uninsured, "hbp")
            asset = PROFILE_ASSETS[buyer.id]
            hbp_draw = min(asset["existing_rrsp_outside_liquid_cash"], 60000*asset["eligible_participants"])
            future_buyer = replace(buyer, liquid_cash=waiting_cash(buyer, 12, 0))
            future = case_for(city, price, future_buyer, insured, uninsured)
            contribution = min(8000*asset["eligible_participants"], 12*buyer.monthly_saving)
            refund = contribution*.30
            fhsa = case_for(city, price, replace(future_buyer, liquid_cash=future_buyer.liquid_cash+refund), insured, uninsured)
            for program, before, after, note in [
                ("BC transfer relief", no_relief, base, "Conditional on BC eligibility; not available for Halifax. Residual price-specific transfer tax remains."),
                ("30-year amortization", base, thirty, "First-time resale buyer assumed; insured premium includes the 0.20 percentage-point surcharge. Interest compares the first five years."),
                ("HBP existing RRSP", base, hbp, f"Draw CAD {hbp_draw:,.0f} from separately stated existing RRSP funds. No increase in total assets; future repayments required."),
                ("FHSA one-year illustration", future, fhsa, "Compare after 12 months of identical saving, flat price/rent and a 30% assumed marginal tax rate. Contribution is funded from that saving, counted once; only the refund adds cash. Refund timing and eligibility are assumed."),
            ]:
                programs.append({"city": city, "profile": buyer.id, "profile_label": buyer.name, "program": program,
                    "cash_target_before": before["cash_target"], "cash_target_after": after["cash_target"],
                    "liquid_cash_before": before["profile_cash"], "liquid_cash_after": after["profile_cash"],
                    "cash_gap_before": before["cash_gap"], "cash_gap_after": after["cash_gap"],
                    "transfer_tax_before": before["transfer_tax"], "transfer_tax_after": after["transfer_tax"],
                    "loan_before": before["mortgage_principal"], "loan_after": after["mortgage_principal"],
                    "required_income_before": before["required_gross_income"], "required_income_after": after["required_gross_income"],
                    "monthly_payment_before": before["monthly_mortgage"], "monthly_payment_after": after["monthly_mortgage"],
                    "five_year_interest_before": before["first_five_years_interest"], "five_year_interest_after": after["first_five_years_interest"],
                    "barrier_before": before["barrier"], "barrier_after": after["barrier"], "note": note,
                    "fhsa_contribution": contribution if program.startswith("FHSA") else 0,
                    "assumed_marginal_tax_rate": .30 if program.startswith("FHSA") else 0,
                    "hbp_draw": hbp_draw if program.startswith("HBP") else 0,
                    "hbp_future_annual_repayment": hbp_draw/15 if program.startswith("HBP") else 0})
            for months in [12, 24]:
                for price_growth in [-.05, 0, .05]:
                    for rent_growth in [0, .03, .06]:
                        future_cash = waiting_cash(buyer, months, rent_growth)
                        future_price = price*(1+price_growth)**(months/12)
                        row = case_for(city, future_price, replace(buyer, liquid_cash=future_cash), insured, uninsured)
                        waiting.append({**row, "months": months, "annual_price_growth": price_growth, "annual_rent_growth": rent_growth,
                                        "saving_added": future_cash-buyer.liquid_cash,
                                        "scope": "Illustrative wait from the 2023 benchmark; fixed income/rates, zero saving interest, rent increases reduce assumed net saving. Not a forecast."})
    cases = explain_cases(pd.DataFrame(all_cases))
    history = pd.DataFrame(history)
    waiting = pd.DataFrame(waiting)
    programs = explain_programs(pd.DataFrame(programs))
    contributions = pd.DataFrame([r for city in CITIES for r in decomposition(city, observed, rate_lookup)])
    baseline = cases[cases.year.eq(latest_year) & cases.scenario.eq("baseline")].copy()
    limits = price_limits(baseline, rate_lookup)
    review = independent_review(cases, programs, waiting, limits)
    write_review_report(cases, programs, waiting, limits, review, ROOT/"reports/calculation_review.md")
    # Later observed rates, held against the same 2023 prices and profile income: a scenario, not 2025 observed affordability.
    rate_replay = []
    for city in CITIES:
        price = observed.loc[observed.city.eq(city) & observed.year.eq(latest_year), "buyer_median_sale_price"].item()
        for buyer in PROFILES:
            row = case_for(city, price, buyer, rate_lookup.loc[2025,"insured"], rate_lookup.loc[2025,"uninsured"])
            base = baseline[baseline.city.eq(city) & baseline.profile.eq(buyer.id)].iloc[0]
            row.update(price_year=latest_year, rate_year=2025, required_income_2023_rates=float(base.required_gross_income),
                       income_reduction=float(base.required_gross_income)-row["required_gross_income"],
                       scope="2025 observed national rates applied to fixed 2023 transaction prices and unchanged profile income/cash; not observed 2025 affordability.")
            rate_replay.append(row)
    rate_replay = pd.DataFrame(rate_replay)
    if len(baseline) != 9 or cases.case_id.duplicated().any():
        raise ValueError("Expected nine unique baseline cases")
    controls = [
        {"control": "Published FCAC example discrepancy", "status": "Exception explained", "detail": "At 4%, the monthly cell says 1587.06 while its total interest and the standard formula imply 1578.06. Eight other monthly examples and the 5-year interest example are independently checked."},
        {"control": "Official source policy and hashes", "status": "Pass", "detail": "Selected WDS responses, metadata, Bank of Canada rates and government tax sources verified"},
        {"control": "Unique market/year and case keys", "status": "Pass", "detail": "No joins across CMA and city geography; three selected CSDs"},
        {"control": "Twelve monthly rate observations", "status": "Pass", "detail": "Funds-advanced fixed 5-years-and-over rates; outstanding-balance rates rejected"},
        {"control": "Source vintages", "status": "Scope note", "detail": "2020 is SGC 2016; 2021–2023 uses SGC 2021. Overlap retained separately; no causal claims"},
        {"control": "Property assessment and tax bill", "status": "Needs evidence", "detail": "Price used as explicit assessment proxy; Halifax urban-rate scenario; actual property bill and local charges required"},
        {"control": "Closing and ongoing cost estimates", "status": "Needs evidence", "detail": "CAD 4,000 closing allowance, CAD 10,000 reserve and monthly heat/fees/insurance/maintenance are assumptions"},
        {"control": "Borrower and program eligibility", "status": "Needs evidence", "detail": "Income, liquid cash, RRSP balances, credit, residency, ownership history and property conditions not verified"},
        {"control": "Waiting and program scenarios", "status": "Scope note", "detail": "No forecast probabilities; FHSA tax rate/timing assumed; HBP moves existing assets"},
        {"control": "Historical policy comparison", "status": "Scope note", "detail": "2026 rules and 2023 tax schedule held constant; not historical mortgage approvals"},
    ]
    summary = {
        "question": "Is the down payment really the biggest obstacle to buying a home?",
        "headline": "Why does buying a home still feel out of reach?",
        "price_year": latest_year, "rule_date": RULE_DATE, "cities": list(CITIES),
        "profiles": [{**asdict(p), **PROFILE_ASSETS[p.id]} for p in PROFILES],
        "observed_scope": "Resident first-time property buyers; city/CSD transaction benchmarks, not all renters or identical properties",
        "case_count": len(cases), "baseline_cases": len(baseline),
        "barriers": {str(k): int(v) for k, v in baseline.barrier.value_counts().items()},
        "cash_ready_but_income_short": int((baseline.cash_pass & ~baseline.income_pass).sum()),
        "modeled_pass_cases": int((baseline.cash_pass & baseline.income_pass).sum()),
        "scope": "Nine illustrations are not population estimates, mortgage approvals or a personal buying-date recommendation.",
        "source_tables": ["46-10-0099-01", "46-10-0062-01"],
        "rate_series": RATE_SERIES, "history_years": [2020, 2021, 2022, 2023],
        "policy_comparison_years": [2021, 2023],
        "waiting_cases": len(waiting), "program_cases": len(programs), "price_limit_cases": len(limits), "review_checks": len(review),
        "source_policy": "Statistics Canada first; official Canadian public bodies only",
        "execution": "Prepared and checked with Python and SQL in Kevin's local desktop VS Code integrated terminal",
    }
    for name, frame in [("homebuying_observed.csv", observed), ("homebuying_observed_long.csv", long),
                         ("homebuying_source_bridge.csv", bridge), ("homebuying_rates.csv", annual),
                         ("homebuying_cases.csv", cases), ("homebuying_history.csv", history), ("homebuying_rate_replay.csv", rate_replay),
                         ("homebuying_waiting.csv", waiting), ("homebuying_programs.csv", programs),
                         ("homebuying_price_limits.csv", limits), ("homebuying_review_checks.csv", review),
                         ("homebuying_decomposition.csv", contributions), ("homebuying_controls.csv", pd.DataFrame(controls))]:
        save_csv(OUT/name, frame)
    write_json(OUT/"homebuying_summary.json", summary)
    with sqlite3.connect(OUT/"homebuying.sqlite") as connection:
        cases.to_sql("purchase_cases", connection, if_exists="replace", index=False)
        history.to_sql("market_history", connection, if_exists="replace", index=False)
        programs.to_sql("program_comparisons", connection, if_exists="replace", index=False)
        waiting.to_sql("waiting_cases", connection, if_exists="replace", index=False)
        limits.to_sql("price_limits", connection, if_exists="replace", index=False)
        review.to_sql("review_checks", connection, if_exists="replace", index=False)
        connection.executescript((ROOT/"sql/homebuying.sql").read_text(encoding="utf-8"))
        check = pd.read_sql_query("SELECT * FROM case_reconciliation", connection)
        if check[[c for c in check.columns if c.endswith("_delta")]].abs().to_numpy().max() > 1e-7:
            raise ValueError("Independent SQL reconciliation failed")
    controls.append({"control": "Independent SQL reconciliation", "status": "Pass", "detail": f"{len(cases)} cash and income calculations agree with SQLite"})
    save_csv(OUT/"homebuying_controls.csv", pd.DataFrame(controls))
    from homebuying_audit import review_cases
    audit = review_cases(baseline)
    save_csv(OUT/"homebuying_bank_audit.csv", audit)
    with sqlite3.connect(OUT/"homebuying.sqlite") as connection:
        audit.to_sql("audit_reviews", connection, if_exists="replace", index=False)
    from homebuying_updates import build_updates
    updates = build_updates(cases)
    summary.update(latest_rate_period=updates["source_freshness"]["rate_period"], calculation_audit_rows=len(updates["calculation_audit"]))
    write_json(OUT/"homebuying_summary.json", summary)
    existing_map = json.loads((ASSETS/"visuals-data.json").read_text(encoding="utf-8"))["map"]
    map_payload = {**existing_map, "markers": projected_markers(existing_map)}
    # SVG plot coordinates are built locally, with explicit axes; no financial rules run in the browser.
    history_lines = {}
    for city in CITIES:
        group = history[history.city.eq(city)].sort_values("year")
        points = []
        for row in group.itertuples():
            x = 70+(row.year-2020)/3*640
            points.append({"year": int(row.year), "x": x, "required_y": 250-row.required_gross_income/250000*215,
                           "observed_y": 250-row.buyer_family_median_income/250000*215,
                           "required_income": row.required_gross_income, "buyer_family_income": row.buyer_family_median_income,
                           "price": row.price, "source_vintage": row.geography_vintage})
        def path(key, pts): return "M"+"L".join(f"{p['x']:.3f},{p[key]:.3f}" for p in pts)
        history_lines[city] = {"points": points, "required_path": path("required_y", points[1:]), "observed_path": path("observed_y", points[1:]),
                               "legacy_required_path": path("required_y", points[:2]), "legacy_observed_path": path("observed_y", points[:2])}
    waiting_lines = {}
    for city in CITIES:
        for buyer in PROFILES:
            initial = baseline[baseline.city.eq(city) & baseline.profile.eq(buyer.id)].iloc[0]
            for rent_growth in [0, .03, .06]:
                series = []
                for price_growth, style, label in [(-.05, "falling", "Prices -5% a year"), (0, "required", "Flat prices"), (.05, "rising", "Prices +5% a year")]:
                    group = waiting[waiting.city.eq(city) & waiting.profile.eq(buyer.id) & waiting.annual_rent_growth.eq(rent_growth) & waiting.annual_price_growth.eq(price_growth)].sort_values("months")
                    points = [{"months": 0, "x": 70, "y": 250-initial.required_gross_income/250000*215, "income": initial.required_gross_income, "barrier": initial.barrier}]
                    for item in group.itertuples():
                        points.append({"months": int(item.months), "x": 70+item.months/24*640, "y": 250-item.required_gross_income/250000*215, "income": item.required_gross_income, "barrier": item.barrier})
                    series.append({"label": label, "style": style, "points": points, "path": "M"+"L".join(f"{p['x']:.3f},{p['y']:.3f}" for p in points)})
                income_y = 250-buyer.gross_income/250000*215
                waiting_lines[f"{city}|{buyer.id}|{rent_growth:g}"] = {"series": series, "profile_path": f"M70,{income_y:.3f}L710,{income_y:.3f}"}
    payload = {**updates, "version": 3, "summary": summary, "cities": CITIES, "profiles": summary["profiles"],
               "scenarios": [{"id": s, "label": label} for s, label in SCENARIOS], "map": map_payload,
               "cases": records(cases), "history": records(history), "history_lines": history_lines,
               "waiting": records(waiting), "waiting_lines": waiting_lines, "programs": records(programs), "rate_replay": records(rate_replay), "decomposition": records(contributions),
               "controls": controls, "bank_audit": records(audit), "price_limits": records(limits), "review_checks": records(review), "sources": RULE_SOURCES}
    target = ASSETS/"homebuying-data.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")), encoding="utf-8", newline="\n")
    write_json(OUT/"homebuying_asset_manifest.json", {"file": str(target.relative_to(ROOT)).replace("\\", "/"),
               "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "bytes": target.stat().st_size, "price_year": latest_year, "rule_date": RULE_DATE})
    from mortgage_file_audit import build as build_training_file
    build_training_file()
    print(json.dumps({"summary": summary, "baseline": records(baseline[["city", "profile_label", "price", "cash_target", "cash_gap", "required_gross_income", "income_gap", "barrier"]])}, indent=2), flush=True)
    return payload

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-sources", action="store_true")
    args = parser.parse_args()
    if args.refresh_sources:
        from homebuying_data import refresh_sources, create_manifest
        refresh_sources()
        create_manifest()
    generate()
