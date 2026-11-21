# Annual district outlays: verified retrieval route

Investigated November 21, 2026. Primary evidence is the official USAspending API contracts and implementation; narrow copies are preserved as `data/raw/outlay-research-*`.

## Result

The verified retrieval route is **Custom Account Data, File C (Account Breakdown by Award), federal-account level**, selecting only the needed columns. It supplies fiscal-year-to-date outlays and derived current place-of-performance congressional districts in one download, so no full database restore is needed. Use fiscal-year end (period 12) for annual totals, and period 3 for December calendar-year cutoffs. Missing or optional reporting must remain explicitly incomplete.

The [account download contract](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/api_contracts/contracts/v2/download/accounts.md) supports `fy`, `period` (2–12), `quarter` (1–4), `submission_types: ["award_financial"]`, agency, and selected `columns`. It does not expose arbitrary district or award-type filters: filter those locally after the download.

Verified national request (FY2017 export finished and its complete ZIP was independently audited):

```json
{
  "account_level": "federal_account",
  "file_format": "csv",
  "filters": {
    "fy": "2017",
    "period": "12",
    "submission_types": [
      "award_financial"
    ],
    "agency": "all"
  },
  "columns": [
    "submission_period",
    "award_type_code",
    "prime_award_summary_place_of_performance_cd_current",
    "gross_outlay_amount_FYB_to_period_end",
    "award_unique_key",
    "awarding_agency_name",
    "cfda_number",
    "cfda_title",
    "naics_code",
    "naics_description"
  ]
}
```

For national snapshots set agency to `all`. Additional supported columns include `primary_place_of_performance_country`, `primary_place_of_performance_state`, `awarding_agency_code`, `awarding_agency_name`, `funding_agency_code`, `funding_agency_name`, `cfda_number`, `cfda_title`, `naics_code`, and `naics_description`. [Official File C download implementation](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/download/delta_downloads/award_financial.py) and [column mappings](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/download/v2/download_column_historical_lookups.py).

## Avoiding double-counting

The federal-account File C export contains year-to-date rows from multiple submission periods (hence filename P01–P12), but its `gross_outlay_amount_FYB_to_period_end` aggregation calls `filter_submission_and_sum`, selecting submission IDs appropriate to the requested cutoff. Prior-period rows therefore have no outlay contribution. This differs from transaction obligations, which are summed across the selected periods. [File C aggregator](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/download/delta_downloads/award_financial.py), [sum helper](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/common/spark/utils.py).

`get_submission_ids_for_periods` selects the latest requested month or quarter per reporting agency and explicitly handles agencies switching between quarterly and monthly submissions, so the same agency's quarterly and monthly cumulative reports do not both enter the outlay total. Only publicly revealed reporting windows qualify. [Submission selection source](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/submissions/helpers.py).

**Do not deduplicate by award ID or by identical selected CSV rows.** One award can have distinct federal-account/program-activity/object-class/DEFC financial entries; those are additive. Reducing selected columns can make distinct source groups look identical. Aggregation should preserve all returned row contributions, skip null outlays, retain negative adjustments, and partition mapped vs unmapped/foreign/unlinked records rather than allocate them by assumption.

The field is fiscal-year-to-date, mapped from File C `gross_outlay_amount_by_award_cpe`. [Output derivation](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/download/delta_models/award_financial_download.py). Submission-period values are `FY2025P12` for monthly reports or `FY2025Q4` for quarterly reports. [Formatter](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/download/helpers/delta_models_helpers.py).

## Why the alternatives do not work

- Ordinary search-geography `spending_level: awards` returns cumulative award `total_outlays`, not annual payment totals.
- Category search `spending_level: award_financial` is explicitly implemented only for DEFC; district categorization raises not implemented. [Source validation](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/search/v2/views/spending_by_category_views/spending_by_category.py).
- Disaster geography aggregates the award's nested cumulative DEFC outlays, intersects filters with COVID DEFCs, and has no fiscal-year payment filter. It is not a general federal payments endpoint. [Disaster geography source](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/disaster/v2/views/spending_by_geography.py) and [base filters](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/disaster/v2/views/disaster_base.py).

## Availability and operation

