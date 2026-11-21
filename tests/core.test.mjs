import { test } from "node:test";
import assert from "node:assert/strict";
import { obligation, measure, ranking, csv } from "../dist/core.mjs";
test("net obligations preserve reductions and genuine zero", () => {
  assert.equal(obligation({ grants: 10, contracts: -4 }), 6);
  assert.equal(obligation({ grants: 0, contracts: 0 }), 0);
  assert.equal(obligation({ grants: null, contracts: 0 }), null);
});
test("missing population cannot be treated as zero per resident", () => {
  assert.equal(
    measure({ grants: 100, contracts: 0, population: 0 }, "all", true),
    null,
  );
  assert.equal(
    measure({ grants: 100, contracts: 0, population: 5 }, "all", true),
    20,
  );
});
test("rankings sort chosen award type, preserve negatives and exclude unavailable", () => {
  const rows = [
    { id: "a", grants: 20, contracts: -25 },
    { id: "b", grants: 5, contracts: 10 },
    { id: "c", grants: null, contracts: 0 },
  ];
  assert.deepEqual(
    ranking(rows, "all").map((r) => r.id),
    ["b", "a"],
  );
  assert.deepEqual(
    ranking(rows, "grants").map((r) => r.id),
    ["a", "b"],
  );
});
test("CSV safely quotes project names, multiline descriptions, and missing values", () => {
  assert.equal(csv([['a,"b"', "line\n2", null]]), '"a,""b""","line\n2",""');
});

test("period selection keeps annual, cycle, combined and cumulative datasets separate", async () => {
  const { getPeriod, periodLabel } = await import("../dist/core.mjs");
  const sample = {
    years: { 2025: { id: "annual" } },
    cycles: { cycle119: { id: "cycle", label: "119th Congress" } },
    cycle_total: { id: "combined" },
    all_reported: { id: "cumulative" },
  };
  assert.equal(getPeriod(sample, "2025").id, "annual");
  assert.equal(getPeriod(sample, "cycle119").id, "cycle");
  assert.equal(getPeriod(sample, "cycles-all").id, "combined");
  assert.equal(getPeriod(sample, "all-reported").id, "cumulative");
  assert.equal(getPeriod(sample, "missing"), null);
  assert.equal(periodLabel(sample, "2025"), "FY 2025");
});
test("unavailable period amounts do not become zero totals", async () => {
  const { sumKnown } = await import("../dist/core.mjs");
  assert.equal(sumKnown([{ grants: null, contracts: null }], "all"), null);
  assert.equal(
    sumKnown(
      [
        { grants: 10, contracts: -2 },
        { grants: 0, contracts: 0 },
      ],
      "all",
    ),
    8,
  );
});
test("combined agency rankings use full-period combined data before top-six truncation", async () => {
  const { combinedCategories } = await import("../dist/core.mjs");
  const details = {
    all: { awarding_agency: [{ name: "Combined leader", amount: 90 }] },
    grants: { awarding_agency: [{ name: "Grant leader", amount: 60 }] },
    contracts: { awarding_agency: [{ name: "Contract leader", amount: 60 }] },
  };
  assert.equal(
    combinedCategories(details, "all", "awarding_agency")[0].name,
    "Combined leader",
  );
});

test("available-cycle aggregation has a separate period key from all five cycles", async () => {
  const { getPeriod } = await import("../dist/core.mjs");
  const sample = {
    cycle_total: null,
    available_cycle_total: { start: "2019-01-01" },
  };
  assert.equal(getPeriod(sample, "cycles-all"), null);
  assert.equal(getPeriod(sample, "cycles-available").start, "2019-01-01");
});
