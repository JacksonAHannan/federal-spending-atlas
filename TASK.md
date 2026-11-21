# Federal Spending Atlas

Goal: deliver an interactive congressional district dashboard on GitHub Pages using verified federal data.
Non-goals: representative credit inferred from award totals, invented earmark locations, all federal expenditures.
Constraints: preserve unrelated projects; GitHub publication authorized by the user on November 21, 2026; retain raw source data and reproducible transforms.

## Design
Palette: ink #142f44, ocean #146b85, water #eaf3f7, mint #8cd4c0, white #ffffff, caution #9a5800. Arial/Helvetica throughout, following the user’s common-font preference. Map is the main canvas, with ranked district list and selected district inspector. Spacious light blue cartographic workspace, restrained navy chrome. No decorative metric cards; statistics form one horizontal ledger. This is a data exploration tool, so map and filters lead rather than a marketing hero.

## Checklist
- [x] Verify USAspending geography endpoint, aggregation semantics, geographic vintage, and fetch real annual grant/contract snapshots.
- [x] Obtain official boundary geometry, preserve original data and identifiers.
- [x] Investigate GAO earmark data and integrate only defensible measures; disclose any access or geographic limitation.
- [x] Implement responsive map, fiscal year/award filters, district search/select, rankings, district breakdowns, downloads, sources/methodology.
- [x] Validate data joins/reconciliation and browser interactions on desktop/mobile; review screenshots.
- [x] Document run/refresh instructions and final evidence.

Completion: working local app with real data, clear metric definitions and source links, no silent mismatches, reproducible refresh, checks passing.

## Follow-up: GitHub publication and usability

User authorized GitHub hosting/sharing and requested usability research, less copy, and common fonts. Applied USWDS/W3C guidance, Arial/Helvetica, compact copy, and static direct API calls for GitHub Pages. Public federal data only; no private credentials or unrelated files.

- [x] UI research and cleanup; source notes in research/ui-principles.md.
- [x] Exact raw/derived data reconciliations and focused logic tests pass.
- [x] Desktop/mobile browser checks pass, including live CORS API requests.
- [x] Create new GitHub repository, push reviewed source, enable Pages, verify deployed URL and browser behavior.

Completed: https://jacksonahannan.github.io/federal-spending-atlas/
Source: https://github.com/JacksonAHannan/federal-spending-atlas

Published gh-pages commit b3cf8772d60d4686d4aac6b8c812648a1bcf2d8f. GitHub Pages reports built; HTTP 200. Deployed index, JavaScript, stylesheet, D3, spending, GAO, and boundary assets match local SHA-256 hashes. Full browser interaction checks pass against the hosted project subpath, including direct live API requests and 390px mobile layout. Four focused logic tests and all source reconciliation checks pass. No JavaScript errors.

Historical availability question documented in research/historical-coverage.md; implemented coverage was not changed. Remaining limits: GAO does not support project district attribution; snapshots are not automatically refreshed; live top-six lists can reflect later source revisions. No blockers.

## Copy removal and outlay availability

User requested removal of the inline obligation/influence explanation and asked whether actual-payment data exist. Removed the full inline note, redundant Details button, dead event-handler reference, and unused styling. Kept table spacing. Outlays verified through official guidance and a read-only API probe; findings in research/outlays.md. The existing map remains an obligations series.

- [x] Verify removal and remaining navigation/filter behavior in browser.
  Evidence: managed local preview passes 441-path render, AL filters/search, both About links/Escape, and mobile overflow checks with no JavaScript errors. Node syntax and git whitespace checks pass. Initial preview process exited before connection; rerun used the server lifecycle helper and passed.
- [x] Push and republish to the existing GitHub Pages site; verify hosted result.
  Evidence: Pages reports built for f2a0195090d82234e12ea490dfe8b657aec0d9b8. Hosted browser removal/navigation/filter/mobile checks pass; deployed HTML, JS, and CSS hashes match local files.

## Payments and five congressional cycles

Goal: add actual reported payments alongside obligations; add five two-year congressional cycle views and their combined total. User confirmed two-year congressional cycles. Preserve the compact Arial/Helvetica interface and the requested removal of inline explanatory prose.

Period design: 115th–119th Congress calendar-year reporting cycles (2017–18, 2019–20, 2021–22, 2023–24, 2025–26), explicitly labeled with dates. Financial payments are monthly reports, so cycle reporting uses Jan 1–Dec 31 rather than the Jan 3 swearing-in boundary. Current cycle is through available reported data and must be marked to date. Earlier optional payment-reporting years must be distinguished from mandatory FY2022+ coverage. Keep current-district map geography consistent.

Non-goals: assigning GAO projects to districts; using lifetime outlays as annual payments; claiming historical payment coverage is complete; claiming congressional-cycle dollars are a member's influence.

