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

// A period is a fiscal year, a calendar-year congressional reporting cycle,
// or the combined total of the five disjoint cycles.
export function getPeriod(dataset, id) {
  if (id === "cycles-all") return dataset?.cycle_total ?? null;
  if (id === "cycles-available") return dataset?.available_cycle_total ?? null;
  if (id === "all-reported") return dataset?.all_reported ?? null;
  return dataset?.years?.[id] ?? dataset?.cycles?.[id] ?? null;
}
export function periodLabel(dataset, id) {
  const p = getPeriod(dataset, id);
  return p?.label ?? (dataset?.years?.[id] ? `FY ${id}` : id);
}
export function sumKnown(rows, kind) {
  const values = rows.map((r) => obligation(r, kind)).filter((n) => n != null);
  return values.length ? values.reduce((sum, n) => sum + n, 0) : null;
}
export function combinedCategories(details, kind, category) {
  if (details?.[kind]?.[category]) return details[kind][category];
  const groups = new Map();
  for (const type of kind === "all" ? ["grants", "contracts"] : [kind]) {
    for (const item of details?.[type]?.[category] ?? []) {
      groups.set(item.name, (groups.get(item.name) ?? 0) + item.amount);
    }
  }
  return [...groups]
    .map(([name, amount]) => ({ name, amount }))
    .sort((a, b) => b.amount - a.amount || a.name.localeCompare(b.name));
}
