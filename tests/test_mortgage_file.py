"""Evidence lineage, conservative funding, corrections, resolution and the fictional packet."""
import copy,hashlib,json,re,sqlite3,sys,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"src"))
from mortgage_file_audit import FIXTURE,analyse,validate
from refresh_homebuying_sources import load_refresh
OUT=ROOT/"data/processed"

def fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8")),load_refresh()[2]

def test_mock_case_has_a_false_pass_a_corrected_exception_and_a_revised_fit():
    case,rates=fixture();stages,findings,support=analyse(case,rates)
    assert stages.financial_pass.tolist()==[True,False,True]
    assert stages.required_gross_income.tolist()==pytest.approx([126574.714962871,161292.078878666,128609.647664622],abs=.00001)
    assert len(findings)==7 and support["gross_income"]==135000 and support["liquid_cash"]==85000
    assert stages.qualifying_rate.tolist()==[4.15,6.15,6.15]

def test_non_recurring_bonus_is_not_counted_twice_or_treated_as_stable_salary():
    case,rates=fixture();first=analyse(case,rates)[0]
    assert sum(r["annual_gross"] for r in case["income_records"])==case["application"]["gross_income"]
    case["income_records"][2]["annual_gross"]=30000
    second=analyse(case,rates)[0]
    assert first.loc[1,"profile_income"]==second.loc[1,"profile_income"]==135000
    assert second.loc[1,"required_gross_income"]==pytest.approx(first.loc[1,"required_gross_income"])

def test_pledged_money_is_removed_once_and_reserve_is_separate():
    case,rates=fixture();stages,_,support=analyse(case,rates)
    assert sum(r["balance"] for r in case["fund_records"])==100000
    assert sum(r["pledged"] for r in case["fund_records"])==15000
    assert support["liquid_cash"]==85000
    for r in stages.iloc[1:].itertuples():
        assert r.profile_cash==85000
        assert r.cash_spent+r.reserve==pytest.approx(85000)
        assert r.reserve==10000

def test_omitted_student_loan_is_traced_and_included():
    case,rates=fixture();stages,findings,support=analyse(case,rates)
    declared=sum(r["monthly_payment"] for r in case["debt_records"] if r["declared"])
    assert declared==case["application"]["monthly_debt"]==500
    assert support["monthly_debt"]==750
    debt=findings[findings.field.eq("monthly_debt")].iloc[0]
    assert debt.difference==250 and "DBT-001-C" in debt.evidence_ids
    assert stages.loc[1,"monthly_debt"]==750

def test_revised_request_changes_price_without_new_money_or_waived_debt():
    case,rates=fixture();stages,_,_=analyse(case,rates)
    corrected,revised=stages.iloc[1],stages.iloc[2]
    for col in ["profile_income","profile_cash","monthly_debt","heating","condo_fee","reserve","closing_allowance","contract_rate","qualifying_rate"]:
        assert corrected[col]==revised[col]
    assert revised.price==600000<corrected.price
    assert revised.annual_property_tax==pytest.approx(600000*.00278070)
    assert corrected.annual_property_tax==pytest.approx(764100*.00278070)

def test_keeping_the_original_price_does_not_resolve_the_income_exception():
    case,rates=fixture();case["revised_request"]["price"]=case["application"]["requested_price"]
    stages,_,_=analyse(case,rates)
    assert not stages.loc[2,"financial_pass"]
    assert stages.loc[2,"required_gross_income"]==pytest.approx(stages.loc[1,"required_gross_income"])

def test_financial_fit_never_authenticates_evidence_or_creates_an_approval():
    case,rates=fixture();case["income_records"][0]["annual_gross"]=1000000
    stages,_,_=analyse(case,rates)
    assert stages.loc[1,"financial_pass"] and stages.loc[2,"financial_pass"]
    assert not stages.external_evidence_verified.any() and not stages.actual_approval.any()
    assert stages.review_outcome.str.startswith("Hold:").all()
    assert stages.open_external_controls.eq(6).all()

def test_all_findings_have_numeric_deltas_units_and_existing_worksheet_ids():
    case,rates=fixture();_,findings,_=analyse(case,rates)
    ids={r["evidence_id"] for group in ["income_records","fund_records","debt_records"] for r in case[group]}
    ids.update(case[k]["evidence_id"] for k in ["application","cost_worksheet","rate_worksheet","revised_request"])
    assert not findings.finding_id.duplicated().any()
    for r in findings.itertuples():
        assert set(r.evidence_ids.split("|"))<=ids and r.unit
        assert r.difference==pytest.approx(r.supported-r.declared)
    assert findings.loc[findings.field.eq("qualifying_rate_used"),"difference_label"].item()=="+2.00 pp"

