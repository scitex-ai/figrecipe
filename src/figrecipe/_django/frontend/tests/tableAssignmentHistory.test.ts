/** Node test for the table history's ATOMIC (table + X/Y binding) undo/redo.
 *
 * The Data pane's every edit is undoable, and one of those edits is destructive
 * beyond the cells: deleting a column that is bound to X or Y clears the plot
 * assignment in the same step. Undo restored only the TABLE, so the binding —
 * which the reconcile step had already dropped — stayed cleared: the column came
 * back but the plot no longer pointed at it, and redo could not restore the
 * clear either. The table and its assignment have to travel together through
 * history, in one state transition, so no render can see half of the pair.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/tableAssignmentHistory.test.ts
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  applyRedo,
  applyUndo,
  assignmentFitsTable,
  cloneSelection,
  deleteColumnAt,
  pushUndo,
  renameColumnAt,
  type TableHistory,
  type TableModel,
  type UndoEntry,
} from "../src/components/DataTablePane/dataTableEdit.ts";

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel: string) =>
  readFileSync(join(here, "..", "src", rel), "utf8");

/** subject | time | signal — time is numeric, so it is the default X. */
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
    ],
  };
}

/** The assignment the pane would hold after the column set changed: names that
 *  are gone are dropped (reconcileSelection), which is why undo has to restore
 *  the assignment itself rather than re-deriving it. */
function reconcile(spec: { x: string | null; ys: string[] }, table: TableModel) {
  const names = new Set(table.columns.map((c) => c.name));
  const ys = spec.ys.filter((y) => names.has(y));
  const x = spec.x && names.has(spec.x) ? spec.x : null;
  return ys.length === 0 ? { x: null, ys: [] } : { x, ys };
}

console.log("tableAssignmentHistory:");

// ── the snapshot itself ───────────────────────────────────────────────────

ok("a history snapshot copies the Y list instead of aliasing it", () => {
  // Arrange
  const live = { x: "time", ys: ["signal"] };
  // Act
  const snapshot = cloneSelection(live);
  live.ys.push("noise");
  live.x = "noise";
  // Assert: a later edit must not rewrite what undo will restore.
  assert.deepEqual(snapshot, { x: "time", ys: ["signal"] });
});

ok("no assignment at all becomes an empty snapshot, not undefined", () => {
  // Arrange / Act / Assert
  assert.deepEqual(cloneSelection(null), { x: null, ys: [] });
  assert.deepEqual(cloneSelection(undefined), { x: null, ys: [] });
  assert.deepEqual(cloneSelection({ x: null, ys: [] }), { x: null, ys: [] });
});

// ── the invariant the pair exists to keep ─────────────────────────────────

ok("an assignment fits its table when every name it holds is a column", () => {
  // Arrange
  const table = fixture();
  // Act / Assert
  assert.equal(assignmentFitsTable(table, { x: "time", ys: ["signal"] }), true);
  assert.equal(assignmentFitsTable(table, { x: null, ys: [] }), true);
  assert.equal(assignmentFitsTable(table, { x: "gone", ys: ["signal"] }), false);
  assert.equal(assignmentFitsTable(table, { x: null, ys: ["gone"] }), false);
});

// ── deleting an assigned column: the pair comes back together ─────────────

/** The state the pane is in right after deleting the X column ("time"). */
function afterDeletingXColumn() {
  const before = fixture();
  const beforeAssignment = { x: "time", ys: ["signal"] };
  const afterTable = deleteColumnAt(before, 1);
  const afterAssignment = reconcile(beforeAssignment, afterTable);
  const entry: UndoEntry = {
    label: "Delete column 'time'",
    op: { kind: "delete-column", columnName: "time" },
    snapshot: before,
    assignment: beforeAssignment,
  };
  const history: TableHistory = {
    table: afterTable,
    assignment: afterAssignment,
    undoStack: pushUndo([], entry),
    redoStack: [],
  };
  return history;
}

ok("undoing the delete of the X column brings the X binding back with it", () => {
  // Arrange
  const history = afterDeletingXColumn();
  // Act
  const undone = applyUndo(history);
  // Assert: the table…
  assert.ok(undone);
  assert.deepEqual(
    undone.table.columns.map((c) => c.name),
    ["subject", "time", "signal"],
  );
  // …AND the binding, in the same transition.
  assert.deepEqual(undone.assignment, { x: "time", ys: ["signal"] });
  // The pair is consistent: no chip points at a column that is not there.
  assert.equal(assignmentFitsTable(undone.table, undone.assignment), true);
});

ok("undo names the change it reversed, so the toast and the redo agree", () => {
  // Arrange
  const history = afterDeletingXColumn();
  // Act
  const undone = applyUndo(history);
  // Assert
  assert.equal(undone?.label, "Delete column 'time'");
  assert.equal(undone?.undoStack.length, 0);
  assert.equal(undone?.redoStack.length, 1);
});

