/** Node test for pasted-spreadsheet parsing.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/pasteData.test.ts
 */

import assert from "node:assert/strict";
import { parsePastedTable } from "../src/components/DataTablePane/pasteData.ts";

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

ok("tab-separated clipboard text imports as TSV", () => {
  const parsed = parsePastedTable("x\ty\n0\t1\n2\t3\n");
  assert.ok(parsed);
  assert.equal(parsed.format, "tsv");
  assert.equal(parsed.rows, 2);
  assert.equal(parsed.columns, 2);
});

ok("comma-separated text imports as CSV", () => {
  const parsed = parsePastedTable("x,y\n0,1\n2,3\n");
  assert.ok(parsed);
  assert.equal(parsed.format, "csv");
  assert.equal(parsed.rows, 2);
  assert.equal(parsed.columns, 2);
});

ok("windows line endings are normalised", () => {
  const parsed = parsePastedTable("x,y\r\n0,1\r\n");
  assert.ok(parsed);
  assert.ok(!parsed.content.includes("\r"));
  assert.equal(parsed.rows, 1);
});

ok("a header with no data rows is not a table", () => {
  assert.equal(parsePastedTable("x,y\n"), null);
});

ok("an empty clipboard is not a table", () => {
  assert.equal(parsePastedTable("   \n "), null);
});

ok("a single pasted column is still a table", () => {
  const parsed = parsePastedTable("y\n1\n2\n");
  assert.ok(parsed);
  assert.equal(parsed.columns, 1);
  assert.equal(parsed.rows, 2);
});

console.log(`\n${passed} passed`);
