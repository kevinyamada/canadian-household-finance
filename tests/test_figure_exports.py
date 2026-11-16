"""The published figure pack must stay tied to its saved evidence."""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/figures/portfolio"


def test_export_manifest_matches_source_and_published_artifacts():
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["figures"]) == 4 and len(manifest["files"]) == 10
    assert "CRLF normalized to LF" in manifest["input_hash_policy"]
    for item in manifest["inputs"]:
        raw = (ROOT / item["path"]).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(raw).hexdigest() == item["sha256"]
    for item in manifest["files"]:
        path = ROOT / item["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    assert manifest["selections"]["map_tenure"] == "Renter"
    assert manifest["selections"]["map_measure"] == "Percentage of households in core housing need"


def test_figures_are_readable_vector_and_raster_files_and_pdf_has_four_pages():
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    for figure in manifest["figures"]:
        with Image.open(OUT / (figure["id"] + ".png")) as image:
            assert image.width >= 2400 and image.height >= 1400
            assert max(image.convert("RGB").getextrema()[0]) - min(image.convert("RGB").getextrema()[0]) > 100
            image.load()
        tree = ET.parse(OUT / (figure["id"] + ".svg"))
        text = " ".join(tree.getroot().itertext())
        assert figure["title"] in text
        assert "Source" in text
    pdf = (OUT / "CanadianHouseholdFinance-Figures.pdf").read_bytes()
    assert pdf.startswith(b"%PDF-")
    assert len(re.findall(rb"/Type\s*/Page\b", pdf)) == 4
