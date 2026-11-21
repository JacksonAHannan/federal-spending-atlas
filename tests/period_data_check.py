"""Independent checks of source ledgers, calendar boundaries, and payment fields."""

import json, pathlib, re
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
KINDS = ["grants", "contracts"]


def read(path):
    return json.loads((ROOT / path).read_text())


def d(value):
    return Decimal(str(value))


def near(a, b):
    assert abs(d(a) - d(b)) <= Decimal(".02"), (a, b)


def check_cycles(spending):
    assert list(sorted(spending["cycles"])) == [f"cycle{n}" for n in range(115, 120)]
    for pid, period in spending["cycles"].items():
        rows = {r["id"]: r for r in period["districts"]}
        for kind in KINDS:
            raw = read(f"data/raw/usaspending-{pid}-{kind}.json")
            assert raw["request"]["spending_level"] == "transactions"
            assert raw["request"]["filters"]["time_period"] == [
                {"start_date": period["start"], "end_date": period["end"]}
            ]
            for item in raw["response"]["results"]:
                if item["shape_code"] in rows:
                    near(rows[item["shape_code"]][kind], item["aggregated_amount"])
                else:
                    assert item in period["unmapped"][kind]
    assert spending["cycle_total"]["start"] == "2017-01-01"
    assert spending["cycle_total"]["end"] == "2026-09-30"
    for row in spending["cycle_total"]["districts"]:
        for kind in KINDS:
            values = [
                next(r[kind] for r in p["districts"] if r["id"] == row["id"])
                for p in spending["cycles"].values()
            ]
            near(row[kind], sum(map(d, values)))


def check_payments():
    outlays = read("dist/data/outlays.json")
    assert outlays["metadata"]["annual_exports_available"]
    assert outlays["cycle_total"] is None
    assert outlays["cycles"]["cycle115"]["reporting"] == "unavailable"
    assert all(
        r[k] is None for r in outlays["cycles"]["cycle115"]["districts"] for k in KINDS
    )
    source = {}
    for year, period in [(y, 12) for y in range(2017, 2027)] + [
        (y, 3) for y in [2019, 2021, 2023, 2025]
    ]:
        name = f"fy{year}-p{period:02}"
        item = read(f"data/raw/outlays-{name}-aggregate.json")
        source[name] = item
        assert len(item["source_sha256"]) == 64
        assert (
            item["counts"]["csv_rows"]
            == item["counts"]["reported_outlay_rows"]
            + item["counts"]["null_outlay_rows"]
        )
        valid_periods = {
            f"FY{year}P{period:02}",
            f"FY{year}P{period}",
            f"FY{year}Q{period // 3}",
        }
        assert set(item["submission_period_counts"]) <= valid_periods
        for kind in KINDS:
            exact = sum(
                (d(r[kind]) for r in item["districts"].values()), Decimal(0)
            ) + sum(map(d, item["unmapped"][kind].values()), Decimal(0))
            assert exact == d(item["totals"][kind])
        assert d(item["totals"]["all_reported_outlays"]) == sum(
            (d(item["totals"][k]) for k in KINDS), Decimal(0)
        ) + d(item["totals"]["excluded_other_or_unlinked_awards"])
        status = read(f"data/raw/outlays-{name}-status.json")
        assert status["status"] == "finished"
        assert item["counts"]["csv_rows"] == status["total_rows"]
        if name == "fy2017-p12":
            audit = read("data/raw/outlay-research-national-fy2017-p12-audit.json")
            # Independent audit owns a different schema; hash match is checked by searching its serialized evidence.
            assert item["source_sha256"] in json.dumps(audit)
    periods = [
        *outlays["years"].values(),
        *outlays["cycles"].values(),
        outlays["available_cycle_total"],
    ]
    for period in periods:
        if period["reporting"] == "unavailable":
            continue
        terms = period["source_terms"]
        assert terms
        for row in period["districts"]:
            for kind in KINDS:
                expected = sum(
                    (
                        term["coefficient"]
                        * d(
                            source[term["snapshot"]]["districts"]
                            .get(row["id"], {})
                            .get(kind, "0")
                        )
                        for term in terms
                    ),
                    Decimal(0),
                )
                near(row[kind], expected)
        for kind in KINDS:
            total = sum((d(r[kind]) for r in period["districts"]), Decimal(0)) + sum(
                (d(r["aggregated_amount"]) for r in period["unmapped"][kind]),
                Decimal(0),
            )
            expected = sum(
                (
                    t["coefficient"] * d(source[t["snapshot"]]["totals"][kind])
                    for t in terms
                ),
                Decimal(0),
            )
            near(total, expected)
    combined = outlays["available_cycle_total"]
    assert combined["start"] == "2019-01-01"
    for row in combined["districts"]:
        for kind in KINDS:
            expected = sum(
                (
                    d(
                        next(
                            r[kind]
                            for r in outlays["cycles"][f"cycle{n}"]["districts"]
                            if r["id"] == row["id"]
                        )
                    )
                    for n in range(116, 120)
                ),
                Decimal(0),
            )
            near(row[kind], expected)
    lifetime = {r["id"]: r for r in outlays["all_reported"]["districts"]}
    for kind in KINDS:
        raw = read(f"data/raw/outlay-research-lifetime-{kind}.json")
        assert raw["request"]["spending_level"] == "awards"
        assert "time_period" not in raw["request"]["filters"]
        for item in raw["response"]["results"]:
            if item["shape_code"] in lifetime:
                near(lifetime[item["shape_code"]][kind], item["total_outlays"])
    # Validate linked agency rankings after all quarter arithmetic, before truncating top six.
    for pid in ["2025", "cycle118", "cycles-available"]:
        period = outlays["years"].get(pid) or outlays["cycles"].get(pid) or combined
        details = read("dist/data/" + period["details_file"])
        code = "0105"
        for kind in KINDS + ["all"]:
            merged = {}
            for t in period["source_terms"]:
                record = source[t["snapshot"]]["details"].get(code, {})
                for k in KINDS if kind == "all" else [kind]:
                    for name, n in record.get(k, {}).get("awarding_agency", {}).items():
                        merged[name] = merged.get(name, Decimal(0)) + t[
                            "coefficient"
                        ] * d(n)
            expected = sorted(merged.items(), key=lambda x: (-x[1], x[0]))[:6]
            actual = details.get(code, {}).get(kind, {}).get("awarding_agency", [])
            assert [r["name"] for r in actual] == [name for name, _ in expected]
            for r, (_, amount) in zip(actual, expected):
                near(r["amount"], amount)
    print(
        "PASS: five obligation cycles; fourteen financial source ledgers; period masks; annual/cycle payment arithmetic; missing first quarter; four-cycle totals; cumulative payment field; linked top-six agency rankings."
    )


if __name__ == "__main__":
    check_cycles(read("dist/data/spending.json"))
    check_payments()
