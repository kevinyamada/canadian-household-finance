"""Small, reproducible extracts from official Canadian public sources."""
from pathlib import Path
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from urllib.parse import urlparse
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/homebuying"
WDS = "https://www150.statcan.gc.ca/t1/wds/rest/"
CITIES = {
    "Vancouver": {"province": "BC", "csd": "5915022", "current_id": 619, "legacy_id": 460,
                  "tax_rate": .00278070, "tax_basis": "2023 total residential rate; per CAD 1,000 taxable assessment",
                  "tax_source": "https://vancouver.ca/files/cov/2023-property-tax-rates.pdf"},
    "Victoria": {"province": "BC", "csd": "5917034", "current_id": 640, "legacy_id": 481,
                 "tax_rate": .0043621, "tax_basis": "2023 total including school and regional levies; per CAD 1,000 assessment",
                 "tax_source": "https://www.victoria.ca/media/file/annual-report-2024"},
    "Halifax": {"province": "NS", "csd": "1209034", "current_id": 6, "legacy_id": 5,
                "tax_rate": .01115, "tax_basis": "2023/24 HALIFAX urban residential rate; RM contains other tax areas",
                "tax_source": "https://data.novascotia.ca/Municipalities/Municipal-Property-Tax-Rates/ure8-3w7m/about_data"},
}
RATE_SERIES = {"insured": "V122667780", "uninsured": "V122667786"}
ALLOWED_DOMAINS = ("statcan.gc.ca", "bankofcanada.ca", "canada.ca", "cmhc-schl.gc.ca", "gov.bc.ca",
                   "bclaws.gov.bc.ca", "halifax.ca", "victoria.ca", "vancouver.ca", "novascotia.ca", "geogratis.gc.ca", "osfi-bsif.gc.ca")
RULE_SOURCES = {
    "OSFI mortgage underwriting and audit": "https://www.osfi-bsif.gc.ca/en/guidance/guidance-library/residential-mortgage-underwriting-practices-procedures-guideline-2017",
    "CMHC debt service and stress test": "https://www.cmhc-schl.gc.ca/professionals/project-funding-and-mortgage-financing/mortgage-loan-insurance/calculating-gds-tds",
    "CMHC insurance premiums": "https://www.cmhc-schl.gc.ca/professionals/project-funding-and-mortgage-financing/mortgage-loan-insurance/mortgage-loan-insurance-homeownership-programs/premium-information-for-homeowner-and-small-rental-loans",
    "CMHC purchase requirements": "https://www.cmhc-schl.gc.ca/consumers/home-buying/mortgage-loan-insurance-for-consumers/what-are-the-general-requirements-to-qualify-for-homeowner-mortgage-loan-insurance",
    "FCAC payment examples": "https://www.canada.ca/en/financial-consumer-agency/services/mortgages/interest-on-mortgages.html",
    "FCAC 30-year amortization": "https://www.canada.ca/en/financial-consumer-agency/services/mortgages/relief-options.html",
    "BC transfer tax statute": "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/96378_01",
    "BC first-time buyer amounts": "https://www2.gov.bc.ca/gov/content/taxes/property-taxes/property-transfer-tax/exemptions/first-time-home-buyers/current-amount",
    "Halifax transfer tax": "https://cdn.halifax.ca/sites/default/files/documents/city-hall/regional-council/220531rc1517.pdf",
    "CRA FHSA": "https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/first-home-savings-account.html",
    "CRA HBP": "https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/rrsps-related-plans/what-home-buyers-plan.html",
}

def trusted_url(url):
    host = urlparse(url).hostname or ""
    return urlparse(url).scheme == "https" and any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8", newline="\n")

def request_json(url, body=None):
    if not trusted_url(url):
        raise ValueError("Source is outside the official Canadian source policy")
    response = requests.get(url, timeout=60) if body is None else requests.post(url, json=body, timeout=60)
    response.raise_for_status()
    if not trusted_url(response.url):
        raise ValueError("Source redirected outside the source policy")
    return response.json()

