"""Check that website interactions preserve the published units and evidence."""
from pathlib import Path
import hashlib
import json
import math
import re
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from site_visuals import load_inputs, TENURE, STAT, POINT, LOW, HIGH, NATIONAL, usable_number


@pytest.fixture(scope="module")
def payload():
    return json.loads((ROOT / "docs/assets/visuals-data.json").read_text(encoding="utf-8"))


def test_map_estimates_are_renter_households_and_published_intervals(payload):
    frame, _, _ = load_inputs()
    source = frame[frame[TENURE].eq("Renter")].set_index(["REF_DATE", "GEO", STAT])
    for year, records in payload["regional"]["records"].items():
        for code, record in records.items():
            if int(code) >= 60:
                continue
            for field, measure in [("value", POINT), ("low", LOW), ("high", HIGH)]:
                row = source.loc[(int(year), record["name"], measure)]
                assert row.UOM == "Percent" and row.SCALAR_FACTOR == "units"
                assert record[field] == usable_number(row)


def test_national_benchmark_uses_published_estimate_not_provincial_mean(payload):
    frame, _, _ = load_inputs()
    source = frame[frame[TENURE].eq("Renter") & frame.GEO.eq(NATIONAL) & frame[STAT].eq(POINT)].set_index("REF_DATE")
    for year in payload["regional"]["years"]:
        expected = float(source.loc[year, "VALUE"])
        assert payload["regional"]["national"][str(year)]["value"] == expected
        for r in payload["regional"]["records"][str(year)].values():
            if r["value"] is not None:
                assert r["difference_pp"] == pytest.approx(r["value"] - expected)
    latest = payload["regional"]["records"]["2024"]
    assert sum(r["value"] for r in latest.values() if r["value"] is not None) / 10 != payload["regional"]["national"]["2024"]["value"]


def test_uncovered_territories_stay_missing_while_a_published_zero_is_valid(payload):
    for records in payload["regional"]["records"].values():
        for code in ["60", "61", "62"]:
            row = records[code]
            assert row["value"] is None and row["low"] is None and row["high"] is None
            assert row["difference_pp"] is None and row["bar_pct"] is None
            assert "coverage" in row["note"]
    assert usable_number(pd.Series({"STATUS": "", "VALUE": 0})) == 0
    assert usable_number(pd.Series({"STATUS": "x", "VALUE": 0})) is None


def test_display_geometry_retains_all_regions_with_finite_bounded_coordinates(payload):
    geometry = payload["map"]
    assert {f["code"] for f in geometry["features"]} == {"10", "11", "12", "13", "24", "35", "46", "47", "48", "59", "60", "61", "62"}
    assert geometry["display_vertices"] < geometry["input_vertices"] * .02
    assert geometry["projection"].endswith("EPSG:3347")
    for feature in geometry["features"]:
        assert feature["path"].startswith("M") and feature["path"].endswith("Z")
        points = [float(v) for v in re.findall(r"-?\d+\.\d+", feature["path"])]
        assert points and all(math.isfinite(v) for v in points)
        assert all(0 <= x <= geometry["width"] for x in points[::2])
        assert all(0 <= y <= geometry["height"] for y in points[1::2])


def test_trend_keeps_national_annual_values_and_accounting_gap(payload):
    source = pd.read_csv(ROOT / "data/processed/renter_annual_saving.csv").set_index("year")
    for record in payload["trend"]["records"]:
        annual = source.loc[record["year"]]
        for key, column in [("income", "income"), ("consumption", "consumption"), ("gap", "income_less_consumption"), ("saving", "saving"), ("pension", "pension")]:
            assert record[key] == annual[column]
        assert record["gap"] == record["income"] - record["consumption"]
        assert annual.quarter_count == 4


def test_cash_chart_uses_all_saved_cases_and_preserves_rule_discontinuity(payload):
    source = pd.read_csv(ROOT / "data/processed/home_purchase_cash_cases.csv").set_index(["closing_allowance_pct", "home_price"])
    count = 0
    for allowance, series in payload["cash"]["series"].items():
        assert len(series["paths"]) == 2
        for record in series["records"]:
            case = source.loc[(float(allowance), record["price"])]
            assert record["down"] == pytest.approx(case.minimum_down_payment)
            assert record["closing"] == pytest.approx(case.closing_allowance)
            assert record["total"] == pytest.approx(case.upfront_cash_scenario)
            count += 1
        cases = {r["price"]: r for r in series["records"]}
        assert cases[1500000]["down"] == 300000
        assert cases[1499999]["down"] == pytest.approx(124999.9)
    assert count == 30


def test_visual_asset_matches_recorded_hash(payload):
    manifest = json.loads((ROOT / "data/processed/website_visuals_manifest.json").read_text())
    asset = ROOT / manifest["file"]
    assert hashlib.sha256(asset.read_bytes()).hexdigest() == manifest["sha256"]
    assert asset.stat().st_size == manifest["bytes"] < 150000
    assert manifest["covered_provinces"] == 10 and manifest["uncovered_territories"] == 3
