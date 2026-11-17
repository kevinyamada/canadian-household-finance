"""Preserve a dated refresh of official rates without changing matched historical inputs."""
from datetime import date,datetime,timezone
from pathlib import Path
import argparse
import hashlib
import json
import math
import requests
from homebuying_data import ROOT,RATE_SERIES,trusted_url,write_json

RAW=ROOT/"data/raw/homebuying_refresh"
TABLE_URL="https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=4610009901"
RELEASE_URL="https://www150.statcan.gc.ca/n1/daily-quotidien/260826/dq260826b-eng.htm"
BOC_PAGE="https://www.bankofcanada.ca/rates/banking-and-financial-statistics/interest-rates-for-new-and-existing-lending-by-chartered-banks/"

def latest_common_rates(payloads,as_of):
    """Use the latest month available in both series; exclude observations after the cutoff."""
    cutoff=date.fromisoformat(as_of);by_kind={}
    for kind,code in RATE_SERIES.items():
        body=payloads[kind];detail=body["seriesDetail"][code]
        if detail["label"]!="Fixed rate, 5 years and over" or "Funds advanced" not in detail["description"]:
            raise ValueError("Expected funds-advanced fixed five-year-and-over mortgage rates")
        marker=", uninsured," if kind=="uninsured" else ", insured,"
        if marker not in detail["description"]:raise ValueError("Wrong insured/uninsured rate series")
        points={}
        for row in body["observations"]:
            if code not in row:continue
            observed=date.fromisoformat(row["d"])
            if observed>cutoff:continue
            period=row["d"][:7];value=float(row[code]["v"])
            if period in points:raise ValueError("Duplicate monthly rate")
            if not math.isfinite(value) or value<0:raise ValueError("Invalid mortgage rate")
            points[period]=value
        by_kind[kind]=points
    common=set(by_kind["insured"])&set(by_kind["uninsured"])
    if not common:raise ValueError("No common published mortgage-rate month")
    period=max(common)
    return {"period":period,"insured":by_kind["insured"][period],"uninsured":by_kind["uninsured"][period]}

def preserve(payloads,as_of,review,attempts):
    date.fromisoformat(as_of)
    if review["checked_on"]!=as_of:raise ValueError("A dated official Statistics Canada release review is required")
    latest=latest_common_rates(payloads,as_of)
    RAW.mkdir(parents=True,exist_ok=True);sources=[]
    for kind,code in RATE_SERIES.items():
        name=f"boc_{code}.json";write_json(RAW/name,payloads[kind])
        url=f"https://www.bankofcanada.ca/valet/observations/{code}/json?start_date=2020-01-01&end_date={as_of}"
        sources.append({"file":name,"url":url,"sha256":hashlib.sha256((RAW/name).read_bytes()).hexdigest()})
    write_json(RAW/"statcan_release_review.json",review)
    sources.append({"file":"statcan_release_review.json","url":RELEASE_URL,
                    "sha256":hashlib.sha256((RAW/"statcan_release_review.json").read_bytes()).hexdigest()})
    write_json(RAW/"manifest.json",{"checked_on":as_of,"retrieved_utc":datetime.now(timezone.utc).isoformat(),
        "sources":sources,"latest_common_rates":latest,"retrieval_attempts":attempts,
        "source_policy":"Official Canadian public bodies only; historical source snapshots are preserved separately.",
        "execution":"Kevin's desktop VS Code integrated terminal"})
    return latest

def load_refresh():
    manifest=json.loads((RAW/"manifest.json").read_text(encoding="utf-8"))
    for item in manifest["sources"]:
        if not trusted_url(item["url"]):raise ValueError("Untrusted source")
        if hashlib.sha256((RAW/item["file"]).read_bytes()).hexdigest()!=item["sha256"]:raise ValueError("Refresh checksum mismatch")
    payloads={kind:json.loads((RAW/f"boc_{code}.json").read_text(encoding="utf-8")) for kind,code in RATE_SERIES.items()}
    review=json.loads((RAW/"statcan_release_review.json").read_text(encoding="utf-8"))
    latest=latest_common_rates(payloads,manifest["checked_on"])
    if latest!=manifest["latest_common_rates"]:raise ValueError("Latest-rate record does not reconcile")
    return manifest,review,latest

def refresh(as_of,review_path):
    """Download rates; a blocked StatCan endpoint is recorded, not silently declared refreshed."""
    review=json.loads(Path(review_path).read_text(encoding="utf-8"));payloads={};attempts=[]
    for kind,code in RATE_SERIES.items():
        url=f"https://www.bankofcanada.ca/valet/observations/{code}/json?start_date=2020-01-01&end_date={as_of}"
        response=requests.get(url,timeout=40);response.raise_for_status()
        if not trusted_url(response.url):raise ValueError("Untrusted redirect")
        payloads[kind]=response.json();attempts.append({"url":url,"http_status":response.status_code,"result":"Downloaded"})
    url="https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata"
    response=requests.post(url,json=[{"productId":46100099}],timeout=40)
    if response.ok:
        metadata=response.json()[0]["object"]
        if int(metadata["cubeEndDate"][:4])>review["latest_sales_year"]:raise ValueError("Newer buyer data require a new matched-baseline review")
        attempts.append({"url":url,"http_status":response.status_code,"result":"Metadata checked"})
    else:
        attempts.append({"url":url,"http_status":response.status_code,"result":"Endpoint unavailable; official release checked separately; historical extract not re-downloaded"})
    return preserve(payloads,as_of,review,attempts)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--as-of",required=True)
    parser.add_argument("--statcan-review",required=True,help="Dated JSON record of official release-page review")
    args=parser.parse_args()
    print(json.dumps(refresh(args.as_of,args.statcan_review),indent=2))
