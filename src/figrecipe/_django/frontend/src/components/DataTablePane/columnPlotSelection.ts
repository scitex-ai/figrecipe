/** Plot-from-columns decisions for the Data pane, kept free of React and the
 * @scitex/ui alias so they run under `node --experimental-strip-types`. */

import type { ColumnDef } from "../../types/editor.ts";

export interface DataPlotKind {
  /** The `plot_type` datatable/plot dispatches on. */
  id: string;
  /** The PlotTypeNav family whose icon and label this kind borrows. */
  family: string;
  /** Distribution kinds plot each Y column on its own; there is no X. */
  usesX: boolean;
}

export const DATA_PLOT_KINDS: DataPlotKind[] = [
  { id: "line", family: "line", usesX: true },
  { id: "scatter", family: "scatter", usesX: true },
  { id: "bar", family: "categorical", usesX: true },
  { id: "histogram", family: "distribution", usesX: false },
  { id: "boxplot", family: "statistical", usesX: false },
];

/** The data kind a rail family plots as; null when the family has none. */
export function kindForFamily(family: string | null): DataPlotKind | null {
  if (!family) return DATA_PLOT_KINDS[0];
  return DATA_PLOT_KINDS.find((k) => k.family === family) ?? null;
}

export function plotKind(id: string): DataPlotKind {
  return DATA_PLOT_KINDS.find((k) => k.id === id) ?? DATA_PLOT_KINDS[0];
}

function isNumericColumn(
  column: ColumnDef,
  index: number,
  rows: (string | number)[][],
): boolean {
  if (column.dtype) return column.dtype === "numeric";
  const present = rows.map((r) => r[index]).filter((v) => v !== "" && v != null);
  return present.length > 0 && present.every((v) => typeof v === "number");
}

export interface ColumnSelection {
  x: string | null;
  ys: string[];
}

/** First numeric column as X, the next numeric one as Y. */
export function defaultColumnSelection(
  columns: ColumnDef[],
  rows: (string | number)[][],
): ColumnSelection {
  const numeric = columns
    .filter((c, i) => isNumericColumn(c, i, rows))
    .map((c) => c.name);
  const pool = numeric.length > 0 ? numeric : columns.map((c) => c.name);
  if (pool.length === 0) return { x: null, ys: [] };
  if (pool.length === 1) return { x: null, ys: [pool[0]] };
  return { x: pool[0], ys: [pool[1]] };
}

/** Keep a selection valid after the table changes under it. */
export function reconcileSelection(
  current: ColumnSelection,
  columns: ColumnDef[],
  rows: (string | number)[][],
): ColumnSelection {
  const names = new Set(columns.map((c) => c.name));
  const ys = current.ys.filter((y) => names.has(y));
  const x = current.x && names.has(current.x) ? current.x : null;
  if (ys.length === 0) return defaultColumnSelection(columns, rows);
  return { x, ys };
}

export interface PlotRequest {
  plot_type: string;
  /** Present for x/y kinds; `null` plots against the row number. */
  x?: string | null;
  columns: string[];
}

export function buildPlotRequest(
  kindId: string,
  selection: ColumnSelection,
): PlotRequest | null {
  const kind = plotKind(kindId);
  const ys = kind.usesX
    ? selection.ys.filter((y) => y !== selection.x)
    : selection.ys;
  if (ys.length === 0) return null;
  if (kind.usesX) {
    return { plot_type: kind.id, x: selection.x, columns: ys };
  }
  return { plot_type: kind.id, columns: ys };
}
