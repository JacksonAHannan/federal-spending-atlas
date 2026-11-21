"""Build district payments from fiscal-year-to-date File C reports, not award lifetime totals.

Queue once, resume the recorded jobs, stream CSVs, and preserve exact Decimal reconciliations.
Large original ZIPs stay in ignored data/downloads/; source URLs/hashes and aggregates are tracked.
"""

import argparse, collections, csv, datetime, hashlib, io, json, pathlib, shutil, time, zipfile
from decimal import Decimal
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SESSION = requests.Session()
SESSION.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=4,
            connect=4,
            read=3,
            status=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
    ),
)
from build_cycles import CYCLES
from financial_csv import financial_rows

ROOT = pathlib.Path(__file__).resolve().parents[1]
API = "https://api.usaspending.gov/api/v2/download/accounts/"
TYPES = {"contracts": {"A", "B", "C", "D"}, "grants": {"02", "03", "04", "05"}}
COLUMNS = [
    "submission_period",
    "award_type_code",
    "prime_award_summary_place_of_performance_cd_current",
    "gross_outlay_amount_FYB_to_period_end",
    "award_unique_key",
    "awarding_agency_name",
    "cfda_number",
    "cfda_title",
    "naics_code",
    "naics_description",
]
SNAPSHOTS = [(y, 12) for y in range(2017, 2027)] + [
    (y, 3) for y in [2019, 2021, 2023, 2025]
]


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def key(year, period):
    return f"fy{year}-p{period:02}"


def manifest_path(year, period):
    return ROOT / f"data/raw/outlays-{key(year, period)}-request.json"


def aggregate_path(year, period):
    return ROOT / f"data/raw/outlays-{key(year, period)}-aggregate.json"


