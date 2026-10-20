/** Node test for the Data page sample table.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/sampleData.test.ts
 */

import assert from "node:assert/strict";
import { SAMPLE_TABLE_CSV, SAMPLE_TABLE_FORMAT } from "../src/components/DataTablePane/sampleData.ts";

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

ok("the sample posts through the CSV import path", () => {
  assert.equal(SAMPLE_TABLE_FORMAT, "csv");
});

ok("the sample has a header plus data rows", () => {
  const lines = SAMPLE_TABLE_CSV.split("\n").filter((line) => line.length > 0);
  assert.deepEqual(lines[0].split(","), ["x", "y", "group"]);
  assert.ok(lines.length >= 4);
});

ok("every data row matches the header width", () => {
  const lines = SAMPLE_TABLE_CSV.split("\n").filter((line) => line.length > 0);
  const width = lines[0].split(",").length;
  for (const line of lines.slice(1)) {
    assert.equal(line.split(",").length, width);
  }
});

ok("the sample holds two plottable series", () => {
  const groups = new Set(
    SAMPLE_TABLE_CSV.split("\n")
      .slice(1)
      .filter((line) => line.length > 0)
      .map((line) => line.split(",")[2]),
  );
  assert.deepEqual([...groups].sort(), ["A", "B"]);
});

console.log(`\n${passed} passed`);
