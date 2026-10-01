/** Node test for the Data pane's table edits, undo stack and CSV write path.
 *
 * The pane's CRUD decisions live here, so this file is the safety net for the
 * two things a user cannot recover from on their own: a delete that loses data
 * (must be restorable exactly) and an edit that never reaches the backend (must
 * serialise to the CSV datatable/import parses back).
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/dataTableEdit.test.ts
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  addColumn,
  affectedAssignmentLabel,
  assignmentImpact,
  changedCells,
  cloneTable,
  datasetFromTable,
  deleteColumnAt,
  deleteRowAt,
  deleteRowsAt,
  diffTable,
  duplicateColumnAt,
  findRowIndexByValues,
  inferColumnDtype,
  insertRowAt,
  planColumnDelete,
  popRedo,
  popUndo,
  pushRedo,
  pushUndo,
  renameColumnAt,
  rowValuesAt,
  serializeTableToCsv,
  setCellValue,
  tableFromDataset,
  tablesEqual,
  UNDO_LIMIT,
  uniqueColumnName,
  type RedoEntry,
  type TableModel,
  type UndoEntry,
} from "../src/components/DataTablePane/dataTableEdit.ts";

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

/** The fixture every edit is exercised against. */
function fixture(): TableModel {
  return {
    columns: [
      { name: "subject", dtype: "string" },
      { name: "time", dtype: "numeric" },
      { name: "signal", dtype: "numeric" },
    ],
    rows: [
      ["s1", 1, 10],
      ["s2", 2, 20],
      ["s3", 3, 30],
    ],
  };
}

/** Minimal RFC4180 reader — the serializer must produce what a csv.reader
 * (Python's, on the backend) parses back to the same table. */
function parseCsv(content: string, delimiter = ","): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let quoted = false;
  for (let i = 0; i < content.length; i++) {
    const char = content[i];
    if (quoted) {
      if (char === '"' && content[i + 1] === '"') {
        cell += '"';
        i++;
      } else if (char === '"') {
        quoted = false;
      } else {
        cell += char;
      }
      continue;
    }
    if (char === '"') {
      quoted = true;
    } else if (char === delimiter) {
      row.push(cell);
      cell = "";
    } else if (char === "\n") {
      row.push(cell);
      rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += char;
    }
  }
  if (cell !== "" || row.length > 0) {
    row.push(cell);
    rows.push(row);
  }
  return rows;
}

/** What datatable/import does with a numeric-looking field (float() else text). */
function reimport(rows: string[][]): (string | number)[][] {
  return rows.map((row) =>
    row.map((value) => (/^-?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(value) ? Number(value) : value)),
  );
}

console.log("dataTableEdit:");

// ------------------------------------------------------- rows

ok("insertRowAt inserts a blank row and keeps every other value", () => {
  // Arrange
  const table = fixture();
  // Act
  const next = insertRowAt(table, 1);
  // Assert
  assert.equal(next.rows.length, 4);
  assert.deepEqual(next.rows, [
    ["s1", 1, 10],
    ["", "", ""],
    ["s2", 2, 20],
    ["s3", 3, 30],
  ]);
  assert.deepEqual(
    next.columns.map((c) => c.name),
    ["subject", "time", "signal"],
  );
});

ok("insertRowAt clamps an out-of-range index to the table", () => {
  // Arrange
  const table = fixture();
  // Act / Assert: past the end appends, before the start prepends.
  assert.deepEqual(insertRowAt(table, 99).rows[3], ["", "", ""]);
  assert.deepEqual(insertRowAt(table, -5).rows[0], ["", "", ""]);
  assert.equal(insertRowAt(table, 99).rows.length, 4);
});

ok("deleteRowAt removes exactly that row, values and shape", () => {
  // Arrange
  const table = fixture();
  // Act
  const next = deleteRowAt(table, 1);
  // Assert
  assert.deepEqual(next.rows, [
    ["s1", 1, 10],
    ["s3", 3, 30],
  ]);
  assert.deepEqual(
    next.columns.map((c) => c.name),
    ["subject", "time", "signal"],
  );
  // The original table is untouched: edits are pure.
  assert.equal(table.rows.length, 3);
});

ok("deleteRowAt of an out-of-range index changes nothing", () => {
  // Arrange
  const table = fixture();
  // Act / Assert
  assert.deepEqual(deleteRowAt(table, 7), table);
  assert.deepEqual(deleteRowAt(table, -1), table);
});

