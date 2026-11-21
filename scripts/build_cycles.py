"""Add five calendar-year congressional reporting cycles using transaction obligations."""

import concurrent.futures, datetime, json, pathlib, time
from decimal import Decimal
import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
API = "https://api.usaspending.gov/api/v2/search/spending_by_geography/"
TYPES = {"contracts": ["A", "B", "C", "D"], "grants": ["02", "03", "04", "05"]}
# Calendar reporting years, matching the years each Congress sits. See method notes.
CYCLES = [
    {
        "id": f"cycle{c}",
        "congress": c,
        "label": f"{c}th Congress · {y}–{y + 1}",
        "start": f"{y}-01-01",
        "end": f"{y + 1}-12-31" if y < 2025 else "2026-09-30",
        "partial": y == 2025,
    }
    for c, y in zip(range(115, 120), range(2017, 2026, 2))
]


def fetch(period, kind):
    raw = ROOT / f"data/raw/usaspending-{period['id']}-{kind}.json"
    request = {
        "scope": "place_of_performance",
        "geo_layer": "district",
        "spending_level": "transactions",
        "filters": {
            "time_period": [{"start_date": period["start"], "end_date": period["end"]}],
            "award_type_codes": TYPES[kind],
        },
    }
    if not raw.exists():
        for attempt in range(3):
            try:
                response = requests.post(API, json=request, timeout=120)
                response.raise_for_status()
                result = response.json()
                raw.write_text(
                    json.dumps(
                        {
                            "fetched_at": datetime.datetime.now(
                                datetime.timezone.utc
                            ).isoformat(),
                            "endpoint": API,
                            "request": request,
                            "response": result,
                        },
                        indent=2,
                    )
                    + "\n"
                )
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2)
    envelope = json.loads(raw.read_text())
    assert envelope["request"] == request
    print(period["id"], kind, len(envelope["response"]["results"]), flush=True)
    return period["id"], kind, envelope


def combine(periods, reference):
    rows = []
    for base in reference:
        r = {"id": base["id"], "name": base["name"], "population": base["population"]}
        for kind in TYPES:
            values = [
                next((x[kind] for x in p["districts"] if x["id"] == base["id"]), None)
                for p in periods
            ]
            r[kind] = (
                float(sum(Decimal(str(v)) for v in values))
                if all(v is not None for v in values)
                else None
            )
        rows.append(r)
    unmapped = {k: [r for p in periods for r in p["unmapped"][k]] for k in TYPES}
    return {
        "label": "Five cycles · 2017–2026",
        "start": "2017-01-01",
        "end": "2026-09-30",
        "partial": True,
        "districts": rows,
        "unmapped": unmapped,
    }


def main():
    spending = json.loads((ROOT / "dist/data/spending.json").read_text())
    reference = spending["years"]["2026"]["districts"]
    ids = {r["id"] for r in reference}
    raws = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(fetch, p, k) for p in CYCLES for k in TYPES]
        for future in concurrent.futures.as_completed(futures):
            pid, kind, env = future.result()
            raws[pid, kind] = env
    periods = {}
    for period in CYCLES:
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
        for kind in TYPES:
            env = raws[period["id"], kind]
            unmapped[kind] = []
            for r in env["response"]["results"]:
                if r["shape_code"] in ids:
                    rows[r["shape_code"]][kind] = r["aggregated_amount"]
                else:
                    unmapped[kind].append(r)
        periods[period["id"]] = {
            **period,
            "districts": list(rows.values()),
            "unmapped": unmapped,
        }
    spending["cycles"] = periods
    spending["cycle_total"] = combine(list(periods.values()), reference)
    spending["cycle_fetched_at"] = max(x["fetched_at"] for x in raws.values())
    (ROOT / "dist/data/spending.json").write_text(
        json.dumps(spending, separators=(",", ":"))
    )
    print("Wrote five cycles and their disjoint combined total.")


if __name__ == "__main__":
    main()
