# Federal Spending Atlas

[Open the dashboard](https://jacksonahannan.github.io/federal-spending-atlas/)

Interactive congressional district map of **federal prime grant and contract net obligations**, FY2022–FY2026. Includes a separate searchable compilation of **20,294 enacted GAO earmark projects**, FY2022–FY2024.

The interface uses Arial/Helvetica, concise controls, a searchable ranking table, CSV exports, and a responsive map. See [usability research](research/ui-principles.md).

## Run locally

No frontend build or runtime packages are required. Python 3 and a current browser are sufficient:

```bash
python server.py --port 8765
```

Open http://localhost:8765. Any static HTTP server can serve `dist/`; opening `index.html` directly through `file://` is unsupported.

The hosted site uses the identical static files. Optional agency/program details call the public USAspending API directly over HTTPS, without a key. All saved map and earmark data remain usable when that API is unavailable. Nothing is sent to a private backend. Filters and selections stay in browser memory; no analytics or tracking are installed.

## What the numbers mean

- **Map:** transaction-level net obligations, using award types A–D (contracts) and 02–05 (grants), grouped by primary place of performance. Deobligations remain negative. Fiscal years run October 1–September 30. Salaries, loans, direct payments, and subawards are outside scope.
- **Geography:** USAspending derived current district identifiers joined to Census 2025 cartographic boundaries for the 119th Congress. Includes 435 voting districts and 6 delegate/resident-commissioner areas. Historical values are not original-year district comparisons. Unmatched endpoint rows remain separate and appear in nationwide CSV exports; state-filtered exports exclude national unmatched rows.
- **Per resident:** obligations divided by the reference population returned by USAspending, whose vintage is not provided in the response. These are not annual population estimates.
- **Earmarks:** enacted appropriations, not obligations or payments. One project per unique GAO ID. GAO provides state-level location strings, not project district identifiers. Multi-location projects remain separate. Requesters are shown without inferring district sponsorship totals.
- **Live details:** top six agencies, grant assistance programs, and/or contract industries, depending on award-type selection. Retrieved on demand; later revisions can differ from map snapshots. Category top-six lists are not a complete reconciliation.

USAspending snapshots and GAO files were retrieved November 21, 2026. FY2026 is recently closed and subject to reporting revisions. Refreshing data is explicit; no scheduled updates are enabled.

## Sources and reproduction

- [USAspending geography API](https://api.usaspending.gov/api/v2/search/spending_by_geography/) and [endpoint contract](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/api_contracts/contracts/v2/search/spending_by_geography.md)
- [Census boundaries](https://www2.census.gov/geo/tiger/GENZ2025/shp/cb_2025_us_cd119_500k.zip)
- [GAO Tracking the Funds](https://www.gao.gov/tracking-funds) and [official dataset archive](https://files.gao.gov/multimedia/gao-26-107944/interactive/GAO_Tracking_the_Funds_data_2022-2024_GAO-26-107944.zip)

Original downloads, request filters, responses, retrieval timestamps, and extracted GAO CSVs are preserved in `data/raw/`. SHA-256 evidence is in [source-hashes.json](research/source-hashes.json). Derived browser data live in `dist/data/`.

```bash
# Data refresh needs requests; tests use Playwright only for browser checks.
uv venv .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
.venv/bin/python scripts/refresh_data.py --force

# Rebuild GAO JSON from the preserved official Overall CSV.
python scripts/build_earmarks.py

# Rebuild display boundaries from preserved Census ZIP; requires GDAL.
python scripts/build_boundaries.py
```

`refresh_data.py` defaults to preserved responses unless `--force` is passed. It fetches five complete fiscal-year ranges and two disjoint award-type groups, saves original responses, then rebuilds the derived snapshot. Rebuilding geometry uses a 0.006-degree simplification and five decimal places for small-scale thematic display; it is not suitable for address assignment or legal boundaries. GDAL may report coordinate-operation selection warnings converting NAD83 to WGS84; this is a display-only transformation, not a geocoding workflow.

See [USAspending findings](research/data-method.md) and [GAO source/schema findings](research/earmarks.md). The other databases in the initial brief are linked as context in the dashboard, not blended with official GAO totals.

## Verification

```bash
node --check dist/app.mjs
node --test tests/core.test.mjs
python tests/data_check.py
# With the local server running and Chromium installed:
.venv/bin/python tests/browser_check.py
```

Data checks reconcile all 441 district joins across five years, ten source responses, an independent combined-type API response for FY2025, and all 20,294 GAO project records. Browser checks cover filters, search, selections, exports, live API details, earmark search, dialog dismissal, zoom/reset, and mobile overflow. Screenshots are kept locally in `research/` and ignored in Git.

## GitHub Pages

GitHub Pages publishes the `gh-pages` branch, containing only `dist/`. The complete source and raw evidence remain on `main`. All asset paths are relative, so project-site subpaths work without rewriting. Before publishing an update, run the verification commands above, commit the source on `main`, push `main`, then run `git subtree push --prefix dist origin gh-pages`. This uses branch-based Pages deployment and requires no manually configured secrets or server.

Third-party code: D3 7.9.0 is vendored under its ISC license in `dist/vendor/`. Government records retain their source attribution. This is an independent dashboard, not a U.S. government website.