ok("deleteRowsAt drops several rows, ignoring duplicates and junk", () => {
  // Arrange
  const table = fixture();
  // Act
  const next = deleteRowsAt(table, [0, 2, 2, 9, -3]);
  // Assert: only rows 0 and 2 go; the surviving row keeps its order.
  assert.deepEqual(next.rows, [["s2", 2, 20]]);
});

ok("rowValuesAt pads a short row rather than losing column alignment", () => {
  // Arrange
  const table: TableModel = {
    columns: fixture().columns,
    rows: [["s1", 1]],
  };
  // Act / Assert
  assert.deepEqual(rowValuesAt(table, 0), ["s1", 1, ""]);
  assert.deepEqual(rowValuesAt(table, 5), []);
});

// ------------------------------------------------------- columns

ok("addColumn appends an empty column without shortening any row", () => {
  // Arrange
  const table = fixture();
  // Act
  const next = addColumn(table, "mass");
  // Assert
  assert.deepEqual(
    next.columns.map((c) => c.name),
    ["subject", "time", "signal", "mass"],
  );
  assert.deepEqual(
    next.rows.map((row) => row.length),
    [4, 4, 4],
  );
  assert.deepEqual(next.rows[0], ["s1", 1, 10, ""]);
  // An empty column is not numeric: it must not become the default X.
  assert.equal(next.columns[3].dtype, "string");
});

ok("addColumn avoids colliding with an existing name", () => {
  // Arrange
  const table = fixture();
  // Act
  const next = addColumn(addColumn(table, "signal"), "signal");
  // Assert
  assert.deepEqual(
    next.columns.map((c) => c.name),
    ["subject", "time", "signal", "signal_2", "signal_3"],
  );
});

ok("uniqueColumnName keeps the wanted name and suffixes only on collision", () => {
  // Arrange
  const columns = [{ name: "mass", dtype: "numeric" }];
  // Act / Assert
  assert.equal(uniqueColumnName(columns, "energy"), "energy");
  assert.equal(uniqueColumnName(columns, "mass"), "mass_2");
  assert.equal(uniqueColumnName(columns, "  "), "column");
});

ok("renameColumnAt changes the header and keeps the cells", () => {
  // Arrange
  const table = fixture();
  // Act
  const next = renameColumnAt(table, 1, " time_s ");
  // Assert
  assert.deepEqual(
    next.columns.map((c) => c.name),
    ["subject", "time_s", "signal"],
  );
  assert.deepEqual(next.rows, table.rows);
  // The renamed column keeps its dtype: the cells did not move.
  assert.equal(next.columns[1].dtype, "numeric");
});

ok("renameColumnAt refuses to blank a header or invent a column", () => {
  // Arrange
  const table = fixture();
  // Act / Assert: a half-typed or unknown rename leaves the table alone.
  assert.deepEqual(renameColumnAt(table, 1, "   "), table);
  assert.deepEqual(renameColumnAt(table, 9, "mass"), table);
});

ok("renameColumnAt never duplicates a column name", () => {
  // Arrange
  const table = fixture();
  // Act: rename "time" to the name "signal" already uses.
  const next = renameColumnAt(table, 1, "signal");
  // Assert
  assert.deepEqual(
    next.columns.map((c) => c.name),
    ["subject", "signal_2", "signal"],
  );
});

ok("deleteColumnAt removes the column and its cell from every row", () => {
  // Arrange
  const table = fixture();
  // Act
  const next = deleteColumnAt(table, 1);
  // Assert
  assert.deepEqual(
    next.columns.map((c) => c.name),
    ["subject", "signal"],
  );
  assert.deepEqual(next.rows, [
    ["s1", 10],
    ["s2", 20],
    ["s3", 30],
  ]);
});

ok("the last remaining column needs a confirm step, others do not", () => {
  // Arrange
  const table = fixture();
  const single: TableModel = {
    columns: [{ name: "mass", dtype: "numeric" }],
    rows: [[1], [2]],
  };
  // Act / Assert
  assert.deepEqual(planColumnDelete(table, 1), {
    allowed: true,
    needsConfirm: false,
    columnName: "time",
  });
  assert.deepEqual(planColumnDelete(single, 0), {
    allowed: false,
    needsConfirm: true,
    columnName: "mass",
  });
  // An index that is not a column is neither: no delete, no confirm.
  assert.deepEqual(planColumnDelete(table, 5), {
    allowed: false,
    needsConfirm: false,
    columnName: null,
  });
});