@pytest.mark.parametrize("change,error",[
    ("synthetic","explicitly synthetic"),("pledged","Pledged"),("duplicate","Duplicate"),("vintage","vintage"),("income_kind","income treatment")])
def test_invalid_or_unreviewed_file_inputs_are_rejected(change,error):
    case,rates=fixture()
    if change=="synthetic":case["synthetic"]=False
    elif change=="pledged":case["fund_records"][1]["pledged"]=50000
    elif change=="duplicate":case["income_records"][1]["evidence_id"]=case["income_records"][0]["evidence_id"]
    elif change=="vintage":case["rate_reference_period"]="2025-01"
    else:case["income_records"][0]["kind"]="unreviewed"
    with pytest.raises(ValueError,match=error):analyse(case,rates)

def test_financial_and_lineage_results_reconcile_to_independent_sql():
    with sqlite3.connect(OUT/"mortgage_file.sqlite") as db:
        finance=pd.read_sql_query("SELECT * FROM supported_finances",db).iloc[0]
        stages=pd.read_sql_query("SELECT * FROM stage_reconciliation",db)
        findings=pd.read_sql_query("SELECT * FROM finding_reconciliation",db)
    assert finance.to_dict()=={"gross_income":135000,"liquid_cash":85000,"monthly_debt":750}
    assert len(stages)==3 and len(findings)==7
    assert stages.filter(regex="_delta$").abs().to_numpy().max()<1e-7
    assert findings.supported_delta.abs().max()<1e-7

def test_training_outputs_are_marked_synthetic_and_match_saved_website_data():
    manifest=json.loads((OUT/"mortgage_file_manifest.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()==manifest["fixture_sha256"]
    asset=ROOT/manifest["asset"];assert hashlib.sha256(asset.read_bytes()).hexdigest()==manifest["asset_sha256"]
    data=json.loads(asset.read_text(encoding="utf-8"));assert data["synthetic"] is True
    stages=pd.read_csv(OUT/"mortgage_file_stages.csv")
    assert stages.synthetic.all() and not stages.actual_approval.any()
    assert np.allclose(stages.required_gross_income,[r["required_gross_income"] for r in data["stages"]],rtol=0,atol=1e-7)
    for p in OUT.glob("mortgage_file_*.csv"):assert pd.read_csv(p).synthetic.all(),p.name

def test_packet_is_complete_clearly_fictional_and_checksums_match_the_zip():
    folder=ROOT/"reports/mortgage_file";manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    pdf=PdfReader(folder/"MortgageFile-Audit-Pack.pdf");assert len(pdf.pages)==8
    for page in pdf.pages:
        text=page.extract_text()
        assert "FICTIONAL TRAINING FILE" in text and len(text)>300
    for r in manifest["assets"]:
        assert hashlib.sha256((ROOT/r["file"]).read_bytes()).hexdigest()==r["sha256"]
    archive_path=ROOT/"work/MortgageFile-Audit-Pack.zip"
    if archive_path.exists():
        with zipfile.ZipFile(archive_path) as archive:
            for r in manifest["assets"]:
                assert hashlib.sha256(archive.read(r["file"])).hexdigest()==r["sha256"]

def test_powerbi_file_review_imports_the_exact_three_stages_and_seven_findings():
    import base64
    model=json.loads((ROOT/"powerbi/HomebuyingBarriers.SemanticModel/model.bim").read_text(encoding="utf-8"))["model"]
    tables={t["name"]:t for t in model["tables"]}
    for name,file,key,cols in [
        ("FileStages","mortgage_file_stages.csv","stage_id",["price","profile_income","profile_cash","required_gross_income"]),
        ("FileFindings","mortgage_file_findings.csv","finding_id",["declared","supported","difference"])]:
        exp="\n".join(tables[name]["partitions"][0]["source"]["expression"])
        encoded=re.search(r'Binary.FromText\("([^"]+)"',exp).group(1)
        actual=pd.DataFrame(json.loads(base64.b64decode(encoded))).set_index(key).sort_index()
        expected=pd.read_csv(OUT/file).set_index(key).sort_index()
        assert list(actual.index)==list(expected.index)
        for col in cols:assert np.allclose(actual[col],expected[col],rtol=0,atol=1e-7)
    assert not any(r["fromTable"] in ["FileStages","FileFindings"] for r in model["relationships"])
