/** Node test for the Data pane's badge ↔ table column highlight mapping.
 *
 * The mapping runs in both directions: a badge (or the X <select>) names the
 * table column to highlight, and a click on a table column names the badge to
 * move. Both directions have to survive a column that is gone (renamed or
 * deleted under the badges) without highlighting the wrong column or throwing.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/dataColumnHighlight.test.ts
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  badgeColumnHighlights,
  columnIndexByName,
  columnNameAt,
  sameBadge,
  selectionAfterColumnClick,
} from "../src/components/DataTablePane/dataColumnHighlight.ts";

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

const COLUMNS = [
  { name: "subject", dtype: "string" },
  { name: "time", dtype: "numeric" },
  { name: "signal", dtype: "numeric" },
  { name: "mass", dtype: "numeric" },
];

console.log("dataColumnHighlight:");

// ------------------------------------------------------- index <-> name

ok("column name maps to its table index", () => {
  // Arrange / Act / Assert
  assert.equal(columnIndexByName(COLUMNS, "subject"), 0);
  assert.equal(columnIndexByName(COLUMNS, "time"), 1);
  assert.equal(columnIndexByName(COLUMNS, "mass"), 3);
});

ok("table index maps back to its column name", () => {
  // Arrange / Act / Assert
  assert.equal(columnNameAt(COLUMNS, 0), "subject");
  assert.equal(columnNameAt(COLUMNS, 3), "mass");
});

ok("a renamed or absent column maps to no highlight instead of throwing", () => {
  // Arrange: the badges still name "temp", the table no longer has it.
  // Act / Assert
  assert.equal(columnIndexByName(COLUMNS, "temp"), -1);
  assert.equal(columnIndexByName(COLUMNS, null), -1);
  assert.equal(columnIndexByName(COLUMNS, undefined), -1);
  assert.equal(columnIndexByName(COLUMNS, ""), -1);
});

ok("an out-of-range index maps to no column name", () => {
  // Arrange / Act / Assert
  assert.equal(columnNameAt(COLUMNS, 9), null);
  assert.equal(columnNameAt(COLUMNS, -1), null);
});

// ------------------------------------------------------- badge -> column

ok("each badge maps to the table column it names, in table order", () => {
  // Arrange
  const selection = { x: "time", ys: ["signal", "mass"] };
  // Act
  const highlights = badgeColumnHighlights(COLUMNS, selection);
  // Assert
  assert.deepEqual(highlights, [
    { index: 1, name: "time", role: "x", preview: false },
    { index: 2, name: "signal", role: "y", preview: false },
    { index: 3, name: "mass", role: "y", preview: false },
  ]);
});

ok("a badge for a column the table no longer has highlights nothing", () => {
  // Arrange
  const selection = { x: "gone", ys: ["signal", "also_gone"] };
  // Act
  const highlights = badgeColumnHighlights(COLUMNS, selection);
  // Assert
  assert.deepEqual(highlights, [
    { index: 2, name: "signal", role: "y", preview: false },
  ]);
});

ok("an empty selection highlights nothing", () => {
  // Arrange
  const selection = { x: null, ys: [] };
  // Act / Assert
  assert.deepEqual(badgeColumnHighlights(COLUMNS, selection), []);
});

ok("a column that is both X and Y is highlighted once, as X", () => {
  // Arrange
  const selection = { x: "mass", ys: ["mass"] };
  // Act
  const highlights = badgeColumnHighlights(COLUMNS, selection);
  // Assert
  assert.deepEqual(highlights, [
    { index: 3, name: "mass", role: "x", preview: false },
  ]);
});

ok("hover previews the hovered badge's column and leaves the others alone", () => {
  // Arrange
  const selection = { x: "time", ys: ["signal"] };
  // Act
  const highlights = badgeColumnHighlights(COLUMNS, selection, {
    name: "signal",
    role: "y",
  });
  // Assert
  assert.deepEqual(highlights, [
    { index: 1, name: "time", role: "x", preview: false },
    { index: 2, name: "signal", role: "y", preview: true },
  ]);
});

ok("hovering a non-badge column previews nothing", () => {
  // Arrange: "subject" carries no badge, so there is nothing to preview.
  const selection = { x: "time", ys: ["signal"] };
  // Act
  const highlights = badgeColumnHighlights(COLUMNS, selection, {
    name: "subject",
    role: "x",
  });
  // Assert: unchanged, and no preview leaked onto another column.
  assert.deepEqual(highlights, [
    { index: 1, name: "time", role: "x", preview: false },
    { index: 2, name: "signal", role: "y", preview: false },
  ]);
});

ok("a hover preview clears when the pointer leaves (hover = null)", () => {
  // Arrange
  const selection = { x: "time", ys: ["signal"] };
  const hovering = badgeColumnHighlights(COLUMNS, selection, {
    name: "signal",
    role: "y",
  });
  // Act
  const left = badgeColumnHighlights(COLUMNS, selection, null);
  // Assert
  assert.equal(hovering[1].preview, true);
  assert.equal(left[1].preview, false);
});

// ------------------------------------------------------- column -> badge

ok("clicking a Y-badge column toggles Y off", () => {
  // Arrange
  const selection = { x: "time", ys: ["signal", "mass"] };
  // Act
  const next = selectionAfterColumnClick(selection, "signal");
  // Assert
  assert.deepEqual(next, { x: "time", ys: ["mass"] });
});

ok("clicking a Y-badge column toggled off moves it to X", () => {
  // Arrange: the first click left "signal" out of ys, a second click on it is
  // therefore an X gesture.
  const selection = { x: "time", ys: ["mass"] };
  // Act
  const next = selectionAfterColumnClick(selection, "signal");
  // Assert
  assert.deepEqual(next, { x: "signal", ys: ["mass"] });
});

ok("clicking a column with no badge makes it X", () => {
  // Arrange: "subject" carries no badge at all.
  const selection = { x: "time", ys: ["signal", "mass"] };
  // Act
  const next = selectionAfterColumnClick(selection, "subject");
  // Assert: X moved, the Y chips are untouched.
  assert.deepEqual(next, { x: "subject", ys: ["signal", "mass"] });
});

ok("clicking the X column again keeps it as X", () => {
  // Arrange
  const selection = { x: "time", ys: ["signal"] };
  // Act
  const next = selectionAfterColumnClick(selection, "time");
  // Assert
  assert.deepEqual(next, { x: "time", ys: ["signal"] });
});

ok("clicking a column with no selection at all makes it X", () => {
  // Arrange
  const selection = { x: null, ys: [] };
  // Act / Assert
  assert.deepEqual(selectionAfterColumnClick(selection, "mass"), {
    x: "mass",
    ys: [],
  });
});

// ------------------------------------------------------- hover identity

ok("the same badge is recognised so a mousemove does not re-render", () => {
  // Arrange
  const badge = { name: "signal", role: "y" as const };
  // Act / Assert
  assert.equal(sameBadge(badge, { name: "signal", role: "y" }), true);
  assert.equal(sameBadge(null, null), true);
  assert.equal(sameBadge(badge, null), false);
  assert.equal(sameBadge(badge, { name: "signal", role: "x" }), false);
  assert.equal(sameBadge(badge, { name: "mass", role: "y" }), false);
});

// ------------------------------------------------------- module hygiene

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(
  join(here, "..", "src", "components", "DataTablePane", "dataColumnHighlight.ts"),
  "utf8",
);

ok("the module stays importable under node --experimental-strip-types", () => {
  // Arrange / Act / Assert: a React or @scitex/ui import would be unresolvable
  // in Node, which is exactly how this module is tested.
  assert.doesNotMatch(source, /from\s+["']react["']/);
  assert.doesNotMatch(source, /from\s+["']@scitex\/ui/);
  assert.doesNotMatch(source, /gettext\s*\(/);
});

console.log(
  "All data-column highlight checks passed (" +
    passed +
    " assertion-groups).",
);