// ------------------------------------------------------- cells + ranges

ok("setCellValue coerces numbers and keeps text, like the backend does", () => {
  // Arrange
  const table = fixture();
  // Act
  const numeric = setCellValue(table, 0, 1, " 2.5 ");
  const text = setCellValue(table, 0, 0, "s9");
  const blank = setCellValue(table, 0, 2, "");
  // Assert
  assert.equal(numeric.rows[0][1], 2.5);
  assert.equal(text.rows[0][0], "s9");
  assert.equal(blank.rows[0][2], "");
  // Decimal-looking text stays text: it must not silently become a number the
  // backend would re-read differently.
  assert.equal(setCellValue(table, 0, 0, "0x10").rows[0][0], "0x10");
  assert.equal(setCellValue(table, 0, 0, "1 abc").rows[0][0], "1 abc");
});

ok("setCellValue ignores an out-of-range cell", () => {
  // Arrange
  const table = fixture();
  // Act / Assert
  assert.deepEqual(setCellValue(table, 9, 0, "x"), table);
  assert.deepEqual(setCellValue(table, 0, 9, "x"), table);
});

ok("changedCells reports only the cells that differ", () => {
  // Arrange
  const before = fixture();
  const after = setCellValue(setCellValue(before, 0, 0, "s9"), 1, 2, 99);
  // Act
  const changed = changedCells(before, after);
  // Assert: the two edited cells, in row-major order — and nothing else.
  assert.deepEqual(changed, [
    { row: 0, col: 0 },
    { row: 1, col: 2 },
  ]);
});

// ------------------------------------------------------- diff + naming

ok("diffTable names a single cell edit with column and row", () => {
  // Arrange
  const before = fixture();
  const after = setCellValue(before, 0, 1, 1.5);
  // Act
  const op = diffTable(before, after);
  // Assert
  assert.deepEqual(op, {
    kind: "edit-cells",
    count: 1,
    columnName: "time",
    rowNumber: 1,
  });
});

ok("diffTable names a header rename", () => {
  // Arrange
  const before = fixture();
  const after = renameColumnAt(before, 2, "amplitude");
  // Act / Assert
  assert.deepEqual(diffTable(before, after), {
    kind: "rename-column",
    from: "signal",
    to: "amplitude",
  });
});

ok("diffTable falls back to the table itself for a structural change", () => {
  // Arrange: a paste can widen the table beyond what this module named.
  const before = fixture();
  const after: TableModel = {
    columns: [...before.columns, { name: "extra", dtype: "string" }],
    rows: before.rows.map((row) => [...row, "x"]),
  };
  // Act / Assert
  assert.deepEqual(diffTable(before, after), { kind: "set-table" });
});

ok("diffTable reports no change for an identical table", () => {
  // Arrange / Act / Assert
  assert.equal(diffTable(fixture(), fixture()), null);
  assert.equal(tablesEqual(fixture(), cloneTable(fixture())), true);
  assert.equal(
    tablesEqual(fixture(), setCellValue(fixture(), 0, 0, "s9")),
    false,
  );
});

ok("findRowIndexByValues prefers the rendered row and survives sorting", () => {
  // Arrange
  const table = fixture();
  // The table's view is sorted by "time" descending: row 0 shows s3.
  const rendered = ["s3", 3, 30];
  // Act / Assert
  assert.equal(findRowIndexByValues(table, rendered, 2), 2);
  // A stale preferred index still resolves by value.
  assert.equal(findRowIndexByValues(table, rendered, 0), 2);
});

ok("findRowIndexByValues refuses an ambiguous or missing row", () => {
  // Arrange
  const duplicated: TableModel = {
    columns: fixture().columns,
    rows: [
      ["s1", 1, 10],
      ["s1", 1, 10],
      ["s3", 3, 30],
    ],
  };
  // Act / Assert: two identical rows -> refuse, so no wrong row is deleted.
  assert.equal(findRowIndexByValues(duplicated, ["s1", 1, 10]), -1);
  // The rendered row wins when it is unambiguous.
  assert.equal(findRowIndexByValues(duplicated, ["s1", 1, 10], 1), 1);
  // Gone / nothing rendered -> refuse.
  assert.equal(findRowIndexByValues(fixture(), ["s8", 8, 80]), -1);
  assert.equal(findRowIndexByValues(fixture(), []), -1);
});