USAspending states that monthly award-level outlay reporting became mandatory in FY2022, with earlier reporting generally optional except COVID awards from April 2020. DATA Act account reports begin during FY2017; a fiscal-year/calendar-cycle calculation extending that early is incomplete and must not impute missing cutoffs as zero. [Analyst guide](https://www.usaspending.gov/federal-spending-guide).

The API initially returned a download job and `status: ready`, but **ready means queued, not finished**. The generated file URL then returned an HTTP403 HTML wait page whose script explicitly describes `ready` and `running` as unfinished. Poll the status URL until `finished`; only then download the ZIP. Preserve the response, generated URL, original ZIP, and derived amount partitions. Narrow selected columns reduce downloaded bytes but the service can still take time to scan and generate account data.

Small-probe creation and status evidence: `data/raw/outlay-research-probe-request.json` and `data/raw/outlay-research-probe-status.json`. The NRC FY2025 federal-account job advanced from ready to running, then failed after 166.60 seconds with generic message "An error occurred." No CSV was produced. Two diagnostic variants also failed: treasury-account selected columns after 166.40 seconds and federal-account default columns after 172.31 seconds, each with the same generic message. No CSV was produced by any of the three jobs. This does not isolate the upstream cause, but it rules out selected columns or federal-account grouping alone. All three used the documented agency abbreviation NRC. A numeric-agency variant was attempted after discovering internal NRC agency ID 554, but the API closed the connection before creating a job. These agency-specific failures do **not** block national exports: the parent’s national requests subsequently finished. The exact reason for the NRC failures is unconfirmed.

## Related upstream reports

The official repository has an [open account-download failure report (#4124)](https://github.com/fedspendingtransparency/usaspending-api/issues/4124). A [separate August 2026 download failure (#4731)](https://github.com/fedspendingtransparency/usaspending-api/issues/4731) was attributed by a maintainer to an API deploy and later reported fixed. These are context, not evidence that the current failure has the same cause. No upstream issue was filed and no messages were sent externally.

## Verified fallback: reported payments to date

Two successful geography requests omitted the time-period filter entirely and requested `spending_level: awards`, `scope: place_of_performance`, `geo_layer: district`, and **only** the appropriate award-type list. Their `total_outlays` values are actual reported payments accumulated to date; `aggregated_amount` is obligations and must not be used for this view. These are not annual or cycle payment totals.

- `data/raw/outlay-research-lifetime-contracts.json`: contracts A/B/C/D.
- `data/raw/outlay-research-lifetime-grants.json`: grants 02/03/04/05.
- `data/raw/outlay-research-lifetime-validation.json`: independent Decimal sums and geography checks.

Each response contains 441 unique matching district GEOIDs plus one blank identifier whose outlays are zero. All mapped district outlays are nonzero in these responses. One contract district has a negative net reported value and is retained. An API aggregate of zero generally cannot establish whether a missing report or actual zero payment is responsible; the response does not supply reporting completeness flags.

- Contracts total_outlays across all returned rows: $1153877806252.20; fetched 2026-11-21T21:05:47.723646+00:00.
- Grants total_outlays across all returned rows: $1384012395850.09; fetched 2026-11-21T21:05:23.588403+00:00.

This snapshot can support a separate “Reported payments to date” view. It must never be treated as an annual/cycle payment total. The annual File C exports described above are the appropriate source for fiscal-year and derived calendar-cycle payments.

## Independent audit of completed national FY2017 export

The parent’s national FY2017 and FY2018 federal-account selected-column requests finished. HEAD responses confirmed ZIP sizes of 38,790,998 and 50,107,014 bytes respectively, consistent with the status response's size values in kilobytes. The FY2017 ZIP was independently downloaded and read in full, then the duplicate copy was removed only after confirming that the parent’s preserved archive in `data/downloads/` had the identical SHA-256.

FY2017 source SHA-256: `1c8d2d84bdc6386a5aca4b07a63ce035a40127fa135e6cb4d3fa6aebcf544508`.

The export has **four CSVs**, not merely one per category: Assistance is split across two files, plus Contracts and Unlinked. All CSVs must be processed. Their combined row count is exactly 2,625,901, matching the download status. All ten requested column headers matched exactly.

- Assistance part 2: 680,053 rows; all-award-type outlay sum $9,909,580,223.74; 410,615 null-outlay rows.
- Assistance part 1: 680,054 rows; all-award-type outlay sum $9,957,520,779.22; 410,819 null-outlay rows.
- Contracts: 627,506 rows; all-award-type outlay sum $473,787,924.21; 527,628 null-outlay rows.
- Unlinked: 638,288 rows; all-award-type outlay sum $12,577,704.53; 580,707 null-outlay rows.

Every non-null outlay in this FY2017 P12 request appears in `FY2017Q4`; earlier FY2017Q2/Q3 rows carry null outlays. This independently verifies the source cutoff-masking logic. Non-null **zero** outlays are common, and small early-year outlay totals do not establish complete reporting: FY2017 preceded the later mandatory award-outlay regime. Assistance contains more than grants; the parser must filter award types 02–05 for the dashboard grant measure, and A–D for contracts. Other award types, unlinked entries, and unmappable geography need separate reconciliation buckets. Negative amounts remain in the sums.

Machine-readable audit: `data/raw/outlay-research-national-fy2017-p12-audit.json`. This is independent source verification of FY2017; later national downloads still need their own parsing/reconciliation checks.
