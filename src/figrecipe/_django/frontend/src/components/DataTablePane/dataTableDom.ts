/** DOM plumbing between the Data pane and the shared scitex-ui DataTable.
 *
 * The shared table keeps its selection and highlight state internal and exposes
 * no hook for them, so the pane reads what it needs back out of the nodes the
 * table rendered and stamps its own highlight on them.
 *
 * Everything here works on the flat list of nodes carrying `data-col` /
 * `data-row`, which keeps the real DOM touch to one line (renderedColumnNodes)
 * and the decisions testable under `node --experimental-strip-types` — a test
 * hands in a hand-written node object, no DOM required.
 */

import type { ColumnHighlight, ColumnRole } from "./dataColumnHighlight.ts";
import type { CellCoordinates } from "./dataTableEdit.ts";

/** Marks a cell/header as part of a highlighted column. The role is machine and
 *  screen-reader readable, so the highlight is never signalled by colour alone. */
export const COLUMN_HIGHLIGHT_ATTRIBUTE = "data-col-highlight";

/** Records the accessible name the pane itself put on a header, together with
 *  whatever label was there before, so clearing a highlight can put the node
 *  back exactly as it was found (see clearColumnRoleLabel). */
export const COLUMN_HIGHLIGHT_LABEL_ATTRIBUTE = "data-col-highlight-label";

/** The role words the pane injects into the announced label.
 *
 *  The copy lives in the pane, which owns gettext with the rest of the UI: this
 *  module stays free of the i18n layer (see the hygiene assertions in
 *  tests/dataTableDom.test.ts) and announces what it is given. */
export interface ColumnRoleWords {
  x: string;
  y: string;
}

/** Fallback for a caller that injects no words: the tokens the app already puts
 *  on its badges and buttons. */
export const DEFAULT_ROLE_WORDS: ColumnRoleWords = { x: "X", y: "Y" };

/** Every class the pane may stamp on a column. Removed en bloc before each
 *  re-apply, so a column that stops being highlighted keeps no stale token. */
export const COLUMN_HIGHLIGHT_CLASSES = [
  "data-pane__col--x",
  "data-pane__col--y",
  "data-pane__col--preview",
] as const;

/** The class the shared table puts on every cell of the current selection. */
const SELECTED_CELL_CLASS = "stx-app-data-table__cell--selected";

/** Headers and cells alike: the column identity is all this module needs. */
const COLUMN_NODE_SELECTOR = "[data-col]";

/** The only node members this module touches. A real element satisfies this
 *  as-is; a Node test can pass a hand-written object. */
export interface TableNode {
  getAttribute(name: string): string | null;
  setAttribute(name: string, value: string): void;
  removeAttribute(name: string): void;
  classList: {
    add(...tokens: string[]): void;
    remove(...tokens: string[]): void;
    contains(token: string): boolean;
  };
  textContent: string | null;
}

/** Every header and cell the table rendered, in document order.
 *
 * The one place this module touches the DOM: scitex-ui renders `data-col` on
 * both headers and cells, which is the hook the pane builds on. */
export function renderedColumnNodes(root: ParentNode): TableNode[] {
  return Array.from(root.querySelectorAll<HTMLElement>(COLUMN_NODE_SELECTOR));
}

/** The accessible name of an assigned column's header.
 *
 *  The visible letter is a CSS `::after` glyph, which is generated content and
 *  not part of the accessibility tree, so a screen reader reading the header
 *  used to hear the column name and nothing about the axis it is bound to. The
 *  name is what is actually announced: the column's own text, then the role. */
export function columnRoleAriaLabel(headerText: string, roleWord: string): string {
  const text = (headerText ?? "").trim();
  return text ? `${text}, ${roleWord}` : roleWord;
}

/** A header carries a column and no row (see readSelectedCells, which relies on
 *  the same distinction). Only headers state the role: labelling every cell of
 *  the column would repeat it on each of hundreds of nodes. */
function isHeaderNode(node: TableNode): boolean {
  return node.getAttribute("data-row") === null;
}

/** Announce the column's assignment on its header.
 *
 *  Idempotent, and it remembers the label it replaced: a node the shared table
 *  labelled for its own reasons gets that label back when the highlight goes. */