// ------------------------------------------------------- undo

ok("delete then undo restores the exact prior table", () => {
  // Arrange
  const table = fixture();
  const snapshot = cloneTable(table);
  const stack = pushUndo([], {
    label: "Delete row 2",
    op: { kind: "delete-rows", rowNumbers: [2] },
    snapshot,
    assignment: { x: "time", ys: ["signal"] },
  });
  // Act: delete a row and a column, then undo the last entry.
  const edited = deleteColumnAt(deleteRowAt(table, 1), 0);
  const { entry, stack: rest } = popUndo(stack);
  // Assert
  assert.equal(entry?.label, "Delete row 2");
  assert.deepEqual(entry?.snapshot, {
    columns: [
      { name: "subject", dtype: "string" },
      { name: "time", dtype: "numeric" },
      { name: "signal", dtype: "numeric" },
    ],
    rows: [
      ["s1", 1, 10],
      ["s2", 2, 20],
      ["s3", 3, 30],
    ],
  });
  assert.equal(rest.length, 0);
  assert.notDeepEqual(edited, table);
});

ok("a snapshot is not mutated by the edits that follow it", () => {
  // Arrange
  const table = fixture();
  const entry: UndoEntry = {
    label: "Delete column 'time'",
    op: { kind: "delete-column", columnName: "time" },
    snapshot: cloneTable(table),
    assignment: { x: "time", ys: ["signal"] },
  };
  const before = cloneTable(table);
  // Act: edit the live table in every way this module offers.
  let live = table;
  live = deleteColumnAt(live, 1);
  live = setCellValue(live, 0, 0, "changed");
  live = insertRowAt(live, 0);
  live = addColumn(live, "extra");
  live = renameColumnAt(live, 0, "renamed");
  // Assert: the snapshot still describes the original table exactly.
  assert.deepEqual(entry.snapshot, before);
  assert.equal(entry.snapshot.columns.length, 3);
  assert.equal(entry.snapshot.rows[0][1], 1);
});

ok("undo works from the oldest op down to the empty stack", () => {
  // Arrange
  const first: UndoEntry = {
    label: "Delete row 1",
    op: { kind: "delete-rows", rowNumbers: [1] },
    snapshot: fixture(),
    assignment: { x: null, ys: [] },
  };
  const second: UndoEntry = {
    label: "Delete column 'signal'",
    op: { kind: "delete-column", columnName: "signal" },
    snapshot: fixture(),
    assignment: { x: null, ys: [] },
  };
  // Act
  const stack = pushUndo(pushUndo([], first), second);
  const one = popUndo(stack);
  const two = popUndo(one.stack);
  const three = popUndo(two.stack);
  // Assert: newest first, then the oldest, then nothing — without throwing.
  assert.equal(one.entry?.label, "Delete column 'signal'");
  assert.equal(two.entry?.label, "Delete row 1");
  assert.equal(two.entry?.op.kind, "delete-rows");
  assert.equal(three.entry, null);
  assert.deepEqual(three.stack, []);
});

ok("an empty undo stack is a no-op, not a throw", () => {
  // Arrange / Act
  const result = popUndo([]);
  // Assert
  assert.equal(result.entry, null);
  assert.deepEqual(result.stack, []);
});

ok("the undo stack keeps its most recent entries within the cap", () => {
  // Arrange / Act: one entry more than the cap allows.
  let stack: UndoEntry[] = [];
  for (let i = 0; i < 60; i++) {
    stack = pushUndo(stack, {
      label: "Delete row " + (i + 1),
      op: { kind: "delete-rows", rowNumbers: [i + 1] },
      snapshot: fixture(),
      assignment: { x: null, ys: [] },
    });
  }
  // Assert
  assert.equal(stack.length, 50);
  assert.equal(stack[0].label, "Delete row 11");
  assert.equal(stack[49].label, "Delete row 60");
});

// ------------------------------------------------------- persistence