def refresh_sources():
    RAW.mkdir(parents=True, exist_ok=True)
    for pid, key in [(46100099, "current_id"), (46100062, "legacy_id")]:
        metadata = request_json(WDS + "getCubeMetadata", [{"productId": pid}])
        write_json(RAW / f"metadata_{pid}.json", metadata)
        queries = [{"productId": pid, "coordinate": f'{spec[key]}.1.1.2.1.{measure}.0.0.0.0', "latestN": 10}
                   for spec in CITIES.values() for measure in [1, 5, 7, 9]]
        responses = request_json(WDS + "getDataFromCubePidCoordAndLatestNPeriods", queries)
        write_json(RAW / f"selected_{pid}.json", {"endpoint": WDS + "getDataFromCubePidCoordAndLatestNPeriods", "queries": queries, "responses": responses})
    write_json(RAW / "wds_codes.json", request_json(WDS + "getCodeSets"))
    for code in RATE_SERIES.values():
        payload = request_json(f"https://www.bankofcanada.ca/valet/observations/{code}/json?start_date=2020-01-01&end_date=2025-12-31")
        write_json(RAW / f"boc_{code}.json", payload)
    # Rule changes and property-tax observations require an explicit human source review.
    return True

def policy_record():
    return {
        "as_of": "2026-11-16",
        "verified_by": "Official source pages reviewed; selected downloads and structured reference facts retained. Direct HTTP downloads of some CMHC/BC/Vancouver pages were blocked; their official web views were reviewed.",
        "gds_limit": .39, "tds_limit": .44, "stress_floor_pct": 5.25, "stress_buffer_pp": 2,
        "insured_price_cap_exclusive": 1500000, "insured_30_year_surcharge": .002,
        "premium_tiers": [{"max_ltv": .85, "premium_rate": .028}, {"max_ltv": .90, "premium_rate": .031}, {"max_ltv": .95, "premium_rate": .04}],
        "bc_transfer_thresholds": [200000, 2000000, 3000000],
        "bc_first_time": {"full_relief_value_limit": 835000, "partial_relief_value_limit": 860000, "maximum_relief": 8000, "exempt_first_value": 500000},
        "halifax_deed_transfer_rate": .015,
        "premium_sales_tax_selected_provinces": 0,
        "sources": RULE_SOURCES,
        "published_example_discrepancy": {"rate": 4, "published_monthly": 1587.06, "formula_monthly": 1578.06, "note": "The FCAC monthly cell transposes digits. The same row total interest of 173418.18 implies 1578.06; the model retains the standard semiannual-compounding formula."},
        "fcac_examples": [{"principal": 300000, "years": 25, "rate": r, "monthly": p} for r, p in [
            (2.5, 1343.90), (2.9, 1404.39), (3.4, 1482.02), (3.8, 1545.70),
            (4, 1587.06), (4.5, 1660.42), (4.8, 1710.82), (5, 1744.81), (5.2, 1779.13)]],
        "conditions": [
            "Hypothetical owner-occupied resale, traditional down-payment funds, first-time buyer and BC relief conditions assumed satisfied; actual eligibility not verified.",
            "BC relief assumes a qualifying property, eligible citizenship/residence, occupancy, land-size and ownership conditions.",
            "No foreign-buyer or NS non-resident taxes: profiles assume eligible residents of the purchase province.",
            "FHSA and HBP limits are not additional wealth. No program funds are added to cash without separate account balances and eligibility.",
            "2026 rules are held constant over historical inputs; calculations do not reconstruct historical approvals or historical tax benefits.",
        ],
    }

