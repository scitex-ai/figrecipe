/** Table edits for the Data pane.
 *
 * Every function is pure: the pane owns the React state and the persistence,
 * these decide what the next table looks like, what a change is called, and
 * what undo has to remember. Kept free of React and the @scitex/ui alias so it
 * runs under `node --experimental-strip-types`.
 */

import type { ColumnDef } from "../../types/editor.ts";

export type CellValue = string | number;

/** The editable shape of one data tab (`TabData` minus its identity). */
export interface TableModel {
  columns: ColumnDef[];
  rows: CellValue[][];
}

/** The shape @scitex/ui's DataTable takes, described structurally so this
 *  module does not have to import the component. */
export interface TableDataset {
  columns: string[];
  rows: Record<string, CellValue>[];
}

export interface CellCoordinates {
  row: number;
  col: number;
}

/** What an edit did, in terms a user would name it. */
export type TableOp =
  | { kind: "delete-rows"; rowNumbers: number[] }
  | { kind: "delete-column"; columnName: string }
  | { kind: "insert-row"; rowNumber: number }
  | { kind: "add-column"; columnName: string }
  | { kind: "duplicate-column"; columnName: string; newName: string }
  | { kind: "clear-cells"; count: number }
  | {
      kind: "edit-cells";
      count: number;
      columnName: string | null;
      rowNumber: number | null;
    }
  | { kind: "rename-column"; from: string; to: string }
  /** A change this module could not name more precisely (e.g. a paste that
   *  widened the table); the pane still keeps the snapshot. */
  | { kind: "set-table" };

export interface UndoEntry {
  /** Localised description of the op — the pane builds it with the i18n helper
   *  before pushing. */
  label: string;
  /** What this entry undoes, kept structured so the stack stays inspectable
   *  (tests and the toast read the same value). */
  op: TableOp;
  /** The table as it was BEFORE the op: an independent copy, never aliased. */
  snapshot: TableModel;
}

/** Undo is a safety net, not a history: capping it keeps a long editing
 *  session from pinning every intermediate table in memory. */
export const UNDO_LIMIT = 50;

// ---------------------------------------------------------------- basics

function copyColumns(columns: readonly ColumnDef[]): ColumnDef[] {
  return columns.map((c) => ({ ...c }));
}

/** Deep copy. Snapshots must never share arrays/objects with the live table,
 *  or a later edit would silently rewrite the state undo restores. */
export function cloneTable(table: TableModel): TableModel {
  return {
    columns: copyColumns(table.columns),
    rows: table.rows.map((row) => [...row]),
  };
}

/** Value equality over the editable shape (dtypes are hints, not data). */
export function tablesEqual(a: TableModel, b: TableModel): boolean {
  if (a.columns.length !== b.columns.length) return false;
  if (a.rows.length !== b.rows.length) return false;
  if (a.columns.some((c, i) => c.name !== b.columns[i].name)) return false;
  return a.rows.every((row, ri) => {
    const other = b.rows[ri];
    return row.length === other.length && row.every((v, ci) => v === other[ci]);
  });
}

/** The @scitex/ui DataTable input for a model. */
export function datasetFromTable(table: TableModel): TableDataset {
  return {
    columns: table.columns.map((c) => c.name),
    rows: table.rows.map((row) => {
      const record: Record<string, CellValue> = {};
      table.columns.forEach((column, ci) => {
        record[column.name] = row[ci] ?? "";
      });
      return record;
    }),
  };
}

/** A model from what the table reports back, keeping dtypes we already knew.
 *
 * The table may hand back columns the pane never created (pasting a wider
 * block grows the grid), so the dataset's own column list wins. */
export function tableFromDataset(
  dataset: TableDataset,
  previous: TableModel | null,
): TableModel {
  const columns: ColumnDef[] = dataset.columns.map((name) => {
    const known = previous?.columns.find((c) => c.name === name);
    if (known) return { ...known };
    return {
      name,
      dtype: inferColumnDtype(dataset.rows.map((row) => row[name] ?? "")),
    };
  });
  const rows = dataset.rows.map((row) =>
    columns.map((column) => row[column.name] ?? ""),
  );
  return { columns, rows };
}

/** "numeric" only when there is something numeric to point at: an empty column
 *  is a string column, so adding one never steals the default X selection. */
export function inferColumnDtype(values: readonly CellValue[]): string {
  const present = values.filter((v) => v !== "" && v !== null && v !== undefined);
  return present.length > 0 && present.every((v) => typeof v === "number")
    ? "numeric"
    : "string";
}

