/** Node test for the Data pane's plot-from-columns defaults.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/columnPlotSelection.test.ts
 */

import assert from "node:assert/strict";

import {
  buildPlotRequest,
  defaultColumnSelection,
} from "../src/components/DataTablePane/columnPlotSelection.ts";

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

console.log("columnPlotSelection:");

ok("first numeric column is X, the next numeric one is Y", () => {
  // Arrange
  const columns = [
    { name: "subject", dtype: "string" },
    { name: "time", dtype: "numeric" },
    { name: "signal", dtype: "numeric" },
    { name: "noise", dtype: "numeric" },
  ];
  // Act
  const selection = defaultColumnSelection(columns, []);
  // Assert
  assert.deepEqual(selection, { x: "time", ys: ["signal"] });
});

ok("a single numeric column is Y against the row number", () => {
  // Arrange
  const columns = [
    { name: "label", dtype: "string" },
    { name: "value", dtype: "numeric" },
  ];
  // Act
  const selection = defaultColumnSelection(columns, []);
  // Assert
  assert.deepEqual(selection, { x: null, ys: ["value"] });
});

ok("histogram drops X from the request", () => {
  // Arrange
  const selection = { x: "time", ys: ["signal"] };
  // Act
  const request = buildPlotRequest("histogram", selection);
  // Assert
  assert.deepEqual(request, { plot_type: "histogram", columns: ["signal"] });
});

console.log("\n" + passed + " assertion-groups passed");