def create_manifest():
    items = []
    catalog_path = RAW / "source_catalog.json"
    catalog = json.loads(catalog_path.read_text()) if catalog_path.exists() else []
    references = {item["file"]: item["url"] for item in catalog}
    for pid in [46100099, 46100062]:
        references[f"metadata_{pid}.json"] = WDS + "getCubeMetadata"
        references[f"selected_{pid}.json"] = WDS + "getDataFromCubePidCoordAndLatestNPeriods"
    for code in RATE_SERIES.values():
        references[f"boc_{code}.json"] = f"https://www.bankofcanada.ca/valet/observations/{code}/json?start_date=2020-01-01&end_date=2025-12-31"
    for name, url in references.items():
        path = RAW / name
        if not path.exists():
            raise ValueError("Missing preserved source: " + name)
        assert trusted_url(url), url
        items.append({"file": name, "url": url, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    write_json(RAW / "rules.json", policy_record())
    write_json(RAW / "manifest.json", {
        "created_utc": datetime.now(timezone.utc).isoformat(), "source_policy": "Statistics Canada first; only official Canadian public bodies used",
        "sources": items, "rules_file": "rules.json", "rules_sha256": hashlib.sha256((RAW / "rules.json").read_bytes()).hexdigest(),
        "large_bulk_archive": "Unused 350 MB national ZIP retained only in ignored local work/official_downloads; production uses 24 narrowly specified WDS series.",
    })

def verify_manifest():
    record = json.loads((RAW / "manifest.json").read_text(encoding="utf-8"))
    for item in record["sources"]:
        assert trusted_url(item["url"])
        if hashlib.sha256((RAW / item["file"]).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Source checksum mismatch: " + item["file"])
    assert hashlib.sha256((RAW / record["rules_file"]).read_bytes()).hexdigest() == record["rules_sha256"]
    return record

def published_number(point):
    # WDS status 3 is excellent quality, not a missing estimate; preserve status in the output.
    usable_statuses = {0, 2, 3, 4, 5, 6, 7}
    if point.get("securityLevelCode") != 0 or point.get("statusCode") not in usable_statuses or point.get("value") is None:
        return None
    value = float(point["value"])
    return value if math.isfinite(value) else None

def observed_data():
    rows = []
    for pid, id_key in [(46100099, "current_id"), (46100062, "legacy_id")]:
        specs = {s[id_key]: (city, s) for city, s in CITIES.items()}
        payload = json.loads((RAW / f"selected_{pid}.json").read_text(encoding="utf-8"))
        for response in payload["responses"]:
            if response["status"] != "SUCCESS":
                raise ValueError("Statistics Canada rejected a selected series")
            obj = response["object"]
            coord = [int(x) for x in obj["coordinate"].split(".")]
            city, spec = specs[coord[0]]
            assert coord[1:5] == [1, 1, 2, 1], "Use all buyer counts, all ages, first-time buyers, total sex categories"
            for dp in obj["vectorDataPoint"]:
                year = int(dp["refPer"][:4])
                if year < 2020:
                    continue
                assert dp["scalarFactorCode"] == 0
                value = dp.get("value")
                value = published_number(dp)
                rows.append({"city": city, "csd": spec["csd"], "year": year, "measure": coord[5],
                             "value": value, "status": dp["statusCode"],
                             "security": dp["securityLevelCode"], "table": str(pid), "vector": str(obj["vectorId"]),
                             "geography_vintage": 2021 if pid == 46100099 else 2016})
    long = pd.DataFrame(rows)
    if long.duplicated(["city", "year", "measure", "table"]).any():
        raise ValueError("Duplicate source keys")
    wide = long.pivot(index=["city", "csd", "year", "table", "geography_vintage"], columns="measure", values="value").reset_index()
    wide = wide.rename(columns={1: "first_time_buyers", 5: "buyer_family_median_income", 7: "buyer_median_sale_price", 9: "published_median_price_income_ratio"})
    bridge = wide[wide.year.eq(2021)].sort_values(["city", "table"])
    # The 2020 legacy point is displayed separately; 2021–2023 uses only the current geography series.
    observed = wide[(wide.table.eq("46100099")) | (wide.table.eq("46100062") & wide.year.eq(2020))].copy()
    if observed.duplicated(["city", "year"]).any():
        raise ValueError("Market/year join must be unique")
    if observed[["buyer_median_sale_price", "buyer_family_median_income"]].isna().any().any():
        raise ValueError("Missing or suppressed price/income must stay unavailable")
    return long, observed.sort_values(["city", "year"]), bridge

def annual_rates():
    series = []
    for kind, code in RATE_SERIES.items():
        body = json.loads((RAW / f"boc_{code}.json").read_text(encoding="utf-8"))
        detail = body["seriesDetail"][code]
        assert detail["label"] == "Fixed rate, 5 years and over"
        assert "Funds advanced" in detail["description"], "Do not substitute outstanding-balance mortgage rates"
        assert (", uninsured," if kind == "uninsured" else ", insured,") in detail["description"]
        frame = pd.DataFrame([{"year": int(row["d"][:4]), "month": row["d"], "rate": float(row[code]["v"])}
                              for row in body["observations"] if code in row])
        annual = frame.groupby("year").agg(rate=("rate", "mean"), months=("month", "nunique")).reset_index()
        if not annual.months.eq(12).all():
            raise ValueError("Annual rates need twelve monthly observations")
        annual["kind"] = kind
        annual["series"] = code
        series.append(annual)
    result = pd.concat(series, ignore_index=True)
    if result.duplicated(["year", "kind"]).any():
        raise ValueError("Duplicate rate/year keys")
    return result
