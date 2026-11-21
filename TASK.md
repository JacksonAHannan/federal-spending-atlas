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
- [ ] Create new GitHub repository, push reviewed source, enable Pages, verify deployed URL and browser behavior.

Next action: publish the verified static dist/ through GitHub Pages.
