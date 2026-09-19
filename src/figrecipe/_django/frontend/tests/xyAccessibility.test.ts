/** Node test for the X/Y assignment's accessible surface in the Data pane.
 *
 * Card acceptance: the X/Y binding must be conveyed SEMANTICALLY, not by colour
 * alone. The table's highlight carried the role in a class and in
 * `data-col-highlight`, and the visible letter `X`/`Y` came from a CSS `::after`
 * rule — a generated-content glyph that is not in the accessibility tree, so a
 * screen reader read "mass" and never "the X column". This file pins the part
 * that is actually announced: the column header's accessible NAME states the
 * role, and the Y chips name the role they assign.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/xyAccessibility.test.ts
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  COLUMN_HIGHLIGHT_LABEL_ATTRIBUTE,
  applyColumnHighlight,
  columnRoleAriaLabel,
  type TableNode,
} from "../src/components/DataTablePane/dataTableDom.ts";
import type { ColumnHighlight } from "../src/components/DataTablePane/dataColumnHighlight.ts";

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel: string) =>
  readFileSync(join(here, "..", "src", rel), "utf8");

// ── fake nodes (same minimal TableNode the pane is written against) ────────

interface FakeNode extends TableNode {
  tokens(): string[];
}

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
      add: (...tokens) => tokens.forEach((token) => classes.add(token)),
      remove: (...tokens) => tokens.forEach((token) => classes.delete(token)),
      contains: (token) => classes.has(token),
    },
    tokens: () => [...classes].sort(),
  };
}

/** A header (data-col only) and a cell (data-col + data-row). */
function header(col: number, text: string) {
  return fakeNode({ "data-col": String(col) }, text);
}
function cell(col: number, row: number, text: string) {
  return fakeNode({ "data-row": String(row), "data-col": String(col) }, text);
}

const ROLE_WORDS = { x: "X column", y: "Y column" };
const height = (name: string, role: "x" | "y", preview = false): ColumnHighlight => ({
  index: role === "x" ? 2 : 0,
  name,
  role,
  preview,
});

console.log("xyAccessibility:");

// ── the role word the pane injects ────────────────────────────────────────

ok("a header's accessible name carries the column name AND the role", () => {
  // Arrange / Act
  const x = columnRoleAriaLabel("mass", "X column");
  const y = columnRoleAriaLabel("subject", "Y column");
  // Assert
  assert.equal(x, "mass, X column");
  assert.equal(y, "subject, Y column");
});

ok("an unnamed header still names the role instead of an empty label", () => {
  // Arrange / Act — the shared table can render a header whose text is not
  // readable (icon-only, or mid-rename).
  const label = columnRoleAriaLabel("", "X column");
  // Assert
  assert.equal(label, "X column");
});

// ── stamped on the header, not on every cell ──────────────────────────────

ok("the X column's header exposes the X role to assistive tech", () => {
  // Arrange
  const th = header(2, "mass");
  const td = cell(2, 0, "1.2");
  // Act
  applyColumnHighlight([th, td], [height("mass", "x")], ROLE_WORDS);
  // Assert
  assert.equal(th.getAttribute("aria-label"), "mass, X column");
  // The marker records the label we replaced — here: there was none.
  assert.equal(th.getAttribute(COLUMN_HIGHLIGHT_LABEL_ATTRIBUTE), "");
});

ok("the Y column's header exposes the Y role", () => {
  // Arrange
  const th = header(0, "subject");
  // Act
  applyColumnHighlight([th], [height("subject", "y")], ROLE_WORDS);
  // Assert
  assert.equal(th.getAttribute("aria-label"), "subject, Y column");
});

ok("cells are not given a label per cell — the role belongs to the column", () => {
  // Arrange
  const td = cell(2, 0, "1.2");
  // Act
  applyColumnHighlight([td], [height("mass", "x")], ROLE_WORDS);
  // Assert
  assert.equal(td.getAttribute("aria-label"), null);
  // The machine-readable role is still stamped on the cell (the highlight).
  assert.equal(td.getAttribute("data-col-highlight"), "x");
});

ok("the injected words are what is announced, not a hardcoded English phrase", () => {
  // Arrange: the pane passes translated role words (gettext), so the module
  // must not decide the copy itself.
  const th = header(2, "質量");
  // Act
  applyColumnHighlight([th], [height("質量", "x")], { x: "X列", y: "Y列" });
  // Assert
  assert.equal(th.getAttribute("aria-label"), "質量, X列");
});

ok("without injected words the raw role token is still announced", () => {
  // Arrange: the fallback keeps the module self-sufficient for callers that
  // have no i18n layer (and for this test).
  const th = header(2, "mass");
  // Act
  applyColumnHighlight([th], [height("mass", "x")]);
  // Assert
  assert.match(th.getAttribute("aria-label") ?? "", /mass.*X/);
});

// ── lifecycle: previews do not claim, clearing does not leave a lie ───────