def save(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def queue(year, period):
    path = manifest_path(year, period)
    if path.exists():
        return json.loads(path.read_text())
    body = {
        "account_level": "federal_account",
        "file_format": "csv",
        "filters": {
            "fy": str(year),
            "period": str(period),
            "submission_types": ["award_financial"],
            "agency": "all",
        },
        "columns": COLUMNS,
    }
    for attempt in range(3):
        response = SESSION.post(API, json=body, timeout=90)
        if response.status_code < 500 or attempt == 2:
            break
        time.sleep(3)
    response.raise_for_status()
    manifest = {
        "fetched_at": stamp(),
        "endpoint": API,
        "request": body,
        "response": response.json(),
    }
    save(path, manifest)
    print("QUEUED", key(year, period), flush=True)
    return manifest


def get_status(manifest):
    r = SESSION.get(manifest["response"]["status_url"], timeout=45)
    r.raise_for_status()
    return r.json()


def download(manifest, status):
    folder = ROOT / "data/downloads"
    folder.mkdir(exist_ok=True)
    path = folder / manifest["response"]["file_name"]
    if path.exists():
        return path
    url = status.get("file_url") or manifest["response"]["file_url"]
    partial = path.with_suffix(".part")
    start = partial.stat().st_size if partial.exists() else 0
    headers = {"Range": f"bytes={start}-"} if start else {}
    r = SESSION.get(url, headers=headers, stream=True, timeout=(30, 180))
    if r.status_code == 416 and start and zipfile.is_zipfile(partial):
        partial.rename(path)
        return path
    r.raise_for_status()
    resume = r.status_code == 206 and r.headers.get("Content-Range", "").startswith(
        f"bytes {start}-"
    )
    total = start if resume else 0
    with partial.open("ab" if resume else "wb") as out:
        for chunk in r.iter_content(8 * 1024 * 1024):
            if shutil.disk_usage(folder).free < 750 * 1024 * 1024:
                raise RuntimeError("Insufficient local disk space for source download")
            out.write(chunk)
            total += len(chunk)
    path.with_suffix(".part").rename(path)
    print("DOWNLOADED", path.name, f"{total / 1024 / 1024:.1f} MiB", flush=True)
    return path


def kind_of(code):
    for kind, codes in TYPES.items():
        if code in codes:
            return kind
    return None


def parse(year, period, manifest, status):
    save(ROOT / f"data/raw/outlays-{key(year, period)}-status.json", status)
    output = aggregate_path(year, period)
    if output.exists():
        return
    path = download(manifest, status)
    rows = {}
    unmapped = {k: collections.defaultdict(Decimal) for k in TYPES}
    details = {}
    totals = collections.defaultdict(Decimal)
    counts = collections.Counter()
    period_counts = collections.Counter()
    reference = json.loads((ROOT / "dist/data/spending.json").read_text())["years"][
        "2026"
    ]["districts"]
    name_to_id = {r["name"]: r["id"] for r in reference}
    with zipfile.ZipFile(path) as archive:
        for member in archive.namelist():
            if not member.lower().endswith(".csv"):
                continue
            with archive.open(member) as raw:
                for row, n, kind in financial_rows(
                    raw, COLUMNS, counts, period_counts, totals
                ):
                    district = row[
                        "prime_award_summary_place_of_performance_cd_current"
                    ].strip()
                    code = name_to_id.get(district)
                    if code is None:
                        unmapped[kind][district] += n
                        continue
                    r = rows.setdefault(code, {k: Decimal(0) for k in TYPES})
                    r[kind] += n
                    if n == 0:
                        continue
                    detail = details.setdefault(code, {k: {} for k in TYPES})[kind]
                    fields = [
                        (
                            "awarding_agency",
                            row["awarding_agency_name"]
                            or "Unspecified awarding agency",
                        )
                    ]
                    if kind == "grants":
                        fields.append(
                            (
                                "cfda",
                                f"{row['cfda_number']} {row['cfda_title']}".strip()
                                or "Unspecified assistance program",
                            )
                        )
                    else:
                        fields.append(
                            (
                                "naics",
                                f"{row['naics_code']} {row['naics_description']}".strip()
                                or "Unspecified industry",
                            )
                        )
                    for category, name in fields:
                        group = detail.setdefault(category, {})
                        group[name] = group.get(name, Decimal(0)) + n
    for kind in TYPES:
        assert (
            sum((r[kind] for r in rows.values()), Decimal(0))
            + sum(unmapped[kind].values(), Decimal(0))
            == totals[kind]
        )
    assert (
        totals["all_reported_outlays"]
        == sum((totals[k] for k in TYPES), Decimal(0))
        + totals["excluded_other_or_unlinked_awards"]
    )

    def convert(value):
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, dict):
            return {k: convert(v) for k, v in value.items()}
        return value

    with path.open("rb") as source_file:
        source_hash = hashlib.file_digest(source_file, "sha256").hexdigest()
    result = {
        "fiscal_year": year,
        "period": period,
        "source_url": status.get("file_url") or manifest["response"]["file_url"],
        "source_sha256": source_hash,
        "source_bytes": path.stat().st_size,
        "retrieved_at": stamp(),
        "counts": dict(counts),
        "submission_period_counts": dict(period_counts),
        "totals": convert(dict(totals)),
        "districts": convert(rows),
        "unmapped": convert(unmapped),
        "details": convert(details),
    }
    save(output, result)
    print("AGGREGATED", key(year, period), dict(counts), flush=True)


def terms_for_cycle(year):
    terms = [(year, 12, 1), (year + 1, 12, 1)]
    if year > 2017:
        terms.append((year, 3, -1))
    if year < 2025:
        terms.append((year + 2, 3, 1))
    return terms