ok("the CSV write path round-trips a table fixture", () => {
  // Arrange: values the backend's csv.reader would otherwise split or strip.
  const table: TableModel = {
    columns: [
      { name: "subject", dtype: "string" },
      { name: "note", dtype: "string" },
      { name: "value", dtype: "numeric" },
    ],
    rows: [
      ["s1", "a,b", 1],
      ["s2", 'he said "hi"', 2],
      ["s3", "", 3.5],
    ],
  };
  // Act
  const csv = serializeTableToCsv(table);
  const parsed = parseCsv(csv);
  // Assert: exact bytes, then the table back.
  assert.equal(
    csv,
    'subject,note,value\ns1,"a,b",1\ns2,"he said ""hi""",2\ns3,,3.5\n',
  );
  assert.deepEqual(parsed[0], ["subject", "note", "value"]);
  assert.deepEqual(reimport(parsed.slice(1)), table.rows);
});

ok("the CSV write path never quotes a plain value", () => {
  // Arrange
  const table = fixture();
  // Act / Assert
  assert.equal(
    serializeTableToCsv(table),
    "subject,time,signal\ns1,1,10\ns2,2,20\ns3,3,30\n",
  );
});

ok("a header-only table still serialises as a CSV with its header row", () => {
  // Arrange
  const table: TableModel = {
    columns: [{ name: "mass", dtype: "numeric" }],
    rows: [],
  };
  // Act / Assert
  assert.equal(serializeTableToCsv(table), "mass\n");
});

// ------------------------------------------------------- dataset bridge

ok("a model survives the round trip through the shared table's shape", () => {
  // Arrange
  const table = fixture();
  // Act
  const dataset = datasetFromTable(table);
  const back = tableFromDataset(dataset, table);
  // Assert
  assert.deepEqual(dataset.columns, ["subject", "time", "signal"]);
  assert.deepEqual(dataset.rows[0], { subject: "s1", time: 1, signal: 10 });
  assert.deepEqual(back.columns, table.columns);
  assert.deepEqual(back.rows, table.rows);
});

ok("columns the table grew (a paste) are adopted with an inferred dtype", () => {
  // Arrange: the shared table can add columns the pane never created.
  const dataset = {
    columns: ["subject", "width"],
    rows: [
      { subject: "s1", width: 1 },
      { subject: "s2", width: 2 },
    ],
  };
  // Act
  const table = tableFromDataset(dataset, fixture());
  // Assert
  assert.deepEqual(
    table.columns.map((c) => c.name),
    ["subject", "width"],
  );
  assert.equal(table.columns[1].dtype, "numeric");
  assert.deepEqual(table.rows, [
    ["s1", 1],
    ["s2", 2],
  ]);
});

ok("inferColumnDtype treats an empty column as text, not as numeric", () => {
  // Arrange / Act / Assert
  assert.equal(inferColumnDtype([1, 2, 3]), "numeric");
  assert.equal(inferColumnDtype([1, "x"]), "string");
  assert.equal(inferColumnDtype([]), "string");
  assert.equal(inferColumnDtype(["", ""]), "string");
});

// ------------------------------------------------- duplicate + redo + impact

const CRUD_TABLE: TableModel = {
  columns: [
    { name: "mass", dtype: "numeric" },
    { name: "label", dtype: "string" },
  ],
  rows: [
    [1, "a"],
    [2, "b"],
  ],
};

ok("duplicateColumnAt copies the column in right after itself", () => {
  // Arrange
  const table = CRUD_TABLE;
  // Act
  const next = duplicateColumnAt(table, 0);
  // Assert
  assert.deepEqual(
    next.columns.map((c) => c.name),
    ["mass", "mass_copy", "label"],
  );
});

ok("duplicateColumnAt copies every cell of that column only", () => {
  // Arrange
  const table = CRUD_TABLE;
  // Act
  const next = duplicateColumnAt(table, 0);
  // Assert
  assert.deepEqual(next.rows, [
    [1, 1, "a"],
    [2, 2, "b"],
  ]);
});

ok("duplicateColumnAt never collides with an existing name", () => {
  // Arrange -- a table that already holds the first candidate name.
  const table: TableModel = {
    columns: [
      { name: "mass", dtype: "numeric" },
      { name: "mass_copy", dtype: "numeric" },
    ],
    rows: [[1, 9]],
  };
  // Act
  const next = duplicateColumnAt(table, 0);
  // Assert
  assert.deepEqual(
    next.columns.map((c) => c.name),
    ["mass", "mass_copy_2", "mass_copy"],
  );
});

