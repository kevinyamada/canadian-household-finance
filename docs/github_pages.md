# Project website

https://kevinyamada.github.io/canadian-household-finance/

GitHub Pages serves the main branch's /docs folder. The page follows one housing-readiness audit, with the saving evidence, purchase-cash assumptions, source links and Power BI download.

- `docs/index.html`: content and accessible navigation.
- `docs/assets/style.css`: responsive light/dark styles and print styles.
- `docs/assets/theme.js`: the small theme button. Fresh visits start in light mode, regardless of the system setting. A visitor’s explicit choice is remembered in local storage.
- The main report download is the focused v2.0.0 PBIX.
- The site has no analytics, external font requests or client-side financial calculations.

The page is a published snapshot. After a source or rule update, review the figures, dates, assumptions and report release together.

Preview from VS Code with `python -m http.server 8765 --directory docs`, then visit http://localhost:8765. Website checks run in the user's local VS Code terminal and cover desktop/phone widths, both themes, reload persistence, navigation and agreement with the saved audit summary.
