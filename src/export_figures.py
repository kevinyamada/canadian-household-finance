"""Export the website's saved evidence as publication figures and a download pack."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import io
import json
import re
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.patches import PathPatch
from matplotlib.path import Path as PlotPath
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/figures/portfolio"
PAPER, INK, MUTED = "#fafbf8", "#1c2d29", "#54635e"
GREEN, RUST, RULE = "#286c5a", "#b3633f", "#d7dfda"
RELEASE = "https://github.com/kevinyamada/canadian-household-finance/releases/tag/v2.1.0"
FIGURES = [
    ("renter_housing_need", "Housing need differs across provinces."),
    ("renter_income_consumption", "Income did not keep up with consumption."),
    ("purchase_cash", "The down payment is only the start."),
    ("saving_reconciliation", "Positive saving is not verified deposit cash."),
]
INPUTS = [
    "docs/assets/visuals-data.json",
    "data/processed/regional_housing_need.csv",
    "data/processed/renter_annual_saving.csv",
    "data/processed/home_purchase_cash_cases.csv",
    "data/processed/housing_audit_summary.json",
    "data/raw/site_visuals/manifest.json",
    "data/raw/housing/purchase_rules.json",
]

def configure():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 11,
        "figure.facecolor": PAPER, "axes.facecolor": PAPER,
        "text.color": INK, "axes.labelcolor": MUTED,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.edgecolor": RULE, "axes.spines.top": False,
        "axes.spines.right": False, "axes.spines.left": False,
        "axes.spines.bottom": False, "svg.fonttype": "none",
        "svg.hashsalt": "canadian-household-finance-figures-v1",
    })

def money(value):
    return ("−" if value < 0 else "") + "CAD " + f"{abs(value):,.0f}"

def heading(fig, title, subtitle):
    fig.text(.055, .935, title, fontsize=23, fontweight="bold", va="top")
    fig.text(.055, .875, subtitle, fontsize=11, color=MUTED, va="top")

def notes(fig, text):
    fig.text(.055, .075, text, fontsize=8.5, color=MUTED, linespacing=1.6, va="top")
    fig.text(.945, .025, "Kevin Yamada · Canadian Household Finance", fontsize=8, color=MUTED, ha="right")

def path_from_svg(value):
    tokens = re.findall(r"[MLZ]|-?\d+(?:\.\d+)?", value)
    vertices, codes, start = [], [], None
    i = 0
    while i < len(tokens):
        command = tokens[i]
        if command == "Z":
            vertices.append(start); codes.append(PlotPath.CLOSEPOLY); i += 1
        else:
            assert command in ("M", "L")
            point = (float(tokens[i + 1]), float(tokens[i + 2]))
            if command == "M":
                start = point
            vertices.append(point)
            codes.append(PlotPath.MOVETO if command == "M" else PlotPath.LINETO)
            i += 3
    return PlotPath(vertices, codes)

def housing_need(data):
    fig = plt.figure(figsize=(15, 8.5))
    year = str(data["regional"]["latest_year"])
    records = data["regional"]["records"][year]
    national = data["regional"]["national"][year]["value"]
    heading(fig, FIGURES[0][1], f"Renter households in core housing need · {year} Canadian Housing Survey")
    ax = fig.add_axes([.035, .19, .49, .64])
    for feature in data["map"]["features"]:
        row = records[feature["code"]]
        missing = row["value"] is None
        patch = PathPatch(path_from_svg(feature["path"]),
            facecolor="#edf1ec" if missing else row["fill_light"],
            edgecolor="#b8c4bb" if missing else PAPER,
            linewidth=.35, hatch="////" if missing else None)
        ax.add_patch(patch)
    x, y, w, h = data["map"]["view_all"]
    ax.set(xlim=(x, x+w), ylim=(y+h, y), aspect="equal")
    ax.axis("off")
    palette = LinearSegmentedColormap.from_list("housing_need", ["#daeadb", "#994d2a"])
    colour_ax = fig.add_axes([.09, .157, .32, .016])
    colourbar = fig.colorbar(ScalarMappable(norm=Normalize(0, 50), cmap=palette), cax=colour_ax, orientation="horizontal", ticks=[0, 25, 50])
    colourbar.outline.set_visible(False)
    colourbar.ax.set_xticklabels(["0%", "25%", "50%"])
    colourbar.ax.tick_params(labelsize=8, length=0)
    fig.text(.09, .116, "Hatched territories: outside survey coverage", fontsize=8, color=MUTED)
    bars = fig.add_axes([.735, .205, .215, .60])
    rows = sorted((r for r in records.values() if r["value"] is not None), key=lambda r: (-r["value"], r["name"]))
    positions = list(range(len(rows)))
    values = [r["value"] for r in rows]
    bars.barh(positions, values, color=[r["fill_light"] for r in rows], height=.58, zorder=2)
    bars.errorbar(values, positions, xerr=[[r["value"]-r["low"] for r in rows], [r["high"]-r["value"] for r in rows]],
                  fmt="none", ecolor=INK, elinewidth=.8, capsize=3, zorder=3)
    bars.axvline(national, color=GREEN, linestyle="--", linewidth=1.3, zorder=1)
    bars.set_yticks(positions, [r["name"] for r in rows], fontsize=9)
    bars.invert_yaxis()
    bars.set_xlim(0, 50)
    bars.set_xticks([0, 10, 20, 30, 40, 50], [f"{v}%" for v in [0, 10, 20, 30, 40, 50]])
    bars.tick_params(axis="both", length=0, pad=7)
    bars.grid(axis="x", color=RULE, linewidth=.6, zorder=0)
    for index, row in enumerate(rows):
        bars.text(48, index, f'{row["value"]:.1f}%', ha="right", va="center", fontsize=9, fontweight="bold", bbox={"facecolor": PAPER, "edgecolor": "none", "pad": 2})
    fig.text(.735, .828, f"Canada, ten provinces: {national:.1f}%", fontsize=10, color=GREEN)
    notes(fig, "Source: Statistics Canada 46-10-0085-01; 2021 cartographic boundaries, adapted under the Statistics Canada Open Licence.\nBars show published point estimates and 95% confidence intervals. Ordering does not establish significant differences; missing is not zero.")
    return fig

def income_consumption(data):
    fig = plt.figure(figsize=(14, 8))
    heading(fig, FIGURES[1][1], "Canada · Renter household averages · Full-year sums, 2020–2025")
    ax = fig.add_axes([.10, .26, .80, .54])
    rows = data["trend"]["records"]
    years = [r["year"] for r in rows]
    income = [r["income"] for r in rows]
    consumption = [r["consumption"] for r in rows]
    ax.fill_between(years, income, consumption, color=MUTED, alpha=.10, zorder=1)
    ax.plot(years, income, color=GREEN, linewidth=2.8, marker="o", markersize=6, label="Disposable income", zorder=3)
    ax.plot(years, consumption, color=RUST, linewidth=2.8, marker="o", markersize=6, linestyle="--", label="Consumption", zorder=3)
    ax.set(xlim=(2019.85, 2025.9), ylim=(50000, 80000), xticks=years, yticks=[50000, 60000, 70000, 80000])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_ylabel("Nominal CAD per household", labelpad=13)
    ax.grid(axis="y", color=RULE, linewidth=.8)
    ax.tick_params(length=0, pad=12)
    ax.legend(loc="upper left", frameon=False, ncols=2, bbox_to_anchor=(0, 1.10))
    latest = rows[-1]
    ax.annotate(money(latest["consumption"]), (latest["year"], latest["consumption"]), xytext=(13, 8), textcoords="offset points", color=RUST, fontsize=10)
    ax.annotate(money(latest["income"]), (latest["year"], latest["income"]), xytext=(13, -15), textcoords="offset points", color=GREEN, fontsize=10)
    fig.text(.10, .17, "2025 income less consumption: " + money(latest["gap"]), fontsize=15, fontweight="bold", color=RUST)
    notes(fig, "Source: Statistics Canada 36-10-0662-01. Each annual value sums four quarterly per-household estimates over changing groups.\nNominal, not seasonally adjusted; national accounts include imputations. The vertical axis starts at CAD 50,000. These are not bank-account budgets.")
    return fig

def purchase_cash(data):
    fig = plt.figure(figsize=(14, 8))
    heading(fig, FIGURES[2][1], "Illustrative purchase prices and closing allowances · Rules checked November 16, 2026")
    ax = fig.add_axes([.085, .275, .56, .49])
    colours = {"1.5": "#789079", "2.5": GREEN, "4": RUST}
    styles = {"1.5": ":", "2.5": "-", "4": "--"}
    for allowance, series in data["cash"]["series"].items():
        rows = series["records"]
        for index, group in enumerate([[r for r in rows if r["price"] < 1500000], [r for r in rows if r["price"] >= 1500000]]):
            ax.plot([r["price"] for r in group], [r["total"] for r in group],
                    color=colours[allowance], linestyle=styles[allowance],
                    linewidth=2.7 if allowance == "2.5" else 1.6,
                    label=f"{allowance}% allowance" if index == 0 else None)
    ax.axvline(1500000, color=MUTED, linewidth=.8, linestyle="--", alpha=.6)
    ax.set(xlim=(280000, 2030000), ylim=(0, 500000))
    ax.set_xticks([300000, 600000, 1000000, 1500000, 2000000], ["300k", "600k", "1m", "1.5m", "2m"])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v/1000:,.0f}k"))
    ax.set_xlabel("Illustrative purchase price · CAD", labelpad=12)
    ax.set_ylabel("Upfront cash · CAD", labelpad=13)
    ax.tick_params(length=0, pad=9)
    ax.grid(axis="y", color=RULE, linewidth=.7)
    ax.legend(frameon=False, loc="upper left", fontsize=9, ncols=3, bbox_to_anchor=(-.01, 1.14))
    case = next(r for r in data["cash"]["series"]["2.5"]["records"] if r["price"] == 600000)
    ax.scatter([case["price"]], [case["total"]], s=70, color=GREEN, edgecolor=PAPER, linewidth=1.5, zorder=5)
    ax.annotate(money(case["total"]), (case["price"], case["total"]), xytext=(8, 20), textcoords="offset points", color=GREEN, fontweight="bold", fontsize=10)
    fig.text(.71, .73, "CAD 600,000 purchase", fontsize=13, fontweight="bold")
    for label, value, y in [
        ("Minimum down payment", case["down"], .65),
        ("Assumed closing costs, 2.5%", case["closing"], .53),
        ("Cash in this scenario", case["total"], .38),
    ]:
        fig.text(.71, y, label, fontsize=10, color=MUTED)
        fig.text(.71, y-.055, money(value), fontsize=22 if y == .38 else 18, color=GREEN if y == .38 else INK, fontweight="bold")
    split = fig.add_axes([.71, .23, .23, .018])
    split.barh([0], [case["down"]], color=GREEN)
    split.barh([0], [case["closing"]], left=[case["down"]], color=RUST)
    split.set_xlim(0, case["total"]); split.axis("off")
    fig.text(.085, .17, "At CAD 1.5 million, minimum down changes to 20%; the line is split at that boundary.", fontsize=10, color=MUTED)
    notes(fig, "Sources: CMHC and Finance Canada; versioned rule record dated November 16, 2026. Values are rounded to the nearest CAD.\nPrices and closing allowances are assumptions, not provincial market prices. Upfront cash only; not approval, all taxes or a complete closing budget.")
    return fig

def saving_reconciliation(data, summary):
    fig = plt.figure(figsize=(14, 8))
    heading(fig, FIGURES[3][1], "Canada · Renter household averages · 2025 Q4")
    ax = fig.add_axes([.10, .265, .54, .49])
    gap, pension, saving = [summary[k] for k in ["quarterly_income_less_consumption", "quarterly_pension", "quarterly_net_saving"]]
    assert abs(gap + pension - saving) <= 2
    ax.bar([0], [gap], color=RUST, width=.57)
    ax.bar([1], [pension], bottom=[gap], color="#8eae9d", width=.57)
    ax.bar([2], [saving], color=GREEN, width=.57)
    ax.plot([.285, .715], [gap, gap], color=MUTED, linewidth=.8, linestyle="--")
    ax.plot([1.285, 1.715], [saving, saving], color=MUTED, linewidth=.8, linestyle="--")
    ax.axhline(0, color=MUTED, linewidth=.8)
    ax.set(ylim=(-850, 650), xlim=(-.6, 2.6), ylabel="CAD per renter household")
    ax.set_xticks([0, 1, 2], ["Income less\nconsumption", "Pension-entitlement\nadjustment", "Reported\nnet saving"])
    ax.tick_params(length=0, pad=12)
    ax.grid(axis="y", color=RULE, linewidth=.6, zorder=0)
    ax.set_axisbelow(True)
    ax.text(0, gap-65, money(gap), ha="center", va="top", fontsize=13, fontweight="bold", color=RUST)
    ax.text(1, saving+70, "+"+money(pension), ha="center", va="bottom", fontsize=13, fontweight="bold")
    ax.text(2, saving+70, "+"+money(saving), ha="center", va="bottom", fontsize=13, fontweight="bold", color=GREEN)
    fig.text(.715, .68, "Full-year 2025", fontsize=13, color=MUTED)
    fig.text(.715, .585, money(summary["annual_net_saving"]), fontsize=31, fontweight="bold", color=RUST)
    fig.text(.715, .525, "Reported net saving", fontsize=13)
    fig.text(.715, .435, "Sum all four quarters.\nDo not annualize the\npositive final quarter.", fontsize=12, linespacing=1.7, va="top")
    fig.text(.10, .17, "A pension adjustment changes reported saving; it does not verify deposit cash.", fontsize=12, fontweight="bold")
    notes(fig, "Source: Statistics Canada 36-10-0662-01. Quarterly nominal CAD per household; not seasonally adjusted.\nAnnual amounts sum quarterly averages over changing groups. National accounts include imputations and pension entitlements, not verified liquid funds.")
    return fig

def gallery():
    descriptions = [
        "Published 2024 renter-household estimates and 95% confidence intervals. The national benchmark is 22%; territories are outside coverage. Ordering is not a significance test.",
        "National renter income and consumption, 2020–2025. The 2025 accounting gap is −CAD 3,570. The figures are nominal sums of quarterly averages, not bank-account budgets.",
        "Thirty saved purchase-cash scenarios. A CAD 600,000 price and 2.5% assumed closing allowance give CAD 35,000 down plus CAD 15,000 allowance. Prices are illustrative; eligibility is not estimated.",
        "The 2025 Q4 accounting reconciliation: −572 + 841 = 269. All four quarters give −CAD 557 for 2025; the positive quarter does not prove deposit cash.",
    ]
    lines = [
        "# Figures: why does buying a home still feel out of reach?", "",
        "Downloadable figures from the same saved evidence used on the project website. Generated with Python and Matplotlib in local VS Code.", "",
        "[Interactive website](https://kevinyamada.github.io/canadian-household-finance/) · [Four-page PDF](CanadianHouseholdFinance-Figures.pdf) · [Download pack]("+RELEASE+")", "",
        "PNG files are for quick sharing. SVG files preserve editable text and vector paths. The ZIP also includes the source tables and hash manifest.", "",
    ]
    for (stem, title), description in zip(FIGURES, descriptions):
        lines += ["## "+title, "", description, "", f"[PNG]({stem}.png) · [SVG]({stem}.svg)", "", f"![{description}]({stem}.png)", ""]
    lines += [
        "## Sources and reproduction", "",
        "Statistics Canada tables [46-10-0085-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=4610008501) and [36-10-0662-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3610066201); Statistics Canada 2021 cartographic boundaries; current CMHC and Finance Canada purchase-rule record.", "",
        "The map, national accounts and purchase scenarios cover different measures and periods. Their comparison does not establish causation or an individual buying date. Adapted Statistics Canada material uses the [Open Licence](https://www.statcan.gc.ca/en/reference/licence).", "",
        "Run python src/export_figures.py in the project VS Code terminal after preparing the saved website data. See [visualization methods](../../../docs/website_visuals.md). Figure inputs and outputs are recorded in [manifest.json](manifest.json).", "",
    ]
    return "\n".join(lines)

def generate(root=ROOT):
    assert root == ROOT, "Use the checked-out project root"
    configure()
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.loads((ROOT / INPUTS[0]).read_text(encoding="utf-8"))
    summary = json.loads((ROOT / "data/processed/housing_audit_summary.json").read_text())
    figures = [housing_need(data), income_consumption(data), purchase_cash(data), saving_reconciliation(data, summary)]
    pdf_path = OUT / "CanadianHouseholdFinance-Figures.pdf"
    with PdfPages(pdf_path, metadata={"Title": summary["question"], "Author": "Kevin Yamada", "Creator": "Canadian Household Finance", "CreationDate": None, "ModDate": None}) as pdf:
        for (stem, title), fig in zip(FIGURES, figures):
            fig.savefig(OUT / (stem+".png"), dpi=180, metadata={"Title": title, "Software": "Canadian Household Finance"})
            buffer = io.StringIO()
            fig.savefig(buffer, format="svg", metadata={"Title": title, "Creator": "Canadian Household Finance", "Date": None})
            (OUT / (stem+".svg")).write_text(buffer.getvalue(), encoding="utf-8", newline="\n")
            pdf.savefig(fig)
            plt.close(fig)
    (OUT / "README.md").write_text(gallery(), encoding="utf-8", newline="\n")
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "execution": "Python and Matplotlib in the local project VS Code integrated terminal",
        "generator": "src/export_figures.py",
        "input_hash_policy": "SHA256 of UTF-8 source bytes with CRLF normalized to LF; outputs hash exact stored bytes",
        "inputs": [{"path": path, "sha256": hashlib.sha256((ROOT/path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()} for path in INPUTS + ["src/export_figures.py"]],
        "selections": {"map_year": 2024, "map_tenure": "Renter", "map_measure": "Percentage of households in core housing need", "national_trend_years": [2020, 2025], "cash_price": 600000, "cash_allowance_pct": 2.5, "saving_quarter": "2025Q4"},
        "figures": [{"id": stem, "title": title, "formats": ["png", "svg"]} for stem, title in FIGURES],
        "files": [],
    }
    for path in sorted(OUT.iterdir()):
        if path.suffix in (".png", ".svg", ".pdf") or path.name == "README.md":
            manifest["files"].append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
    pack = ROOT / "work/CanadianHouseholdFinance-Figures.zip"
    pack.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(pack, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT.iterdir()):
            if path.is_file():
                archive.write(path, path.name)
        for source in INPUTS[1:5]:
            archive.write(ROOT / source, "data/" + Path(source).name)
    print(json.dumps({"files": len(manifest["files"]), "pdf": str(pdf_path), "pack": str(pack), "pack_bytes": pack.stat().st_size}, indent=2), flush=True)
    return manifest

if __name__ == "__main__":
    generate()
