# Federal Spending Atlas

Goal: deliver a local interactive congressional district dashboard using verified federal data.
Non-goals: representative credit inferred from award totals, invented earmark locations, all federal expenditures.
Constraints: preserve unrelated projects; GitHub publication authorized by the user on November 21, 2026; retain raw source data and reproducible transforms.

## Design
Palette: ink #142f44, ocean #146b85, water #eaf3f7, mint #8cd4c0, white #ffffff, caution #9a5800. System sans for controls; Georgia display headline. Map is the main canvas, with ranked district list and selected district inspector. Spacious light blue cartographic workspace, restrained navy chrome. No decorative metric cards; statistics form one horizontal ledger. This is a data exploration tool, so map and filters lead rather than a marketing hero.

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
- [ ] Push and republish to the existing GitHub Pages site; verify hosted result.