ok("redo re-applies the cleared binding and the delete together", () => {
  // Arrange
  const undone = applyUndo(afterDeletingXColumn());
  assert.ok(undone);
  // Act
  const redone = applyRedo(undone);
  // Assert: the state the undo removed comes back as one pair — the binding is
  // cleared exactly when its column goes away.
  assert.ok(redone);
  assert.deepEqual(
    redone.table.columns.map((c) => c.name),
    ["subject", "signal"],
  );
  assert.deepEqual(redone.assignment, { x: null, ys: ["signal"] });
  assert.equal(assignmentFitsTable(redone.table, redone.assignment), true);
  // ...and the redo is undoable again, with the pair it restored.
  assert.equal(redone.undoStack.length, 1);
  assert.deepEqual(redone.undoStack[0].assignment, { x: "time", ys: ["signal"] });
});

ok("the pair stays consistent across undo, redo, undo", () => {
  // Arrange
  const first = afterDeletingXColumn();
  // Act
  const second = applyUndo(first);
  assert.ok(second);
  const third = applyRedo(second);
  assert.ok(third);
  const fourth = applyUndo(third);
  // Assert: no step can leave a binding naming a column its table does not have.
  assert.ok(fourth);
  for (const state of [first, second, third, fourth]) {
    assert.equal(assignmentFitsTable(state.table, state.assignment), true);
  }
  assert.deepEqual(fourth.assignment, { x: "time", ys: ["signal"] });
});

// ── renaming an assigned column: same class of loss ───────────────────────

ok("undoing a rename restores the old name AND the binding that named it", () => {
  // Arrange: renaming the X column drops the binding (the name is gone).
  const before = fixture();
  const beforeAssignment = { x: "time", ys: ["signal"] };
  const afterTable = renameColumnAt(before, 1, "elapsed");
  const afterAssignment = reconcile(beforeAssignment, afterTable);
  const history: TableHistory = {
    table: afterTable,
    assignment: afterAssignment,
    undoStack: pushUndo([], {
      label: "Rename column 'time' to 'elapsed'",
      op: { kind: "rename-column", from: "time", to: "elapsed" },
      snapshot: before,
      assignment: beforeAssignment,
    }),
    redoStack: [],
  };
  // Act
  const undone = applyUndo(history);
  // Assert
  assert.ok(undone);
  assert.deepEqual(
    undone.table.columns.map((c) => c.name),
    ["subject", "time", "signal"],
  );
  assert.deepEqual(undone.assignment, { x: "time", ys: ["signal"] });
});

// ── edges ─────────────────────────────────────────────────────────────────

ok("undo and redo on empty stacks are no-ops, not errors", () => {
  // Arrange
  const history: TableHistory = {
    table: fixture(),
    assignment: { x: "time", ys: ["signal"] },
    undoStack: [],
    redoStack: [],
  };
  // Act / Assert
  assert.equal(applyUndo(history), null);
  assert.equal(applyRedo(history), null);
});

ok("undo does not mutate the state it was handed", () => {
  // Arrange
  const history = afterDeletingXColumn();
  const beforeNames = history.table.columns.map((c) => c.name);
  // Act
  applyUndo(history);
  // Assert
  assert.deepEqual(
    history.table.columns.map((c) => c.name),
    beforeNames,
    "the caller's table must be untouched",
  );
  assert.deepEqual(history.assignment, { x: null, ys: ["signal"] });
});

// ── the pane must apply the pair in one step ──────────────────────────────

ok("the pane snapshots the assignment with every edit", () => {
  // Arrange
  const pane = read("components/DataTablePane/DataTablePane.tsx");
  // Act / Assert
  assert.match(
    pane,
    /pushUndo\(stack, \{\s*label,\s*op,\s*snapshot: cloneTable\(table\),\s*assignment: cloneSelection\(badgeSelection\),?\s*\}\)/,
  );
});

ok("the pane's undo and redo go through the atomic transitions", () => {
  // Arrange
  const pane = read("components/DataTablePane/DataTablePane.tsx");
  // Act / Assert: one transition per gesture — no hand-built redo entry, and no
  // second step that restores the binding on its own.
  assert.match(pane, /applyUndo\(\{/);
  assert.match(pane, /applyRedo\(\{/);
  assert.match(pane, /setSelectionCommand\(\(c\) => \(\{/);
  assert.doesNotMatch(pane, /pushRedo\(/);
});

ok("the form applies the restored binding after the reconciler, not instead", () => {
  // Arrange
  const form = read("components/DataTablePane/PlotFromColumns.tsx");
  // Act / Assert: the reconciler runs on the new column set and would drop a
  // name the restored table has re-introduced; the explicit command therefore
  // has to be applied AFTER it, in the same commit.
  const reconcileAt = form.indexOf("reconcileSelection(s, tab.columns, tab.rows)");
  const commandAt = form.indexOf("setSelection(cloneSelection(selectionCommand.selection))");
  assert.ok(reconcileAt > 0, "the reconciler must still be there");
  assert.ok(commandAt > reconcileAt, "the explicit command must come after the reconciler");
  assert.match(form, /export interface SelectionCommand/);
});

ok("the pane hands the restored binding to the form", () => {
  // Arrange
  const pane = read("components/DataTablePane/DataTablePane.tsx");
  // Act / Assert
  assert.match(pane, /selectionCommand=\{selectionCommand\}/);
});

console.log(
  "\nAll table-assignment-history checks passed (" + passed + " assertion-groups).",
);
