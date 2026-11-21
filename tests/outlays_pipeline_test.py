"""Regression checks for cumulative reports, split files, and projected duplicate rows."""

import csv, io, json, pathlib, sys, tempfile, unittest, zipfile
from decimal import Decimal
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import build_outlays as pipeline


class FinancialReports(unittest.TestCase):
    def test_all_split_files_and_legitimate_duplicate_rows_are_counted(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            (root / "data/raw").mkdir(parents=True)
            (root / "dist/data").mkdir(parents=True)
            reference = {
                "years": {
                    "2026": {
                        "districts": [
                            {"id": "0101", "name": "AL-01", "population": 100}
                        ]
                    }
                }
            }
            (root / "dist/data/spending.json").write_text(json.dumps(reference))
            archive = root / "reports.zip"

            def row(amount, kind="02", district="AL-01", period="FY2025P12"):
                r = {key: "" for key in pipeline.COLUMNS}
                r.update(
                    submission_period=period,
                    award_type_code=kind,
                    prime_award_summary_place_of_performance_cd_current=district,
                    gross_outlay_amount_FYB_to_period_end=amount,
                    award_unique_key="same-award",
                    awarding_agency_name="Agency",
                )
                return r

            batches = [
                [row("100"), row("", period="FY2025P11")],
                [row("100")],
                [row("-5", "A")],
                [row("7", district="AL-90"), row("4", "06")],
            ]
            with zipfile.ZipFile(archive, "w") as z:
                for i, batch in enumerate(batches):
                    text = io.StringIO()
                    writer = csv.DictWriter(text, fieldnames=pipeline.COLUMNS)
                    writer.writeheader()
                    writer.writerows(batch)
                    z.writestr(f"split_{i}.csv", text.getvalue())
            with (
                patch.object(pipeline, "ROOT", root),
                patch.object(pipeline, "download", return_value=archive),
            ):
                pipeline.parse(
                    2025,
                    12,
                    {"response": {"file_url": "https://example.test/source.zip"}},
                    {},
                )
            result = json.loads(
                (root / "data/raw/outlays-fy2025-p12-aggregate.json").read_text()
            )
            self.assertEqual(result["counts"]["csv_rows"], 6)
            self.assertEqual(result["counts"]["null_outlay_rows"], 1)
            self.assertEqual(Decimal(result["districts"]["0101"]["grants"]), 200)
            self.assertEqual(Decimal(result["districts"]["0101"]["contracts"]), -5)
            self.assertEqual(Decimal(result["unmapped"]["grants"]["AL-90"]), 7)
            self.assertEqual(Decimal(result["totals"]["all_reported_outlays"]), 206)
            self.assertEqual(
                Decimal(result["totals"]["excluded_other_or_unlinked_awards"]), 4
            )

    def test_calendar_cycle_uses_year_end_less_opening_quarter_plus_closing_quarter(
        self,
    ):
        snapshots = {
            (2019, 12): Decimal(100),
            (2019, 3): Decimal(20),
            (2020, 12): Decimal(200),
            (2021, 3): Decimal(30),
        }
        total = sum(
            (
                sign * snapshots[year, period]
                for year, period, sign in pipeline.terms_for_cycle(2019)
            ),
            Decimal(0),
        )
        self.assertEqual(total, 310)

    def test_adjacent_calendar_cycles_telescope_without_repeating_boundary_quarters(
        self,
    ):
        coefficients = {}
        for start in [2019, 2021, 2023, 2025]:
            for year, period, sign in pipeline.terms_for_cycle(start):
                coefficients[year, period] = coefficients.get((year, period), 0) + sign
        expected = {(y, 12): 1 for y in range(2019, 2027)}
        expected[2019, 3] = -1
        self.assertEqual({k: v for k, v in coefficients.items() if v}, expected)


if __name__ == "__main__":
    unittest.main()