// ---------------------------------------------------------------- cells

/** Coerce an edited value the way the shared table and the backend do: a
 *  trimmed decimal literal becomes a number, anything else stays text. */
export function coerceCellValue(raw: string | number): CellValue {
  if (typeof raw === "number") return raw;
  const text = raw.trim();
  if (text === "") return "";
  // Number() alone accepts forms float() rejects ("0x10", "Infinity"); only
  // decimal/scientific literals round-trip through datatable/import.
  return /^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/.test(text) ? Number(text) : text;
}

/** Grow a row to cover a column index, then set the value. */
function setAt(row: readonly CellValue[], col: number, value: CellValue): CellValue[] {
  const next = [...row];
  while (next.length < col) next.push("");
  next[col] = value;
  return next;
}

/** Write one cell. Out-of-range writes return the table unchanged rather than
 *  throwing: the table can report a cell the model no longer has. */
export function setCellValue(
  table: TableModel,
  row: number,
  col: number,
  raw: string | number,
): TableModel {
  if (row < 0 || row >= table.rows.length || col < 0 || col >= table.columns.length) {
    return cloneTable(table);
  }
  const value = coerceCellValue(raw);
  return {
    columns: copyColumns(table.columns),
    rows: table.rows.map((r, ri) => (ri === row ? setAt(r, col, value) : [...r])),
  };
}

/** Every cell where two models disagree, in row-major order. */
export function changedCells(
  before: TableModel,
  after: TableModel,
): CellCoordinates[] {
  const changed: CellCoordinates[] = [];
  const rows = Math.max(before.rows.length, after.rows.length);
  for (let row = 0; row < rows; row++) {
    const cols = Math.max(
      before.rows[row]?.length ?? 0,
      after.rows[row]?.length ?? 0,
    );
    for (let col = 0; col < cols; col++) {
      const a = before.rows[row]?.[col] ?? "";
      const b = after.rows[row]?.[col] ?? "";
      if (a !== b) changed.push({ row, col });
    }
  }
  return changed;
}

// ---------------------------------------------------------------- rows

/** Move any index into the table's row range. */
function clampRow(table: TableModel, at: number): number {
  return Math.max(0, Math.min(at, table.rows.length));
}

/** Insert a blank row at `at` (0 inserts above the first row). */
export function insertRowAt(table: TableModel, at: number): TableModel {
  const rows = table.rows.map((row) => [...row]);
  rows.splice(clampRow(table, at), 0, table.columns.map(() => ""));
  return { columns: copyColumns(table.columns), rows };
}

/** Remove one row; an out-of-range index leaves the table as it was. */
export function deleteRowAt(table: TableModel, index: number): TableModel {
  return deleteRowsAt(table, [index]);
}

/** Remove several rows at once (duplicates and out-of-range values are
 *  dropped, so a stale selection cannot delete an unrelated row). */
export function deleteRowsAt(
  table: TableModel,
  indexes: readonly number[],
): TableModel {
  const doomed = new Set(
    indexes.filter((i) => Number.isInteger(i) && i >= 0 && i < table.rows.length),
  );
  return {
    columns: copyColumns(table.columns),
    rows: table.rows.filter((_, index) => !doomed.has(index)).map((row) => [...row]),
  };
}

/** The rendered values of one model row, as the table would show them. */
export function rowValuesAt(table: TableModel, index: number): CellValue[] {
  const row = table.rows[index];
  if (!row) return [];
  return table.columns.map((_, ci) => row[ci] ?? "");
}

/** Locate a model row from the values the table is showing.
 *
 * The table can sort its view, so a rendered row number is not the model
 * index. `preferred` wins when it still matches; a row that is gone, or one of
 * several identical rows, resolves to -1 so the caller refuses instead of
 * deleting the wrong row. */
export function findRowIndexByValues(
  table: TableModel,
  values: readonly CellValue[],
  preferred = -1,
): number {
  if (values.length === 0) return -1;
  const matches = (index: number): boolean => {
    const row = table.rows[index];
    if (!row) return false;
    if (row.length < values.length) return false;
    return values.every((v, ci) => text(row[ci]) === text(v));
  };
  if (matches(preferred)) return preferred;
  const found = table.rows.reduce<number[]>(
    (acc, _row, index) => (matches(index) ? [...acc, index] : acc),
    [],
  );
  return found.length === 1 ? found[0] : -1;
}

