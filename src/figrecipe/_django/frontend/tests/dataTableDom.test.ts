/** Node test for the Data pane's DOM sync with the shared scitex-ui DataTable.
 *
 * The shared table owns its rendering and re-renders its className, so the
 * highlight and the selection read-back are driven from figrecipe's pane code,
 * against the data-col / data-row attributes the table renders. The single DOM
 * touch point (renderedColumnNodes, one querySelectorAll) is deliberately not
 * exercised here: every decision and every stamped class is, through the
 * minimal TableNode accessor the module is written against.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/dataTableDom.test.ts
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  applyColumnHighlight,
  readRowValues,
  readSelectedCells,
  type TableNode,
} from "../src/components/DataTablePane/dataTableDom.ts";
import type { ColumnHighlight } from "../src/components/DataTablePane/dataColumnHighlight.ts";

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

// ------------------------------------------------------- fake nodes

interface FakeNode extends TableNode {
  /** Test-only view of the stamped classes, sorted for stable comparison. */
  tokens(): string[];
}

/** The handful of node members the module actually calls — attributes, classes
 *  and text. Deliberately not a DOM: no tree, no selectors, no jsdom. */
function fakeNode(attributes: Record<string, string>, text = ""): FakeNode {
  const attrs = new Map<string, string>(Object.entries(attributes));
  const classes = new Set<string>();
  return {
    textContent: text,
    getAttribute: (name) => (attrs.has(name) ? (attrs.get(name) as string) : null),
    setAttribute: (name, value) => {
      attrs.set(name, value);
    },
    removeAttribute: (name) => {
      attrs.delete(name);
    },
    classList: {
      add: (...tokens) => {
        tokens.forEach((token) => classes.add(token));
      },
      remove: (...tokens) => {
        tokens.forEach((token) => classes.delete(token));
      },
      contains: (token) => classes.has(token),
    },
    tokens: () => [...classes].sort(),
  };
}

/** A table as the shared component renders it: headers first, then a cell for
 *  every row/column, all carrying data-col (cells also data-row). */
function fakeTable(cols: number, rows: number) {
  const nodes: FakeNode[] = [];
  for (let col = 0; col < cols; col++) {
    nodes.push(fakeNode({ "data-col": String(col) }, "header" + col));
  }
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      nodes.push(
        fakeNode(
          { "data-row": String(row), "data-col": String(col) },
          "r" + row + "c" + col,
        ),
      );
    }
  }
  return {
    nodes,
    header: (col: number) => nodes[col],
    cell: (col: number, row: number) => nodes[cols + row * cols + col],
    select: (node: FakeNode) =>
      node.classList.add("stx-app-data-table__cell--selected"),
  };
}

console.log("dataTableDom:");

// ------------------------------------------------------- highlight

ok("a highlighted column marks its header and every one of its cells", () => {
  // Arrange
  const table = fakeTable(3, 2);
  const highlights: ColumnHighlight[] = [
    { index: 1, name: "time", role: "x", preview: false },
  ];
  // Act
  applyColumnHighlight(table.nodes, highlights);
  // Assert: header + both cells of column 1, via class and attribute.
  for (const node of [table.header(1), table.cell(1, 0), table.cell(1, 1)]) {
    assert.deepEqual(node.tokens(), ["data-pane__col--x"]);
    assert.equal(node.getAttribute("data-col-highlight"), "x");
  }
  // ...and nothing else.
  assert.deepEqual(table.header(0).tokens(), []);
  assert.equal(table.cell(2, 0).getAttribute("data-col-highlight"), null);
});

ok("X and Y are told apart by the attribute, not only by colour", () => {
  // Arrange
  const table = fakeTable(3, 1);
  // Act
  applyColumnHighlight(table.nodes, [
    { index: 0, name: "subject", role: "y", preview: false },
    { index: 2, name: "mass", role: "x", preview: false },
  ]);
  // Assert
  assert.equal(table.header(0).getAttribute("data-col-highlight"), "y");
  assert.deepEqual(table.header(0).tokens(), ["data-pane__col--y"]);
  assert.equal(table.header(2).getAttribute("data-col-highlight"), "x");
  assert.deepEqual(table.header(2).tokens(), ["data-pane__col--x"]);
  assert.deepEqual(table.cell(1, 0).tokens(), []);
});

ok("a hover preview is marked as provisional", () => {
  // Arrange
  const table = fakeTable(2, 1);
  // Act
  applyColumnHighlight(table.nodes, [
    { index: 1, name: "signal", role: "y", preview: true },
  ]);
  // Assert
  assert.deepEqual(table.header(1).tokens(), [
    "data-pane__col--preview",
    "data-pane__col--y",
  ]);
});

ok("clearing the preview removes it and leaves the selection standing", () => {
  // Arrange
  const table = fakeTable(2, 1);
  applyColumnHighlight(table.nodes, [
    { index: 0, name: "time", role: "x", preview: false },
    { index: 1, name: "signal", role: "y", preview: true },
  ]);
  // Act: the pointer leaves the badge (selection kept, hover gone).
  applyColumnHighlight(table.nodes, [
    { index: 0, name: "time", role: "x", preview: false },
    { index: 1, name: "signal", role: "y", preview: false },
  ]);
  // Assert
  assert.deepEqual(table.header(1).tokens(), ["data-pane__col--y"]);
  assert.deepEqual(table.header(0).tokens(), ["data-pane__col--x"]);
});