ok("duplicateColumnAt leaves the table untouched for an unknown column", () => {
  // Arrange
  const table = CRUD_TABLE;
  // Act
  const next = duplicateColumnAt(table, 7);
  // Assert
  assert.deepEqual(next, table);
});

ok("redo restores exactly the state an undo removed", () => {
  // Arrange -- "delete row 1, undo, redo" as the pane performs it.
  const before = CRUD_TABLE;
  const deleted = deleteRowAt(before, 0);
  const undoEntry: UndoEntry = {
    label: "Delete row 1",
    op: { kind: "delete-rows", rowNumbers: [1] },
    snapshot: cloneTable(before),
    assignment: { x: "time", ys: ["signal"] },
  };
  // Act -- undo restores the snapshot, then redo takes back what it removed.
  const afterUndo = cloneTable(undoEntry.snapshot);
  const parked = pushRedo([], {
    label: undoEntry.label,
    table: cloneTable(deleted),
    assignment: { x: "time", ys: ["signal"] },
  });
  const { entry, stack } = popRedo(parked);
  const afterRedo = entry ? cloneTable(entry.table) : null;
  // Assert
  assert.deepEqual(afterUndo, before);
  assert.deepEqual(afterRedo, deleted);
  assert.deepEqual(stack, []);
});

ok("an empty redo stack is a no-op, not an error", () => {
  // Arrange
  const stack: RedoEntry[] = [];
  // Act
  const { entry, stack: after } = popRedo(stack);
  // Assert
  assert.equal(entry, null);
  assert.deepEqual(after, []);
});

ok("the redo stack is capped like undo, oldest dropped", () => {
  // Arrange
  let stack: RedoEntry[] = [];
  // Act
  for (let i = 0; i < UNDO_LIMIT + 3; i += 1) {
    stack = pushRedo(stack, {
      label: `op ${i}`,
      table: cloneTable(CRUD_TABLE),
      assignment: { x: "time", ys: ["signal"] },
    });
  }
  // Assert
  assert.equal(stack.length, UNDO_LIMIT);
  assert.equal(stack[0].label, "op 3");
});

ok("assignmentImpact names the X column", () => {
  // Arrange
  const selection = { x: "mass", ys: ["label"] };
  // Act
  const impact = assignmentImpact(selection, "mass");
  // Assert
  assert.deepEqual(impact, { x: true, y: false, affected: true });
});

ok("assignmentImpact names a Y column", () => {
  // Arrange
  const selection = { x: "mass", ys: ["label", "other"] };
  // Act
  const impact = assignmentImpact(selection, "other");
  // Assert
  assert.deepEqual(impact, { x: false, y: true, affected: true });
});

ok("assignmentImpact says nothing for an unassigned column", () => {
  // Arrange
  const selection = { x: "mass", ys: ["label"] };
  // Act
  const impact = assignmentImpact(selection, "spare");
  // Assert
  assert.equal(impact.affected, false);
});

ok("assignmentImpact tolerates no removed column at all", () => {
  // Arrange
  const selection = { x: null, ys: [] };
  // Act
  const impact = assignmentImpact(selection, null);
  // Assert
  assert.deepEqual(impact, { x: false, y: false, affected: false });
});

ok("the affected assignment is named the way the user sees it", () => {
  // Arrange
  const cases = [
    [{ x: true, y: false, affected: true }, "X"],
    [{ x: false, y: true, affected: true }, "Y"],
    [{ x: true, y: true, affected: true }, "X and Y"],
  ] as const;
  // Act
  const labels = cases.map(([impact]) => affectedAssignmentLabel(impact));
  // Assert
  assert.deepEqual(labels, ["X", "Y", "X and Y"]);
});

// ------------------------------------------------------- module hygiene

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(
  join(here, "..", "src", "components", "DataTablePane", "dataTableEdit.ts"),
  "utf8",
);

ok("the module stays importable under node --experimental-strip-types", () => {
  // Arrange / Act / Assert
  assert.doesNotMatch(source, /from\s+["']react["']/);
  assert.doesNotMatch(source, /from\s+["']@scitex\/ui/);
  assert.doesNotMatch(source, /gettext\s*\(/);
});

console.log(
  "All data-table edit checks passed (" + passed + " assertion-groups).",
);