ok("a hover preview never claims an assignment the column does not have", () => {
  // Arrange: the pointer is over the X badge, previewing an unassigned column.
  const th = header(1, "noise");
  // Act
  applyColumnHighlight([th], [height("noise", "x", true)], ROLE_WORDS);
  // Assert
  assert.equal(th.getAttribute("aria-label"), null);
});

ok("a preview does not erase a role the column really has", () => {
  // Arrange: hover the Y badge over a column that IS the Y column.
  const th = header(0, "subject");
  applyColumnHighlight([th], [height("subject", "y")], ROLE_WORDS);
  // Act
  applyColumnHighlight([th], [height("subject", "y", true)], ROLE_WORDS);
  // Assert
  assert.equal(th.getAttribute("aria-label"), "subject, Y column");
});

ok("clearing the highlight takes the announced role away with it", () => {
  // Arrange
  const th = header(2, "mass");
  applyColumnHighlight([th], [height("mass", "x")], ROLE_WORDS);
  // Act: the badge moves off the column (or the column is deleted).
  applyColumnHighlight([th], [], ROLE_WORDS);
  // Assert
  assert.equal(th.getAttribute("aria-label"), null);
  assert.equal(th.getAttribute(COLUMN_HIGHLIGHT_LABEL_ATTRIBUTE), null);
  assert.equal(th.getAttribute("data-col-highlight"), null);
});

ok("a label the pane did not stamp is left alone", () => {
  // Arrange: a header the shared table labelled for its own reasons.
  const th = fakeNode({ "data-col": "2", "aria-label": "mass" }, "mass");
  // Act: highlight, then clear.
  applyColumnHighlight([th], [height("mass", "x")], ROLE_WORDS);
  assert.equal(th.getAttribute("aria-label"), "mass, X column");
  assert.equal(th.getAttribute(COLUMN_HIGHLIGHT_LABEL_ATTRIBUTE), "mass");
  applyColumnHighlight([th], [], ROLE_WORDS);
  // Assert: the unstamped original is restored, not deleted.
  assert.equal(th.getAttribute("aria-label"), "mass");
});

ok("re-applying the same highlight never stacks role words", () => {
  // Arrange
  const th = header(2, "mass");
  // Act
  const highlights = [height("mass", "x")];
  applyColumnHighlight([th], highlights, ROLE_WORDS);
  applyColumnHighlight([th], highlights, ROLE_WORDS);
  applyColumnHighlight([th], highlights, ROLE_WORDS);
  // Assert
  assert.equal(th.getAttribute("aria-label"), "mass, X column");
});

// ── the pane must inject translated role words ─────────────────────────────

ok("the Data pane passes translated role words into the highlighter", () => {
  // Arrange
  const pane = read("components/DataTablePane/DataTablePane.tsx");
  // Act / Assert: the module stays free of gettext; the pane owns the copy.
  assert.match(pane, /gettext\("X column"\)/);
  assert.match(pane, /gettext\("Y column"\)/);
  assert.match(pane, /applyColumnHighlight\(renderedColumnNodes\(root\), highlights, \w+\)/);
});

// ── the Y chips name the role they assign ─────────────────────────────────

ok("a Y chip's accessible name says which role it toggles", () => {
  // Arrange
  const form = read("components/DataTablePane/PlotFromColumns.tsx");
  // Act / Assert: the chip's visible text is the column name; the accessible
  // name must CONTAIN it (WCAG 2.5.3) and add the Y role.
  assert.match(form, /aria-label=\{interpolate\(gettext\("Y column: %s"\), \[c\.name\]\)\}/);
  assert.match(form, /aria-pressed=\{selection\.ys\.includes\(c\.name\)\}/);
});

ok("the X chooser stays labelled by its own visible legend", () => {
  // Arrange
  const form = read("components/DataTablePane/PlotFromColumns.tsx");
  // Act / Assert: the <label> wraps the select and reads "X column", so the
  // control is already named; a second aria-label would only duplicate it.
  assert.match(form, /<label className="plot-from-columns__group">[\s\S]*?gettext\("X column"\)[\s\S]*?<select/);
  assert.doesNotMatch(form, /<select[\s\S]{0,200}?aria-label=/);
});

// ── the visual letter must survive the semantic one ───────────────────────

ok("the visible X/Y letter stays a style concern, not an accessibility one", () => {
  // Arrange
  const css = readFileSync(
    join(here, "..", "src", "styles", "panels", "datatable.css"),
    "utf8",
  );
  // Act / Assert: both signals exist — the announced name above, the glyph here.
  assert.match(css, /th\[data-col-highlight="x"\] > span::after\s*\{\s*content: "X";/);
  assert.match(css, /th\[data-col-highlight="y"\] > span::after\s*\{\s*content: "Y";/);
});

console.log(
  "\nAll X/Y accessibility checks passed (" + passed + " assertion-groups).",
);
