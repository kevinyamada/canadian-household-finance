# Project website

Live page: https://kevinyamada.github.io/canadian-household-finance/

GitHub Pages serves the main branch's /docs folder. The site is plain HTML and CSS with no build tools, external fonts, JavaScript, analytics or AI features. The `.nojekyll` file tells Pages to serve the files directly.

- `docs/index.html`: the question, four findings, their source links and the Power BI download.
- `docs/assets/style.css`: responsive layout and print styles.
- The report link points to the tested v1.0.0 PBIX release.
- Evidence links use commit c7316975293c8ba62c1d48c516dafcb86a7286b6 so they match the figures on the page.

This is a published snapshot, not a live data feed. If the analysis is refreshed, review the dates, values, chart scales and wording before editing the page. Update the pinned evidence links and report release together.

To preview locally, open the project in VS Code, run `python -m http.server 8765 --directory docs` in its terminal, then visit http://localhost:8765. Check a narrow phone viewport as well as desktop.

Website checks run locally on the user's PC. The financial analysis does not need to be rerun to edit this page. GitHub Pages only publishes the static files.

## Website validation

The page was checked on the user's Windows PC in a separate headless browser at widths 1440, 768, 390 and 320 pixels. Checks covered the displayed numbers against the saved insight JSON, local navigation, keyboard access, stylesheet loading and horizontal overflow. Desktop and phone screenshots were also reviewed.

This website update changes presentation only. It does not rerun the financial pipeline, replace the Power BI binary or start a paid GPU job. The 32 analysis tests and 71 report-schema checks describe the existing tested analysis release.