function text(value: CellValue | undefined): string {
  return value === undefined || value === null ? "" : String(value);
}

// ---------------------------------------------------------------- columns

/** A column name that is not taken yet: "mass", then "mass_2", "mass_3"… */
export function uniqueColumnName(
  columns: readonly ColumnDef[],
  wanted: string,
): string {
  const taken = new Set(columns.map((c) => c.name));
  const base = wanted.trim() || "column";
  if (!taken.has(base)) return base;
  let suffix = 2;
  while (taken.has(`${base}_${suffix}`)) suffix++;
  return `${base}_${suffix}`;
}

/** Append a column; existing rows get an empty cell rather than a short row. */
export function addColumn(table: TableModel, name = "column"): TableModel {
  const columns = copyColumns(table.columns);
  columns.push({
    name: uniqueColumnName(table.columns, name),
    dtype: "string",
  });
  return {
    columns,
    rows: table.rows.map((row) => [...row, ""]),
  };
}

/** Rename a column in place, keeping its cells. Blank/unknown names are no-ops
 *  so a half-typed rename never blanks a header. */
export function renameColumnAt(
  table: TableModel,
  index: number,
  name: string,
): TableModel {
  const trimmed = name.trim();
  if (index < 0 || index >= table.columns.length || trimmed === "") {
    return cloneTable(table);
  }
  const columns = copyColumns(table.columns);
  columns[index] = {
    ...columns[index],
    name: uniqueColumnName(
      columns.filter((_, i) => i !== index),
      trimmed,
    ),
  };
  return { columns, rows: table.rows.map((row) => [...row]) };
}

/** Remove a column and its cell from every row. */
export function deleteColumnAt(table: TableModel, index: number): TableModel {
  if (index < 0 || index >= table.columns.length) return cloneTable(table);
  return {
    columns: copyColumns(table.columns.filter((_, i) => i !== index)),
    rows: table.rows.map((row) => row.filter((_, ci) => ci !== index)),
  };
}

/** Copy a column — its definition and every cell — in right after the original.
 *
 * "Duplicate" is the operation that makes a table a scratchpad (take `mass`,
 * copy it, transform the copy); the operator acceptance for this card lists
 * create/rename/duplicate/delete as one set, so duplicate is not satisfied by
 * add-then-retype. The copy gets a unique name, so a duplicated column can never
 * collide with one that already exists. */
export function duplicateColumnAt(table: TableModel, index: number): TableModel {
  const source = table.columns[index];
  if (!source) return cloneTable(table);
  const columns = copyColumns(table.columns);
  columns.splice(index + 1, 0, {
    ...source,
    name: uniqueColumnName(table.columns, `${source.name}_copy`),
  });
  return {
    columns,
    rows: table.rows.map((row) => {
      const next = [...row];
      next.splice(index + 1, 0, row[index] ?? "");
      return next;
    }),
  };
}

export interface ColumnDeletePlan {
  /** Safe to delete straight away. */
  allowed: boolean;
  /** Deleting would empty the table's schema — ask the user first. */
  needsConfirm: boolean;
  columnName: string | null;
}

/** Decide how a column delete has to be handled.
 *
 * The last column is the only thing standing between the pane and a table with
 * no columns at all (nothing left to plot, nothing left to add), so it needs an
 * explicit confirm step instead of a silent, irreversible-looking delete. */
export function planColumnDelete(
  table: TableModel,
  index: number,
): ColumnDeletePlan {
  const column = table.columns[index];
  if (!column) return { allowed: false, needsConfirm: false, columnName: null };
  if (table.columns.length <= 1) {
    return { allowed: false, needsConfirm: true, columnName: column.name };
  }
  return { allowed: true, needsConfirm: false, columnName: column.name };
}

/** Which plot assignment a column currently carries.
 *
 * Deleting a column that is bound to X or Y must not leave the Data pane's
 * chips pointing at a column that no longer exists (operator acceptance 7692:
 * "show affected assignment, clear/update it atomically, never leave a stale
 * chip/plot binding"). The pane asks this BEFORE the delete so it can say what
 * the delete will affect, and the selection reconciler drops the name in the
 * same edit. */
export interface AssignmentImpact {
  /** The deleted column is the plot's X. */
  x: boolean;
  /** The deleted column is one of the plot's Y columns. */
  y: boolean;
  /** Either of the above — the delete touches the plot assignment. */
  affected: boolean;
}

