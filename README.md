# Federal Spending Atlas

[Open the dashboard](https://jacksonahannan.github.io/federal-spending-atlas/)

Interactive congressional district map of **federal grant and contract payments and obligations**, with annual FY2022–FY2026 views and five two-year congressional reporting cycles (2017–2026). Includes a separate searchable compilation of **20,294 enacted GAO earmark projects**, FY2022–FY2024.

The interface uses Arial/Helvetica, concise controls, a searchable ranking table, CSV exports, and a responsive map. See [usability research](research/ui-principles.md).

## Run locally

No frontend build or runtime packages are required. Python 3 and a current browser are sufficient:

```bash
python server.py --port 8765
```

Open http://localhost:8765. Any static HTTP server can serve `dist/`; opening `index.html` directly through `file://` is unsupported.

The hosted site uses the identical static files. Obligation agency/program details call the public USAspending API directly over HTTPS, without a key. Payment agency/program details load from precomputed financial-report data on demand. All saved map and earmark data remain usable when that API is unavailable. Nothing is sent to a private backend. Filters and selections stay in browser memory; no analytics or tracking are installed.

## What the numbers mean

- **Payments (default):** reported fiscal-year-to-date gross outlays from File C federal-account exports. The pipeline counts the selected period-end submission once, preserves legitimate repeated financial rows and negative adjustments, filters to grants 02–05 and contracts A–D, and separates unlinked, other-type, and unmapped amounts. Annual FY2022–FY2026 totals use fiscal period 12. [Detailed source and arithmetic](research/annual-outlays-api.md).
- **Obligations:** transaction-level net obligations, using the same grant/contract type codes and primary place of performance. Negative changes remain in totals. Salaries, loans, direct payments, and subawards are outside both measures.
- **Congressional cycles:** calendar reporting years corresponding to the 115th–119th Congresses: 2017–2018, 2019–2020, 2021–2022, 2023–2024, and 2025–2026 through September 30. These use January 1 reporting boundaries, not the January 3 swearing-in instant. The five-cycle obligation total covers January 1, 2017–September 30, 2026. Payment cycles use year-end fiscal reports minus their opening fiscal quarter plus their closing fiscal quarter. **2017–2018 payments are unavailable**, because FY2017's opening-quarter report did not exist. The combined payment view therefore covers only the four measurable cycles (2019–2026), labeled explicitly. Earlier optional-reporting cycles are marked partial reporting; missing values never become zero.
- **All reported payments:** a separate cumulative-to-date view from the search-geography API's `total_outlays`, with no award-date filter. It is not substituted for annual payments. `aggregated_amount` in that API mode is obligations, not payments.
- **Geography:** USAspending derived current district identifiers joined to Census 2025 cartographic boundaries for the 119th Congress. Includes 435 voting districts and 6 delegate/resident-commissioner areas. Historical values are not original-year district comparisons. Unmatched endpoint rows remain separate and appear in nationwide CSV exports; state-filtered exports exclude national unmatched rows.
- **Per resident:** the selected amount divided by the reference population returned by USAspending, whose vintage is not provided in the response. These are not annual population estimates.
- **Earmarks:** enacted appropriations, not obligations or payments. One project per unique GAO ID. GAO provides state-level location strings, not project district identifiers. Multi-location projects remain separate. Requesters are shown without inferring district sponsorship totals.
- **Details:** top six agencies, grant assistance programs, and/or contract industries for the selected measure, period, and award types. Payment rankings are computed after period arithmetic, with a combined agency ranking calculated before truncation. Obligation rankings are fetched live and can reflect later revisions. These lists are not complete category reconciliations.

USAspending snapshots and GAO files were retrieved November 21, 2026. FY2026 is recently closed and subject to reporting revisions. Refreshing data is explicit; no scheduled updates are enabled.

## Sources and reproduction

- [USAspending geography API](https://api.usaspending.gov/api/v2/search/spending_by_geography/) and [endpoint contract](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/api_contracts/contracts/v2/search/spending_by_geography.md)
- [Census boundaries](https://www2.census.gov/geo/tiger/GENZ2025/shp/cb_2025_us_cd119_500k.zip)
- [GAO Tracking the Funds](https://www.gao.gov/tracking-funds) and [official dataset archive](https://files.gao.gov/multimedia/gao-26-107944/interactive/GAO_Tracking_the_Funds_data_2022-2024_GAO-26-107944.zip)

Request filters, responses, retrieval timestamps, exact financial-source ledgers, and extracted GAO CSVs are preserved in `data/raw/`. Original large File C ZIPs are retained locally in ignored `data/downloads/`, with official URLs, byte counts, and SHA-256 hashes recorded in the tracked source ledgers. All 462,491,832 CSV rows across fourteen financial exports were processed; all split CSVs in each ZIP are included. These ZIPs are excluded from Git because individual files exceed GitHub’s file-size limit. SHA-256 evidence is in [source-hashes.json](research/source-hashes.json). Derived browser data live in `dist/data/`.

```bash
# Data refresh needs requests; tests use Playwright only for browser checks.
uv venv .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
.venv/bin/python scripts/refresh_data.py --force

# Queue/resume official financial exports; keep recorded job IDs and wait for finished.
.venv/bin/python scripts/build_outlays.py --wait
# Rebuild browser data from completed financial source ledgers without network calls.
.venv/bin/python scripts/build_outlays.py --assemble

# Rebuild GAO JSON from the preserved official Overall CSV.
python scripts/build_earmarks.py

# Rebuild display boundaries from preserved Census ZIP; requires GDAL.
python scripts/build_boundaries.py
```

`refresh_data.py` defaults to preserved responses unless `--force` is passed. It fetches five complete fiscal-year ranges and two disjoint award-type groups, saves original responses, then rebuilds the derived snapshot and cached calendar-cycle queries. `build_cycles.py` owns the five cycle definitions. Financial ingestion uses streamed ZIP members and Arrow batches with exact decimal128 currency; a standard-library reader remains available for small inputs. It resumes recorded download jobs and partial HTTP transfers rather than re-requesting completed source files. Run `--assemble` after new ledgers are ready. Monthly award-outlay reporting was optional before FY2022; retrieval does not make those older records complete. Rebuilding geometry uses a 0.006-degree simplification and five decimal places for small-scale thematic display; it is not suitable for address assignment or legal boundaries. GDAL may report coordinate-operation selection warnings converting NAD83 to WGS84; this is a display-only transformation, not a geocoding workflow.

See [USAspending findings](research/data-method.md) and [GAO source/schema findings](research/earmarks.md). The other databases in the initial brief are linked as context in the dashboard, not blended with official GAO totals.

## Verification

```bash
node --check dist/app.mjs
node --test tests/core.test.mjs
python tests/data_check.py
.venv/bin/python tests/outlays_pipeline_test.py
# With the local server running and Chromium installed:
.venv/bin/python tests/browser_check.py
```

Data checks reconcile all 441 district joins across five annual obligation views, ten cycle responses, fourteen financial-source ledgers, cumulative payment fields, annual and calendar-quarter payment arithmetic, four-cycle payment totals, five-cycle obligation totals, linked agency rankings, an independent combined-type FY2025 response, and all 20,294 GAO project records. Focused fixtures cover split CSVs, projected duplicate rows, null prior-period outlays, negative adjustments, and missing opening-quarter coverage. Browser checks cover filters, search, selections, exports, live API details, earmark search, dialog dismissal, zoom/reset, and mobile overflow. Screenshots are kept locally in `research/` and ignored in Git.

## GitHub Pages

GitHub Pages publishes the `gh-pages` branch, containing only `dist/`. The complete source and raw evidence remain on `main`. All asset paths are relative, so project-site subpaths work without rewriting. Before publishing an update, run the verification commands above, commit the source on `main`, push `main`, then run `git subtree push --prefix dist origin gh-pages`. This uses branch-based Pages deployment and requires no manually configured secrets or server.

Third-party code: D3 7.9.0 is vendored under its ISC license in `dist/vendor/`. Government records retain their source attribution. This is an independent dashboard, not a U.S. government website.