ok("re-applying the same highlight leaves exactly one role class", () => {
  // Arrange
  const table = fakeTable(2, 1);
  const highlights: ColumnHighlight[] = [
    { index: 0, name: "time", role: "x", preview: false },
  ];
  // Act: the pane re-applies on every commit and every table DOM change.
  applyColumnHighlight(table.nodes, highlights);
  applyColumnHighlight(table.nodes, highlights);
  applyColumnHighlight(table.nodes, highlights);
  // Assert
  assert.deepEqual(table.cell(0, 0).tokens(), ["data-pane__col--x"]);
});

ok("a column that stops being highlighted is cleared completely", () => {
  // Arrange
  const table = fakeTable(2, 1);
  applyColumnHighlight(table.nodes, [
    { index: 0, name: "time", role: "x", preview: false },
    { index: 1, name: "signal", role: "y", preview: false },
  ]);
  // Act
  applyColumnHighlight(table.nodes, [
    { index: 1, name: "signal", role: "y", preview: false },
  ]);
  // Assert
  assert.deepEqual(table.header(0).tokens(), []);
  assert.equal(table.header(0).getAttribute("data-col-highlight"), null);
  assert.deepEqual(table.header(1).tokens(), ["data-pane__col--y"]);
});

ok("an empty highlight list clears the whole table", () => {
  // Arrange
  const table = fakeTable(3, 2);
  applyColumnHighlight(table.nodes, [
    { index: 0, name: "a", role: "x", preview: false },
    { index: 1, name: "b", role: "y", preview: false },
  ]);
  // Act
  applyColumnHighlight(table.nodes, []);
  // Assert
  for (const node of table.nodes) {
    assert.deepEqual(node.tokens(), []);
    assert.equal(node.getAttribute("data-col-highlight"), null);
  }
});

ok("a column index the table no longer renders is skipped, not a crash", () => {
  // Arrange: the badge still points at column 7.
  const table = fakeTable(2, 1);
  // Act
  applyColumnHighlight(table.nodes, [
    { index: 7, name: "gone", role: "x", preview: false },
  ]);
  // Assert
  for (const node of table.nodes) {
    assert.equal(node.getAttribute("data-col-highlight"), null);
  }
});

ok("a node with an unusable data-col is left alone", () => {
  // Arrange
  const broken = fakeNode({ "data-col": "not-a-number" }, "?");
  // Act
  applyColumnHighlight([broken], [
    { index: 0, name: "time", role: "x", preview: false },
  ]);
  // Assert
  assert.deepEqual(broken.tokens(), []);
  assert.equal(broken.getAttribute("data-col-highlight"), null);
});

// ------------------------------------------------------- selection read-back

ok("selected cells are read back as row/column coordinates", () => {
  // Arrange
  const table = fakeTable(3, 2);
  table.select(table.cell(1, 0));
  table.select(table.cell(2, 0));
  table.cell(0, 1).classList.add("stx-app-data-table__cell--current");
  // Act
  const cells = readSelectedCells(table.nodes);
  // Assert: the current cell is not a selection.
  assert.deepEqual(cells, [
    { row: 0, col: 1 },
    { row: 0, col: 2 },
  ]);
});

ok("a selected header is not mistaken for row 0 of the table", () => {
  // Arrange: a header has data-col and no data-row, and Number(null) is 0.
  const table = fakeTable(2, 1);
  table.select(table.header(0));
  // Act
  const cells = readSelectedCells(table.nodes);
  // Assert
  assert.deepEqual(cells, []);
});

ok("row 0 itself is still read back", () => {
  // Arrange
  const table = fakeTable(2, 1);
  table.select(table.cell(0, 0));
  // Act / Assert
  assert.deepEqual(readSelectedCells(table.nodes), [{ row: 0, col: 0 }]);
});

// ------------------------------------------------------- rendered rows

ok("a rendered row's values come back in column order", () => {
  // Arrange
  const table = fakeTable(3, 2);
  // Act / Assert
  assert.deepEqual(readRowValues(table.nodes, 1), ["r1c0", "r1c1", "r1c2"]);
});

ok("a row that is not rendered reads back as empty, never as another row", () => {
  // Arrange
  const table = fakeTable(3, 1);
  // Act / Assert
  assert.deepEqual(readRowValues(table.nodes, 5), []);
});

ok("a column the table did not render becomes an empty value, not a hole", () => {
  // Arrange: only columns 0 and 2 are present (Array#every would skip a hole).
  const nodes: TableNode[] = [
    fakeNode({ "data-row": "0", "data-col": "0" }, "a"),
    fakeNode({ "data-row": "0", "data-col": "2" }, "c"),
  ];
  // Act
  const values = readRowValues(nodes, 0);
  // Assert
  assert.deepEqual(values, ["a", "", "c"]);
});

// ------------------------------------------------------- module hygiene

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(
  join(here, "..", "src", "components", "DataTablePane", "dataTableDom.ts"),
  "utf8",
);

ok("the module stays importable under node --experimental-strip-types", () => {
  // Arrange / Act / Assert
  assert.doesNotMatch(source, /from\s+["']react["']/);
  assert.doesNotMatch(source, /from\s+["']@scitex\/ui/);
  assert.doesNotMatch(source, /gettext\s*\(/);
  // No global document either: the pane hands the root in.
  assert.doesNotMatch(source, /\bdocument\./);
});

console.log(
  "All data-table DOM sync checks passed (" + passed + " assertion-groups).",
);
