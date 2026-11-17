# Source refresh: what is current, and what is not?

Checked 2026-11-17 in desktop VS Code.

| Input | Published period used | Treatment |
|---|---|---|
| Statistics Canada city buyer transactions and family income | 2023 | Latest comparable buyer release reviewed; matched historical baseline retained |
| Residential-property stock in that release | 2024 | Not relabeled as the sales year |
| Insured fixed mortgages, five years and over, funds advanced | 2026-09: 4.15% | Latest common published monthly observation |
| Uninsured equivalent | 2026-09: 4.66% | Same month, same lending concept |
| Municipal property-tax rates and cost assumptions | Original 2023 schedule and explicit profile assumptions | Held fixed; not a current property bill |

Statistics Canada's release dated 2026-08-26 combines property-stock information for 2024 with home-sale and buyer information for 2023. A newer webpage date does not make the transactions newer.

**Retrieval limit:** Official release reviewed on 2026-11-17. Desktop WDS metadata and download-info requests returned HTTP 403; the existing checksummed historical extract was not re-downloaded or certified free of revisions.. The earlier extract remains checksummed; no claim is made that revisions were re-downloaded. The latest-rate JSON files were downloaded successfully from Bank of Canada Valet, then checked for series identity, duplicate months, future dates, common coverage and checksums.

## What the newer rates change

For the Vancouver two-earner example at the unchanged CAD 849,000 price, required income changes from **CAD 190,014** to **CAD 175,293**. Monthly mortgage payment changes from **CAD 4,742** to **CAD 4,303**. The result is **income still short**.

This is a rate sensitivity on old prices and unchanged finances. It cannot establish current affordability: prices, taxes, costs and buyer finances would also need updating. The 2026 monthly rate is not an annual average and is not an available offer for a particular applicant.

- [Statistics Canada table](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=4610009901)
- [Release explaining the reference years](https://www150.statcan.gc.ca/n1/daily-quotidien/260826/dq260826b-eng.htm)
- [Bank of Canada lending-rate table](https://www.bankofcanada.ca/rates/banking-and-financial-statistics/interest-rates-for-new-and-existing-lending-by-chartered-banks/)
- [Checksummed refresh sources](../data/raw/homebuying_refresh/manifest.json)
- [Nine latest-rate examples](../data/processed/homebuying_latest_rates.csv)
