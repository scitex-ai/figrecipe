/** Node test for the table-column -> canvas-element emphasis mapping.
 *
 * Column badges (X/Y) select table columns for plotting; the canvas should
 * emphasize the elements drawn from those columns -- highlight only, never a
 * selection change (selection owns the Details pane). This inverts the
 * backend-served element_data_map: columns -> element keys.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/elementEmphasis.test.ts
 */

import assert from "node:assert/strict";

import { elementsForColumns } from "../src/components/DataTablePane/elementEmphasis.ts";

let passed = 0;

function check(name: string, actual: unknown, expected: unknown): void {
  assert.deepEqual(actual, expected, name);
  passed += 1;
  console.log(`  ok ${passed} - ${name}`);
}

const elementDataMap = {
  ax0_line0: { columns: ["time", "signal"], rowIndices: [0, 1, 2] },
  ax0_bar0: { columns: ["bar_0_x", "bar_0_y"], rowIndices: [0] },
};

check(
  "columns shared with a series emphasize its element",
  elementsForColumns(elementDataMap, ["signal"]),
  ["ax0_line0"],
);

check(
  "x column alone also emphasizes (points are (x, y) pairs)",
  elementsForColumns(elementDataMap, ["time"]),
  ["ax0_line0"],
);

check(
  "badging both series selects both elements",
  elementsForColumns(elementDataMap, ["signal", "bar_0_x"]),
  ["ax0_line0", "ax0_bar0"],
);

check(
  "unknown column emphasizes nothing",
  elementsForColumns(elementDataMap, ["nope"]),
  [],
);

check("empty badges emphasize nothing", elementsForColumns(elementDataMap, []), []);

check(
  "empty map emphasizes nothing",
  elementsForColumns({}, ["signal"]),
  [],
);

check(
  "element with no columns never matches",
  elementsForColumns(
    { ax0_line9: { columns: [], rowIndices: [] } },
    ["signal"],
  ),
  [],
);

console.log(`\n${passed} passed`);