def reported_payments():
    reference = json.loads((ROOT / "dist/data/spending.json").read_text())["years"][
        "2026"
    ]["districts"]
    rows = {
        r["id"]: {
            "id": r["id"],
            "name": r["name"],
            "population": r["population"],
            "grants": None,
            "contracts": None,
        }
        for r in reference
    }
    unmapped = {}
    dates = []
    for kind in TYPES:
        raw = json.loads(
            (ROOT / f"data/raw/outlay-research-lifetime-{kind}.json").read_text()
        )
        assert raw["request"]["spending_level"] == "awards"
        assert "time_period" not in raw["request"]["filters"]
        dates.append(raw["fetched_at"])
        unmapped[kind] = []
        for item in raw["response"]["results"]:
            # aggregated_amount here is lifetime obligations, NOT actual payments.
            n = item["total_outlays"]
            code = item["shape_code"]
            if code in rows:
                rows[code][kind] = n
            else:
                unmapped[kind].append({**item, "aggregated_amount": n})
    return {
        "source": "https://api.usaspending.gov/api/v2/search/spending_by_geography/",
        "fetched_at": max(dates),
        "measure": "Reported payments to date",
        "boundary_congress": 119,
        "all_reported": {
            "label": "Reported payments to date",
            "start": None,
            "end": None,
            "as_of": max(dates)[:10],
            "reporting": "cumulative",
            "districts": list(rows.values()),
            "unmapped": unmapped,
        },
        "years": {},
        "cycles": {},
        "cycle_total": None,
        "metadata": {
            "annual_exports_available": False,
            "mandatory_award_outlays_start": "2021-10-01",
        },
    }


