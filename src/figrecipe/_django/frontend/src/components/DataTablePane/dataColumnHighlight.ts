/** Column ↔ badge highlight policy for the Data pane.
 *
 * The pane shows the X/Y badges (PlotFromColumns) and the table side by side;
 * this decides which table column each badge points at and what clicking a
 * table column does to the badges. Kept free of React and the @scitex/ui alias
 * so it runs under `node --experimental-strip-types` — the JSX only renders
 * what this module decides.
 */

import type { ColumnDef } from "../../types/editor.ts";
import type { ColumnSelection } from "./columnPlotSelection.ts";

/** X is single-valued (the X <select>), Y is the chip list. */
export type ColumnRole = "x" | "y";

/** The badge the pointer is over — a transient preview, never a state change. */
export interface HoverBadge {
  name: string;
  role: ColumnRole;
}

/** One table column to stamp as highlighted, addressed by index. */
export interface ColumnHighlight {
  /** Index into the pane's column list — the same number the shared table
   *  renders as `data-col`, so the pane can find its cells without editing
   *  scitex-ui. */
  index: number;
  name: string;
  role: ColumnRole;
  /** True for a hover preview: highlighted, but not part of the selection. */
  preview: boolean;
}

/** Index of a column by name; -1 when the table has no such column.
 *
 * A badge can outlive its column (renamed or deleted under it), so callers get
 * "no highlight" instead of an exception or a wrong column. */
export function columnIndexByName(
  columns: readonly ColumnDef[],
  name: string | null | undefined,
): number {
  if (!name) return -1;
  return columns.findIndex((c) => c.name === name);
}

/** Name of the column at an index; null when the index is out of range. */
export function columnNameAt(
  columns: readonly ColumnDef[],
  index: number,
): string | null {
  return columns[index]?.name ?? null;
}

/** Same column *and* same role — used to skip re-renders on every mousemove. */
export function sameBadge(
  a: HoverBadge | null,
  b: HoverBadge | null,
): boolean {
  if (!a || !b) return a === b;
  return a.name === b.name && a.role === b.role;
}

/** Every table column a badge points at, in table order.
 *
 * `hover` previews the badge it belongs to, so a previewed column keeps its
 * role and never looks like a different kind of column. */
export function badgeColumnHighlights(
  columns: readonly ColumnDef[],
  selection: ColumnSelection,
  hover: HoverBadge | null = null,
): ColumnHighlight[] {
  const roles = new Map<string, ColumnRole>();
  if (selection.x) roles.set(selection.x, "x");
  for (const y of selection.ys) {
    // X wins when a name is somehow both.
    if (!roles.has(y)) roles.set(y, "y");
  }
  if (hover && roles.has(hover.name)) roles.set(hover.name, hover.role);

  const highlights: ColumnHighlight[] = [];
  columns.forEach((column, index) => {
    const role = roles.get(column.name);
    if (!role) return;
    highlights.push({
      index,
      name: column.name,
      role,
      preview: hover?.name === column.name,
    });
  });
  return highlights;
}

/** What clicking the table column called `name` does to the badges: a
 *  Y-badge column toggles Y, any other column becomes the X. */
export function selectionAfterColumnClick(
  selection: ColumnSelection,
  name: string,
): ColumnSelection {
  if (selection.ys.includes(name)) {
    return { x: selection.x, ys: selection.ys.filter((y) => y !== name) };
  }
  // A column already carrying the X badge stays X; the click is a no-op in
  // effect, which keeps a repeat click from clearing the plot selection.
  return { x: name, ys: selection.ys.filter((y) => y !== name) };
}
