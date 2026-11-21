# GAO enacted earmark data

Verified and retrieved 2026-11-21. This note concerns the GAO series only; it does not equate enacted appropriations with obligations or outlays, and does not assign congressional districts.

## Primary sources and access

- [GAO Tracking the Funds](https://www.gao.gov/tracking-funds) states that its consolidated dataset covers FY2022–FY2024, approximately $39 billion and 20,294 projects; Congress did not designate CPF/CDS funds for FY2025. It says FY2026 information will be added in a later update.
- [GAO report GAO-26-107944](https://www.gao.gov/products/gao-26-107944), published July 16, 2026, distinguishes enacted appropriation amounts from its separately estimated obligations/outlays based on a sample. Those sample estimates are not district measures.
- [Official interactive map](https://files.gao.gov/multimedia/gao-26-107944/interactive/index.html) links the data archive and explains that its own state map allocates multistate projects equally among listed recipient jurisdictions. Our derived data deliberately retain these projects in a separate category rather than making that allocation.
- [Official map-hosted ZIP](https://files.gao.gov/multimedia/gao-26-107944/interactive/GAO_Tracking_the_Funds_data_2022-2024_GAO-26-107944.zip) downloaded successfully (7,172,772 bytes). The equivalent www.gao.gov/assets URL returned HTTP 403 from this machine. Firecrawl retrieval was unavailable because the account had zero credits; the overview/report were read with the web tool and structured files fetched directly.

Archive SHA-256: `6d1edfe1e16b80641ef3d2872550f49ec668cf74b2d1f8ba4ecbcc94dc02c6a4`.

## Raw data retained

`data/raw/gao-2022-2024.zip` preserves the original archive, containing four CSVs and an XLSX workbook. Extracted CSVs retain their original bytes, prefixed `gao-`:

- `gao-1. Overall data.csv`: 20,294 project rows.
- `gao-2. Map - data by location.csv`: 440 rows across the map's different views, years, and denominators. Do not sum these repeated map views.
- `gao-3. Map - data by loc, agency.csv`: 8,360 map-view rows.
- `gao-4. Projects by requester SEE WARNING on XLSX readme tab.csv`: 29,034 project/requester rows. The workbook README warns that projects with several requesters repeat in this table, so it must not be summed for location or agency totals.

The Overall CSV columns are exactly: unnamed row index; `OV_GAO_ID`; `Fiscal Year of Appropriation`; `Period of Availability`; `Appropriations Subcommittee of Jurisdiction`; `Agency`; `Subunit`; `Amount`; `Project/Recipient`; `Location`; `Budget Account Name`; `Budget Account Number`; `Budget Function`; `Requesting Member Info`.

The workbook defines Amount as funds designated for the provision in U.S. dollars, Location as the recipient/project location provided by the joint explanatory statement, and Requesting Member Information as requesters' names and locations. In this CSV the Location strings are states/territories or lists of them; there is no district, street address, latitude, or longitude field. Requester labels include chamber, name, and state, but no congressional district. Do not infer a project district from the requesting representative.

## Derived dashboard file

`dist/data/earmarks.json` contains one project per Overall CSV row, preserves GAO's unique project ID, exact location string, and full requester string, and includes provenance and aggregate totals.

Schema:

```text
metadata: source, source_url, download_url, retrieved_at, zip_sha256,
          measure, geography, aggregation, years
 totals: {amount, projects}
 years[year]: {amount, projects}
 states[exact source location]: {amount, projects, years[year]: {amount, projects}}
 multistate: {amount, projects, years, locations[exact source location]: aggregates}
 projects[]: {id, year, amount, agency, project, location, requesters}
```

`states` includes only single-location strings. The source uses both `VI` and `USVI` (two projects use the latter); both are retained distinctly. An interface joining state contexts should explicitly include the USVI alias for the Virgin Islands or disclose the distinction, without modifying source project labels. `multistate` includes every location containing a comma or ampersand. No multistate amount is also included in `states`.

| Fiscal year | Unique projects | Enacted appropriations |
| --- | ---: | ---: |
| 2022 | 4,963 | $9,064,392,164 |
| 2023 | 7,233 | $15,328,321,787 |
| 2024 | 8,098 | $14,564,834,043 |
| Total | 20,294 | $38,957,547,994 |

Nineteen administering agencies appear across the full period (18 in FY2022). There are 47 multistate projects with $411,412,000, leaving 20,247 single-location projects with $38,546,135,994. GAO's map likewise documents 47 multistate projects, approximately 1.06% of funds.

## Reproduction and checks

Read the Overall CSV with Python's `csv.DictReader(..., encoding='utf-8-sig')`. For each row, map `OV_GAO_ID` to `id`, fiscal year to integer `year`, `Amount` through `decimal.Decimal` to an exact integer dollar value, `Agency` to `agency`, `Project/Recipient` to `project`, `Location` to `location`, and `Requesting Member Info` to `requesters`. Group the unique project records by year. Send every location with `,` or `&` to the multistate category and all other exact strings to `states`; group each category by year too. Never aggregate requester-table rows.

Checks performed: 20,294 distinct nonempty project IDs; exact amount reconciliation against all source rows; 2022/2023/2024 totals sum to the overall total; state and multistate amounts and project counts partition the overall totals; each project's amount is an integer number of dollars. JSON was reloaded and compared against an independently read source CSV after generation.

## Recommended integration

Use this file for an enacted-earmark project explorer with year, state/territory, agency, recipient/project, and requester search. A selected district may display its state's GAO context only if labeled explicitly as statewide context. A district spending choropleth needs independently sourced district geography and obligations data, such as USAspending.

Do not present these GAO amounts as district funding or representative sponsorship totals. A future sponsorship dataset would need a reviewed historical requester-to-district crosswalk for the relevant Congress and separate joint-sponsorship semantics. A project-location district series would require project-level geocoding or verified award links, a boundary vintage, and an explicit treatment of regional/multidistrict projects. Neither is derived here.