def assemble():
    source = {
        key(y, p): json.loads(aggregate_path(y, p).read_text()) for y, p in SNAPSHOTS
    }
    spending = json.loads((ROOT / "dist/data/spending.json").read_text())
    reference = spending["years"]["2026"]["districts"]

    def build(terms, label, start, end, partial=False):
        sources = [(source[key(y, p)], sign) for y, p, sign in terms]
        rows = {
            r["id"]: {
                "id": r["id"],
                "name": r["name"],
                "population": r["population"],
                "grants": Decimal(0),
                "contracts": Decimal(0),
            }
            for r in reference
        }
        unmapped = {k: collections.defaultdict(Decimal) for k in TYPES}
        details = {}
        available = any(
            s["counts"].get("reported_outlay_rows", 0) > 0 for s, _ in sources
        )
        for s, sign in sources:
            for code, r in s["districts"].items():
                for kind in TYPES:
                    rows[code][kind] += sign * Decimal(r[kind])
            for kind in TYPES:
                for name, n in s["unmapped"][kind].items():
                    unmapped[kind][name] += sign * Decimal(n)
            for code, types in s["details"].items():
                for kind, categories in types.items():
                    for category, groups in categories.items():
                        target = (
                            details.setdefault(code, {})
                            .setdefault(kind, {})
                            .setdefault(category, {})
                        )
                        for name, n in groups.items():
                            target[name] = target.get(
                                name, Decimal(0)
                            ) + sign * Decimal(n)
        for r in rows.values():
            for kind in TYPES:
                r[kind] = float(r[kind]) if available else None
        compact = {}
        for code, types in details.items():
            merged = {}
            for kind, categories in types.items():
                for cat, groups in categories.items():
                    target = merged.setdefault(cat, {})
                    for name, n in groups.items():
                        target[name] = target.get(name, Decimal(0)) + n
            all_types = {**types, "all": merged}
            compact[code] = {
                kind: {
                    cat: [
                        {"name": name, "amount": float(n)}
                        for name, n in sorted(
                            groups.items(), key=lambda x: (-x[1], x[0])
                        )[:6]
                    ]
                    for cat, groups in categories.items()
                }
                for kind, categories in all_types.items()
            }
        mandatory = start >= "2021-10-01"
        return {
            "label": label,
            "start": start,
            "end": end,
            "partial": partial,
            "reporting": ("mandatory" if mandatory else "optional-years")
            if available
            else "unavailable",
            "source_terms": [
                {"snapshot": key(y, p), "coefficient": sign} for y, p, sign in terms
            ],
            "districts": list(rows.values()),
            "unmapped": {
                k: [
                    {
                        "shape_code": name,
                        "display_name": name or None,
                        "aggregated_amount": float(n),
                    }
                    for name, n in groups.items()
                ]
                for k, groups in unmapped.items()
            },
            "details": compact,
        }

    years = {
        str(y): build([(y, 12, 1)], f"FY {y}", f"{y - 1}-10-01", f"{y}-09-30")
        for y in range(2022, 2027)
    }
    cycles = {
        p["id"]: build(
            terms_for_cycle(int(p["start"][:4])),
            p["label"],
            p["start"],
            p["end"],
            p["partial"],
        )
        for p in CYCLES
    }
    # FY2017P03 did not exist. Never silently treat that opening-quarter baseline as zero.
    # Without it, FY2017 year-end outlays could include Oct-Dec2016 payments.
    first = cycles["cycle115"]
    first["reporting"] = "unavailable"
    first["missing_reason"] = "Opening-quarter data unavailable"
    first["source_terms"] = []
    first["details"] = {}
    first["unmapped"] = {kind: [] for kind in TYPES}
    for row in first["districts"]:
        for kind in TYPES:
            row[kind] = None
    available_terms = [(y, 12, 1) for y in range(2019, 2027)] + [(2019, 3, -1)]
    total = build(
        available_terms,
        "Four available cycles · 2019–2026",
        "2019-01-01",
        "2026-09-30",
        True,
    )
    for pid, period in (
        [(str(y), p) for y, p in years.items()]
        + list(cycles.items())
        + [("cycles-available", total)]
    ):
        details = period.pop("details")
        filename = f"outlays-details-{pid}.json"
        (ROOT / "dist/data" / filename).write_text(
            json.dumps(details, separators=(",", ":"), ensure_ascii=False)
        )
        period["details_file"] = filename
    result = {
        **reported_payments(),
        "source": API,
        "fetched_at": max(x["retrieved_at"] for x in source.values()),
        "measure": "Reported fiscal-year-to-date gross outlays",
        "boundary_congress": 119,
        "years": years,
        "cycles": cycles,
        "cycle_total": None,
        "available_cycle_total": total,
        "metadata": {
            "mandatory_award_outlays_start": "2021-10-01",
            "earliest_account_data": "2017-04-01",
            "financial_data_through": "2026-09-30",
            "cycle_calendar_reporting": True,
            "fy2017_q1_unavailable": True,
            "first_cycle_payments_unavailable": True,
            "annual_exports_available": True,
        },
    }
    (ROOT / "dist/data/outlays.json").write_text(
        json.dumps(result, separators=(",", ":"), ensure_ascii=False)
    )
    print("WROTE outlays.json", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", action="store_true")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--assemble", action="store_true")
    parser.add_argument("--reported", action="store_true")
    args = parser.parse_args()
    if args.reported:
        target = ROOT / "dist/data/outlays.json"
        existing = json.loads(target.read_text()) if target.exists() else {}
        fresh = reported_payments()
        if existing.get("metadata", {}).get("annual_exports_available"):
            fresh = {**existing, "all_reported": fresh["all_reported"]}
        target.write_text(json.dumps(fresh, separators=(",", ":")))
        print("WROTE reported payments to date; annual values not inferred.")
        return
    if args.assemble:
        assemble()
        return
    for y, p in SNAPSHOTS:
        queue(y, p)
    if args.queue and not args.wait:
        return
    pending = [(y, p) for y, p in SNAPSHOTS if not aggregate_path(y, p).exists()]
    while pending:
        ready = []
        for y, p in pending:
            manifest = json.loads(manifest_path(y, p).read_text())
            try:
                status = get_status(manifest)
                save(ROOT / f"data/raw/outlays-{key(y, p)}-status.json", status)
                state = status.get("status")
                print("STATUS", key(y, p), state, flush=True)
                if state == "finished":
                    parse(y, p, manifest, status)
                    ready.append((y, p))
                elif state in ["failed", "error"]:
                    raise RuntimeError(f"{key(y, p)}: {status}")
            except requests.RequestException as error:
                print("NETWORK_RETRY", key(y, p), type(error).__name__, flush=True)
        pending = [x for x in pending if x not in ready]
        if not args.wait:
            break
        if pending:
            time.sleep(30)
    if not pending:
        assemble()


if __name__ == "__main__":
    main()
