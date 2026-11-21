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
