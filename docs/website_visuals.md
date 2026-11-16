# Website map and graphs

The website follows the same question as the audit: **Why does buying a home still feel out of reach?** The map gives regional context. The two graphs explain the national renter budget and the purchase-cash assumptions.

## Provincial map

The measure is the **percentage of renter households in core housing need**, published directly in Statistics Canada table [46-10-0085-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=4610008501). The preserved release is dated September 21, 2026 and contains survey reference years 2018, 2021, 2022 and 2024.

Core housing need combines housing standards and the ability to afford an acceptable local alternative. It is not simply the percentage spending at least 30% of income on shelter. The selected dimension is **households**, not persons, and **Renter**, not all tenures.

Each province uses its published point estimate and published 95% confidence interval. The national comparison uses the source's “Canada (provinces only)” estimate, not a simple average of provinces. Bar ordering does not establish statistically significant differences.

The survey's geographic coverage is the ten provinces. Yukon, the Northwest Territories and Nunavut retain their geometry but have null estimates and an explicit coverage message. No missing value is converted to zero.

The official [Statistics Canada 2021 cartographic boundary service](https://geo.statcan.gc.ca/geo_wa/rest/services/2021/Cartographic_boundary_files/MapServer/0) supplies all 13 province/territory polygons in Statistics Canada Lambert, EPSG:3347. Local Python scales the geometry into a common SVG coordinate system and simplifies it at a 0.55 display-pixel tolerance. Very small islands are omitted for display; every region retains its main polygon. The map is for visualization, not spatial measurement. Source geometry and request parameters are preserved.

The colour scale is fixed at 0–50% across all four survey years. Selection, the comparison bars and a dropdown expose the same figures. Controls support mouse, touch and keyboard. Zooming changes the viewport, not the underlying data.

## National income and consumption graph

The graph reads the existing validated `renter_annual_saving.csv`. Each year sums four quarterly per-household estimates for renter households across Canada. Amounts are nominal CAD, not seasonally adjusted, and represent changing groups.

The graph shows disposable income and consumption. The readout also reports their difference and reported net saving, which includes the pension-entitlement adjustment. None of these is a verified deposit balance or individual bank-account cash flow. The vertical scale starts at CAD 50,000 and is labelled.

This national series does not filter with the provincial map. The survey and national accounts have different definitions and reference periods; their comparison does not establish causation.

## Purchase-cash graph

The controls look up the 30 existing scenarios in `home_purchase_cash_cases.csv`: ten illustrative prices and closing allowances of 1.5%, 2.5% or 4%. The browser does not implement a second version of the financial rules.

Minimum down payment and the assumed closing allowance remain separate. The two line segments preserve the discontinuity at CAD 1.5 million. Scenario prices are not measured provincial home prices. The result does not establish eligibility or a complete closing budget.

The financial rule date remains November 16, 2026. The Power BI release is unchanged; the map is a website addition.

## Reproduce in VS Code

From the project terminal:

```powershell
.\.venv\Scripts\python.exe src/site_visuals.py
.\.venv\Scripts\python.exe -m pytest -q
$env:HOUSEHOLD_FINANCE_VSCODE="1"
node tests/check_website.mjs
```

The browser check uses Node 24 and an installed Chrome or Edge on the local PC. It serves the site on a temporary loopback port, uses a separate headless-browser profile, and saves screenshots and results under ignored `work/`. An optional URL argument checks the published site.

Raw source hashes are in `data/raw/site_visuals/manifest.json`. The derived asset hash is in `data/processed/website_visuals_manifest.json`. All new data preparation and verification for this update ran in the user's local VS Code integrated terminal.

Statistics Canada material is adapted under its [Open Licence](https://www.statcan.gc.ca/en/reference/licence). The website loads its own saved SVG/data assets and needs no map service key.
