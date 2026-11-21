"""Yield only nonzero, eligible File C rows while reconciling every source row.

Arrow reads fixed-size batches and exact decimal128 currency. The standard-library
reader is retained for small fixtures and environments without Arrow.
"""

import csv
import io
from decimal import Decimal

AMOUNT = "gross_outlay_amount_FYB_to_period_end"
TYPE_CODES = {"contracts": ["A", "B", "C", "D"], "grants": ["02", "03", "04", "05"]}


def financial_rows(raw, columns, counts, period_counts, totals):
    try:
        import pyarrow as pa
        import pyarrow.compute as pc
        import pyarrow.csv as pacsv
    except ImportError:
        yield from python_rows(raw, columns, counts, period_counts, totals)
        return
    column_types = {name: pa.string() for name in columns}
    column_types[AMOUNT] = pa.decimal128(38, 2)
    reader = pacsv.open_csv(
        raw,
        read_options=pacsv.ReadOptions(block_size=4 * 1024 * 1024),
        convert_options=pacsv.ConvertOptions(
            column_types=column_types, null_values=[""]
        ),
    )
    assert set(columns) <= set(reader.schema.names), reader.schema.names
    codes = {
        kind: pa.array(values, type=pa.string()) for kind, values in TYPE_CODES.items()
    }
    all_codes = pa.array(
        [c for values in TYPE_CODES.values() for c in values], type=pa.string()
    )
    for batch in reader:
        amounts = batch.column(AMOUNT)
        types = batch.column("award_type_code")
        valid = pc.is_valid(amounts)
        counts["csv_rows"] += batch.num_rows
        counts["null_outlay_rows"] += amounts.null_count
        counts["reported_outlay_rows"] += batch.num_rows - amounts.null_count
        totals["all_reported_outlays"] += pc.sum(amounts).as_py() or Decimal(0)
        period_values = pc.value_counts(
            pc.filter(batch.column("submission_period"), valid)
        )
        for group in period_values.to_pylist():
            period_counts[group["values"]] += group["counts"]
        known = pc.is_in(types, value_set=all_codes)
        totals["excluded_other_or_unlinked_awards"] += pc.sum(
            pc.filter(amounts, pc.invert(known))
        ).as_py() or Decimal(0)
        for kind, value_set in codes.items():
            totals[kind] += pc.sum(
                pc.filter(amounts, pc.is_in(types, value_set=value_set))
            ).as_py() or Decimal(0)
        eligible = pc.and_(
            known,
            pc.not_equal(amounts, pa.scalar(Decimal(0), type=pa.decimal128(38, 2))),
        )
        for row in batch.filter(eligible).to_pylist():
            kind = (
                "contracts"
                if row["award_type_code"] in TYPE_CODES["contracts"]
                else "grants"
            )
            yield row, row[AMOUNT], kind


def python_rows(raw, columns, counts, period_counts, totals):
    reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
    assert set(columns) <= set(reader.fieldnames or []), reader.fieldnames
    for row in reader:
        counts["csv_rows"] += 1
        amount = row[AMOUNT].strip()
        if not amount:
            counts["null_outlay_rows"] += 1
            continue
        n = Decimal(amount)
        counts["reported_outlay_rows"] += 1
        period_counts[row["submission_period"]] += 1
        totals["all_reported_outlays"] += n
        kind = next(
            (k for k, v in TYPE_CODES.items() if row["award_type_code"] in v), None
        )
        if kind is None:
            totals["excluded_other_or_unlinked_awards"] += n
            continue
        totals[kind] += n
        if n != 0:
            yield row, n, kind