- [x] Verify feasible File C extraction and year/month aggregation without cumulative double counting; retain source manifest and reconciliation evidence.
- [x] Load payment data and cycle obligations; validate joins and amount partitioning, including unmapped and unlinked records.
- [x] Extend existing filters/map/rankings/exports and district trends with Payments / Obligations, cycle totals, and combined five-cycle view. Keep agency/program detail aligned or explicitly unavailable for unsupported measure.
- [x] Add focused aggregation/data tests, browser-check desktop/mobile views and downloads; update method/run documentation.
- [x] Republish GitHub Pages and verify deployed behavior and asset hashes.

Research delegation: bounded independent API feasibility investigation owns research/annual-outlays-api.md and data/raw/outlay-research-*; parent owns data pipeline, UI, integration, checks and publication.

User clarification: keep congressional calendar-year cycles, even when the earliest payment cycle is unavailable. FY2017P03 did not exist; using FY2017P12 without its missing opening-quarter baseline would wrongly include possible Oct–Dec2016 payments. Therefore 2017–2018 payments are null/unavailable, not zero. Combined payments cover only the four measurable cycles (2019–2026), labeled explicitly. Combined obligations cover all five cycles. National annual exports subsequently finished successfully despite NRC diagnostics failing; the national route has been independently audited.

Checkpoint: all ten cycle-obligation API responses are saved and build_cycles.py has added five cycles plus the combined total to spending.json. National File C exports work (the NRC abbreviation tests failed); FY2017 independently audited complete: 2,625,901 CSV rows across four split files, only FY2017Q4 has non-null period-end outlays, archive SHA matches. Exact grant/contract vs other/unlinked and mapped vs unmapped reconciliations are enforced in build_outlays.py. All fourteen national snapshot requests are queued. Aggregates through FY2020 are complete; later reports are being processed by `.venv/bin/python scripts/build_outlays.py --wait` (resumable manifests, HTTP Range resumes, ignored archives in data/downloads). The original Python CSV loop processed FY2020's 90,978,282 rows; the remaining ingestion uses PyArrow 26.0.1 batch CSV with decimal128 and a tested standard-library fallback. No payments are synthesized. New tests cover split files, legitimate repeated award rows, negatives, null historical reporting snapshots, unmatched districts, and calendar-quarter telescoping.

UI checkpoint: Payments/Obligations measure selector, fiscal/cycle period selector, Cycles navigation, five-row cycle table, combined views, aligned amount labels, CSV metadata, and on-demand payment agency/program detail implemented. Real cumulative paid snapshot ($2.54T mapped) renders and cycle obligation comparison renders on desktop/mobile with no JS errors. Annual payment output not yet assembled, so final acceptance/browser run is pending. Updated payment assembler must be re-run after all source aggregates exist (the older ingestion process was replaced by the current version). It explicitly nulls cycle115, has no five-cycle payment total, and produces an available_cycle_total for2019–2026. Source detail is split into per-period on-demand files, to keep initial payload small.

Accepted implementation: all fourteen national financial exports finished. All 462,491,832 CSV rows processed, exact annual ledgers reconcile mapped + unmatched and eligible + other/unlinked amounts. Earlier optional-reporting years remain labeled. Annual FY2022–2026, four measurable calendar cycles, four-cycle payment total, cumulative payments, five obligation cycles, and five-cycle obligation total are loaded. First 2017–2018 payments remain null and export as missing. Initial data payload remains compact; payment detail is loaded per period on demand. Asset/data version queries protect returning browsers from mixing old JSON/module schemas.

Verification: 8 Node logic tests and 3 financial-parser fixtures pass; complete data checks pass for fourteen source ledgers, their selected period masks, all annual/cycle arithmetic, independent 2017 hash audit, first-quarter gap, cumulative-outlay field selection and combined agency rankings. Desktop/390px browser checks pass annual/cumulative payments, cycle navigation, unavailable CSV fields, actual payment detail, obligation request dates, map controls, GAO search and dialogs; no JS errors. Publication is next.

Published and verified: main implementation 1b2e8ec; GitHub Pages commit 42d9380fa8840bf43937db9ce8c0ba07b0493127 reports built. Full browser checks pass against https://jacksonahannan.github.io/federal-spending-atlas/?v=20261121-payments-cycles, including annual/cumulative payments, cycle comparisons, first-cycle missing CSV values, period-aligned detail, mobile and navigation. All 17 changed hosted HTML/JS/CSS/data/detail assets match local SHA-256 hashes. Final source and working tree reconciled; no remaining blockers. Original File C archives retained in ignored data/downloads (6.8 GiB); exact source ledgers and provenance are tracked in GitHub.