export function assignmentImpact(
  selection: { x: string | null; ys: readonly string[] },
  removedName: string | null,
): AssignmentImpact {
  if (!removedName) return { x: false, y: false, affected: false };
  const x = selection.x === removedName;
  const y = selection.ys.includes(removedName);
  return { x, y, affected: x || y };
}

/** How to name the affected assignment in the user's own words. */
export function affectedAssignmentLabel(impact: AssignmentImpact): string {
  if (impact.x && impact.y) return "X and Y";
  if (impact.x) return "X";
  if (impact.y) return "Y";
  return "";
}

// ---------------------------------------------------------------- diff + undo

/** Name the change between two models; null when there is none.
 *
 * The pane adopts whatever the shared table reports, so this is what turns
 * "the table changed" into a label the user recognises and an undo entry. */
export function diffTable(
  before: TableModel,
  after: TableModel,
): TableOp | null {
  if (tablesEqual(before, after)) return null;

  const sameNames =
    before.columns.length === after.columns.length &&
    before.columns.every((c, i) => c.name === after.columns[i].name);
  if (!sameNames) {
    if (before.columns.length === after.columns.length) {
      const renamed = before.columns
        .map((c, i) => (c.name === after.columns[i].name ? -1 : i))
        .filter((i) => i >= 0);
      if (renamed.length === 1) {
        const i = renamed[0];
        return {
          kind: "rename-column",
          from: before.columns[i].name,
          to: after.columns[i].name,
        };
      }
    }
    return { kind: "set-table" };
  }

  const changed = changedCells(before, after);
  const first = changed[0];
  return {
    kind: "edit-cells",
    count: changed.length,
    columnName: first ? after.columns[first.col]?.name ?? null : null,
    rowNumber: first ? first.row + 1 : null,
  };
}

/** Push an entry, dropping the oldest one once the cap is reached. */
export function pushUndo(
  stack: readonly UndoEntry[],
  entry: UndoEntry,
): UndoEntry[] {
  const next = [...stack, entry];
  return next.length > UNDO_LIMIT ? next.slice(next.length - UNDO_LIMIT) : next;
}

/** Take the most recent entry. An empty stack is a no-op, not an error. */
export function popUndo(stack: readonly UndoEntry[]): {
  entry: UndoEntry | null;
  stack: UndoEntry[];
} {
  if (stack.length === 0) return { entry: null, stack: [] };
  return { entry: stack[stack.length - 1], stack: stack.slice(0, -1) };
}

// ---------------------------------------------------------------- redo

/** One redo step: the table as it was AFTER the edit that undo reversed.
 *
 * Undo alone is only half a destructive-edit story: the operator acceptance for
 * this card requires undo AND redo, because an undo is itself a change the user
 * may want back ("I deleted the wrong column, undid it, then wanted the delete
 * back"). The undo stack stores what to RESTORE going back; this stores what to
 * restore going forward. */
export interface RedoEntry {
  /** The same human-readable label the undo entry carried. */
  label: string;
  /** The table to put back when this entry is redone. */
  table: TableModel;
}

export const REDO_LIMIT = UNDO_LIMIT;

/** Push a redo entry with the same cap policy as undo. */
export function pushRedo(
  stack: readonly RedoEntry[],
  entry: RedoEntry,
): RedoEntry[] {
  const next = [...stack, entry];
  return next.length > REDO_LIMIT ? next.slice(next.length - REDO_LIMIT) : next;
}

/** Take the most recent redo entry; an empty stack is a no-op. */
export function popRedo(stack: readonly RedoEntry[]): {
  entry: RedoEntry | null;
  stack: RedoEntry[];
} {
  if (stack.length === 0) return { entry: null, stack: [] };
  return { entry: stack[stack.length - 1], stack: stack.slice(0, -1) };
}

// ---------------------------------------------------------------- persistence

/** One CSV field, quoted only when it has to be.
 *
 * This is the exact text `datatable/import` parses with Python's csv.reader,
 * and it re-reads numeric literals as numbers — so numbers stay unquoted and
 * plain text stays byte-identical. */
function csvField(value: CellValue): string {
  const text = typeof value === "number" ? String(value) : value;
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

/** The whole table as CSV, header row first — the write path for every edit
 *  (datatable/import replaces the stored table with it). */
export function serializeTableToCsv(table: TableModel): string {
  const lines = [table.columns.map((c) => csvField(c.name)).join(",")];
  for (const row of table.rows) {
    lines.push(table.columns.map((_, ci) => csvField(row[ci] ?? "")).join(","));
  }
  return lines.join("\n") + "\n";
}
