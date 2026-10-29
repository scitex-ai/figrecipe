/** Node test for the provenance chip's recording-call parser.
 *
 * A figure-recorded (locked) table names its provenance with zero new
 * backend and zero new copy: the recipe filename plus the recording call
 * ids, both parsed from what the table already shows. Recorded columns
 * follow the `{call_id}_x` / `{call_id}_y` convention (see
 * _call_table_columns backend-side); anything else is user data, not
 * provenance.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/provenanceChip.test.ts
 */

import assert from "node:assert/strict";

import { recordingCalls } from "../src/components/DataTablePane/provenanceChip.ts";

let passed = 0;

function check(name: string, actual: unknown, expected: unknown): void {
  assert.deepEqual(actual, expected, name);
  passed += 1;
  console.log(`  ok ${passed} - ${name}`);
}

check(
  "x/y column pairs collapse to one call, first-appearance order",
  recordingCalls(["bar_0_x", "bar_0_y", "bar_1_x", "bar_1_y"]),
  ["bar_0", "bar_1"],
);

check(
  "a lone x names its call",
  recordingCalls(["plot_000_x"]),
  ["plot_000"],
);

check(
  "user columns are not provenance",
  recordingCalls(["time", "signal"]),
  [],
);

check(
  "mixed tables keep only recorded calls",
  recordingCalls(["time", "plot_000_x", "plot_000_y", "signal"]),
  ["plot_000"],
);

check("empty table names nothing", recordingCalls([]), []);

check(
  "lookalikes without the _x/_y suffix are user data",
  recordingCalls(["bar_0", "bar_0_z", "x_bar_0"]),
  [],
);

console.log(`\n${passed} passed`);
