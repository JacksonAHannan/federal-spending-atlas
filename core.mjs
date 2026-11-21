export function obligation(row, kind = "all") {
  if (!row) return null;
  if (kind !== "all") return row[kind];
  if (row.grants == null || row.contracts == null) return null;
  return row.grants + row.contracts;
}
export function measure(row, kind, perCapita = false) {
  const n = obligation(row, kind);
  return n == null || (perCapita && !row.population)
    ? null
    : perCapita
      ? n / row.population
      : n;
}
export function ranking(rows, kind, perCapita = false) {
  return rows
    .filter((r) => measure(r, kind, perCapita) != null)
    .sort(
      (a, b) =>
        measure(b, kind, perCapita) - measure(a, kind, perCapita) ||
        a.id.localeCompare(b.id),
    );
}
export function csv(rows) {
  return rows
    .map((row) =>
      row
        .map((x) => '"' + String(x ?? "").replaceAll('"', '""') + '"')
        .join(","),
    )
    .join("\r\n");
}