function stampColumnRoleLabel(
  node: TableNode,
  role: ColumnRole,
  roleWords: ColumnRoleWords,
): void {
  if (!isHeaderNode(node)) return;
  if (node.getAttribute(COLUMN_HIGHLIGHT_LABEL_ATTRIBUTE) === null) {
    // "" (rather than absence) records "we stamped it and there was no label".
    node.setAttribute(
      COLUMN_HIGHLIGHT_LABEL_ATTRIBUTE,
      node.getAttribute("aria-label") ?? "",
    );
  }
  node.setAttribute(
    "aria-label",
    columnRoleAriaLabel(node.textContent ?? "", roleWords[role]),
  );
}

/** Take the pane's label back off, restoring whatever the node carried before
 *  (and deleting only a label this module created). */
function clearColumnRoleLabel(node: TableNode): void {
  const original = node.getAttribute(COLUMN_HIGHLIGHT_LABEL_ATTRIBUTE);
  if (original === null) return;
  node.removeAttribute(COLUMN_HIGHLIGHT_LABEL_ATTRIBUTE);
  if (original === "") node.removeAttribute("aria-label");
  else node.setAttribute("aria-label", original);
}

/** Highlight every rendered cell and header of the named columns, and clear the
 *  ones that are no longer named.
 *
 * Idempotent: re-running it (which the pane does on every commit and on every
 * table DOM change) writes only what differs, so it cannot feed itself. */
export function applyColumnHighlight(
  nodes: readonly TableNode[],
  highlights: readonly ColumnHighlight[],
  roleWords: ColumnRoleWords = DEFAULT_ROLE_WORDS,
): void {
  const byIndex = new Map<number, ColumnHighlight>();
  for (const highlight of highlights) byIndex.set(highlight.index, highlight);

  for (const node of nodes) {
    const rawIndex = node.getAttribute("data-col");
    const index = rawIndex === null ? NaN : Number(rawIndex);
    const highlight = byIndex.get(index);

    node.classList.remove(...COLUMN_HIGHLIGHT_CLASSES);
    if (!highlight) {
      node.removeAttribute(COLUMN_HIGHLIGHT_ATTRIBUTE);
      clearColumnRoleLabel(node);
      continue;
    }
    node.classList.add(`data-pane__col--${highlight.role}`);
    if (highlight.preview) node.classList.add("data-pane__col--preview");
    node.setAttribute(COLUMN_HIGHLIGHT_ATTRIBUTE, highlight.role);
    // A hover preview neither stamps nor clears: it is a transient pointer
    // state, and the column's real binding must keep being announced while the
    // pointer passes over a badge.
    if (!highlight.preview) {
      stampColumnRoleLabel(node, highlight.role, roleWords);
    }
  }
}

/** The cells the table currently shows as selected (one click or a dragged
 *  range), read back because the selection never leaves the component. */
export function readSelectedCells(
  nodes: readonly TableNode[],
): CellCoordinates[] {
  const cells: CellCoordinates[] = [];
  for (const node of nodes) {
    if (!node.classList.contains(SELECTED_CELL_CLASS)) continue;
    const rawRow = node.getAttribute("data-row");
    const rawCol = node.getAttribute("data-col");
    // A header carries a column but no row: without this guard Number(null)
    // would read as row 0 and pull the header into the selection.
    if (rawRow === null || rawCol === null) continue;
    const row = Number(rawRow);
    const col = Number(rawCol);
    if (Number.isInteger(row) && Number.isInteger(col)) cells.push({ row, col });
  }
  return cells;
}

/** The rendered values of one table row, in column order.
 *
 * The table can sort its view, so a row number in the DOM is not necessarily
 * the model index; the caller matches these values back against the model. */
export function readRowValues(nodes: readonly TableNode[], row: number): string[] {
  const values: string[] = [];
  for (const node of nodes) {
    const rawRow = node.getAttribute("data-row");
    if (rawRow === null || Number(rawRow) !== row) continue;
    const rawCol = node.getAttribute("data-col");
    if (rawCol === null) continue;
    const col = Number(rawCol);
    if (!Number.isInteger(col)) continue;
    values[col] = node.textContent ?? "";
  }
  // A hole would make Array#every skip that column and shift the comparison,
  // so missing columns become empty strings.
  for (let col = 0; col < values.length; col++) {
    if (values[col] === undefined) values[col] = "";
  }
  return values;
}
