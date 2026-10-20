/** Node test for the Data pane's phone touch targets, evaluated through the
 *  FINAL cascade — not by grepping one stylesheet.
 *
 * The bug this file exists for: `datatable.css` declared `.data-pane__btn {
 * min-height: 44px }` inside `@media (max-width: 768px)` and then declared the
 * base `.data-pane__btn { min-height: 26px }` LATER in the same file. Media
 * queries do not add specificity, so at equal specificity the later rule wins
 * and the phone CRUD toolbar stayed 26px tall — a rule that looked correct in
 * review and was dead in the browser.
 *
 * A test that greps for "44px" cannot see that. So this test implements the
 * part of the CSS cascade that decides it — source order across the stylesheet
 * import order, filtered by the width media conditions actually in use — and
 * asserts the declaration a 390px phone really ends up with.
 *
 * The cascade model is calibrated against declarations whose browser behaviour
 * is known: `.plot-from-columns__select` is 30px on desktop and 44px on a phone
 * (media rule AFTER its base rule), and `.data-pane__btn` is the broken one.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/dataPaneMobileTargets.test.ts
 */

import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

const here = dirname(fileURLToPath(import.meta.url));
const STYLES = join(here, "..", "src", "styles");

// ── the stylesheet order the browser really sees ───────────────────────────
// main.tsx imports these in this order; panels.css pulls its own children in.
// Verbatim from the source, so a reorder there fails this test rather than
// silently changing which declaration wins.

const MAIN_CSS_IMPORTS = [
  "app-variables.css",
  "layout.css",
  "context-menu.css",
  "canvas.css",
  "panels.css",
  "gallery.css",
  "export-dialog.css",
  "feedback.css",
  "mobile.css",
];

const read = (rel: string) => readFileSync(join(STYLES, rel), "utf8");

/** Expand `@import "./x.css";` in place, depth-first, in statement order. */
function flattenImports(rel: string, seen: string[] = []): string[] {
  if (seen.includes(rel)) return [];
  const css = read(rel);
  const out: string[] = [];
  css.replace(
    /@import\s+(?:url\()?["']([^"']+)["']\)?[^;]*;/g,
    (_m: string, target: string) => {
      const child = target.replace(/^\.\//, "");
      out.push(...flattenImports(child, [...seen, rel]));
      return "";
    },
  );
  out.push(rel);
  return out;
}

/** The full cascade, in the order the browser applies it. */
function stylesheetOrder(): string[] {
  const order: string[] = [];
  for (const entry of MAIN_CSS_IMPORTS) order.push(...flattenImports(entry));
  return order;
}

// ── a small CSS reader ────────────────────────────────────────────────────

interface CssRule {
  /** One comma-separated selector from the list, trimmed. */
  selector: string;
  declarations: Record<string, string>;
  /** The enclosing @media condition, or null for top level. */
  media: string | null;
  /** Position in the flattened cascade: the tie-breaker. */
  order: number;
}

function stripComments(css: string): string {
  return css.replace(/\/\*[\s\S]*?\*\//g, "");
}

/** Read every rule of one stylesheet, remembering @media nesting (the
 *  enclosing condition is inherited by the nested rules it contains). */
function parseRules(
  css: string,
  startOrder: number,
  enclosing: string | null = null,
): CssRule[] {
  const rules: CssRule[] = [];
  let order = startOrder;
  let i = 0;
  const text = stripComments(css);
  let media: string | null = enclosing;

  while (i < text.length) {
    const open = text.indexOf("{", i);
    if (open < 0) break;
    const prelude = text.slice(i, open).trim();
    const close = matchingBrace(text, open);
    if (close < 0) break;
    const body = text.slice(open + 1, close);

    if (prelude.startsWith("@media")) {
      const condition = prelude.slice("@media".length).trim();
      for (const rule of parseRules(body, order, condition)) rules.push(rule);
      order += countRules(body);
    } else if (prelude.startsWith("@")) {
      // @supports/@keyframes/@font-face: no simple selector to cascade.
      order += 1;
    } else {
      const declarations = parseDeclarations(body);
      for (const selector of prelude.split(",")) {
        rules.push({ selector: selector.trim(), declarations, media, order });
      }
      order += 1;
    }
    i = close + 1;
  }
  return rules;
}

/** Rules inside a block, for advancing the source-order counter. */
function countRules(body: string): number {
  let count = 0;
  let i = 0;
  while (i < body.length) {
    const open = body.indexOf("{", i);
    if (open < 0) break;
    const close = matchingBrace(body, open);
    if (close < 0) break;
    count += 1;
    i = close + 1;
  }
  return count;
}

function matchingBrace(text: string, open: number): number {
  let depth = 0;
  for (let i = open; i < text.length; i++) {
    if (text[i] === "{") depth++;
    else if (text[i] === "}") {
      depth--;
      if (depth === 0) return i;
    }
  }
  return -1;
}

function parseDeclarations(body: string): Record<string, string> {
  const declarations: Record<string, string> = {};
  for (const chunk of body.split(";")) {
    const at = chunk.indexOf(":");
    if (at < 0) continue;
    const name = chunk.slice(0, at).trim();
    const value = chunk.slice(at + 1).trim();
    if (name) declarations[name] = value;
  }
  return declarations;
}

/** (ids, classes+attributes, elements) — enough for the selectors in play. */
function specificity(selector: string): number {
  const ids = (selector.match(/#[\w-]+/g) ?? []).length;
  const classes = (
    selector.match(/\.[\w-]+|\[[^\]]+\]|:(?!:)[\w-]+(?:\([^)]*\))?/g) ?? []
  ).length;
  const elements = (
    selector
      .replace(/\[[^\]]*\]/g, " ")
      .replace(/\.[\w-]+/g, " ")
      .replace(/::?[\w-]+(?:\([^)]*\))?/g, " ")
      .match(/(^|[\s>+~])([a-zA-Z][\w-]*)/g) ?? []
  ).length;
  return ids * 10000 + classes * 100 + elements;
}

/** Does this @media condition match a viewport of `width`? */
function mediaMatches(media: string | null, width: number): boolean {
  if (!media) return true;
  return media
    .split(/\b(?:and|or)\b/)
    .map((part) => part.trim().replace(/^\(|\)$/g, "").trim())
    .filter(Boolean)
    .every((condition) => {
      const max = condition.match(/^max-width:\s*(\d+)px$/);
      if (max) return width <= Number(max[1]);
      const min = condition.match(/^min-width:\s*(\d+)px$/);
      if (min) return width >= Number(min[1]);
      throw new Error(`unsupported media condition: ${condition}`);
    });
}

/** The declaration a viewport of `width` ends up with, or null.
 *
 * `selectors` is the ELEMENT's own selector list: an element carrying both
 * `.data-pane__btn` and `.data-pane__btn--danger` is matched by rules for
 * either class, which is how the confirm button gets its height. */
function computed(
  rules: readonly CssRule[],
  selectors: string | readonly string[],
  property: string,
  width: number,
): string | null {
  const wanted = new Set(
    typeof selectors === "string" ? [selectors] : selectors,
  );
  const matching = rules.filter(
    (rule) => wanted.has(rule.selector) && mediaMatches(rule.media, width),
  );
  let winner: { value: string; rank: number; order: number } | null = null;
  for (const rule of matching) {
    const raw = rule.declarations[property];
    if (raw === undefined) continue;
    const important = raw.includes("!important");
    const rank = specificity(rule.selector) + (important ? 100000 : 0);
    if (!winner || rank > winner.rank || (rank === winner.rank && rule.order >= winner.order)) {
      winner = { value: raw, rank, order: rule.order };
    }
  }
  return winner ? winner.value : null;
}

function px(value: string | null): number {
  const match = value?.match(/^(-?[\d.]+)px$/);
  assert.ok(match, `expected a px value, got ${JSON.stringify(value)}`);
  return Number(match![1]);
}

const ORDER = stylesheetOrder();
const RULES = ORDER.flatMap((rel, index) =>
  parseRules(read(rel), index * 10000),
);

console.log("dataPaneMobileTargets:");

// ── cascade model calibration ─────────────────────────────────────────────

ok("the flattened order is main.tsx's import order, imports expanded in place", () => {
  // Arrange / Act / Assert
  assert.equal(ORDER[0], "app-variables.css");
  assert.ok(ORDER.includes("panels/datatable.css"));
  assert.ok(ORDER.includes("mobile.css"));
  // panels.css is an orchestrator: its children sit where it sits, before the
  // files main.tsx imports after it.
  assert.ok(
    ORDER.indexOf("panels/datatable.css") < ORDER.indexOf("gallery.css"),
    "panels.css children must be applied before gallery.css",
  );
  assert.ok(
    ORDER.indexOf("mobile.css") > ORDER.indexOf("panels/datatable.css"),
    "mobile.css is imported last",
  );
});

ok("the model reproduces declarations whose browser behaviour is known", () => {
  // Arrange: these two are correct today (media rule AFTER the base rule), so a
  // model that mis-orders source would disagree with the browser here first.
  // Act / Assert
  assert.equal(px(computed(RULES, ".plot-from-columns__select", "min-height", 390)), 44);
  assert.equal(px(computed(RULES, ".plot-from-columns__select", "min-height", 1440)), 30);
  assert.equal(px(computed(RULES, ".plot-from-columns__submit", "min-height", 390)), 44);
  assert.equal(px(computed(RULES, ".plot-from-columns__submit", "min-height", 1440)), 30);
});

ok("every stylesheet that declares a target is inside the modelled order", () => {
  // Arrange: a file outside the order could override the target unseen.
  const onDisk: string[] = [];
  const walk = (dir: string, prefix = "") => {
    for (const entry of readdirSync(join(STYLES, dir), { withFileTypes: true })) {
      const rel = prefix ? `${prefix}/${entry.name}` : entry.name;
      if (entry.isDirectory()) walk(join(dir, entry.name), rel);
      else if (entry.name.endsWith(".css")) onDisk.push(rel);
    }
  };
  walk(".");
  // Act: a stylesheet is modelled when it is in the flattened order.
  const declaring = onDisk.filter(
    (rel) =>
      /\.data-pane__btn\b|\.data-pane__prompt-input\b/.test(read(rel)),
  );
  // Assert
  for (const rel of declaring) {
    assert.ok(ORDER.includes(rel), `${rel} declares a CRUD target but is not in the cascade order`);
  }
});

// ── the CRUD targets the acceptance requires at 44px on a phone ───────────

console.log("  -- .data-pane__btn (add/delete row, add/rename/duplicate/delete column)");

ok("a 390px phone gets 44px CRUD buttons, not the 26px desktop size", () => {
  // Arrange / Act
  const phone = px(computed(RULES, ".data-pane__btn", "min-height", 390));
  // Assert
  assert.equal(phone, 44, "the phone CRUD toolbar must meet the 44px touch target");
});

ok("the 768px boundary is still the phone layout", () => {
  // Arrange / Act / Assert
  assert.equal(px(computed(RULES, ".data-pane__btn", "min-height", 768)), 44);
});

ok("desktop keeps its compact 26px toolbar", () => {
  // Arrange / Act — the fix must not inflate the desktop chrome.
  const desktop = px(computed(RULES, ".data-pane__btn", "min-height", 1440));
  // Assert
  assert.equal(desktop, 26);
});

ok("the phone CRUD type is legible, not the 11px desktop size", () => {
  // Arrange / Act / Assert
  assert.equal(px(computed(RULES, ".data-pane__btn", "font-size", 390)), 13);
  assert.equal(px(computed(RULES, ".data-pane__btn", "font-size", 1440)), 11);
});

ok("the rename/confirm prompt buttons are CRUD targets too", () => {
  // Arrange: the confirm button carries both classes, and each contributes
  // declarations to the element's computed style.
  const confirmButton = [".data-pane__btn", ".data-pane__btn--danger"];
  // Act / Assert
  assert.equal(px(computed(RULES, confirmButton, "min-height", 390)), 44);
  assert.equal(px(computed(RULES, confirmButton, "min-height", 1440)), 26);
});

ok("the rename input is a 44px target and 14px text on a phone", () => {
  // Arrange / Act
  const phone = px(computed(RULES, ".data-pane__prompt-input", "min-height", 390));
  const text = px(computed(RULES, ".data-pane__prompt-input", "font-size", 390));
  // Assert
  assert.equal(phone, 44, "the rename field is part of the same CRUD flow");
  assert.equal(text, 14);
  assert.equal(px(computed(RULES, ".data-pane__prompt-input", "min-height", 1440)), 26);
});

ok("the toolbar wraps rather than overflowing the phone width", () => {
  // Arrange / Act / Assert
  assert.equal(computed(RULES, ".data-pane__toolbar", "flex-wrap", 390), "wrap");
});

// ── the shape of the fix: the phone block must win the final cascade ──────

ok("the phone declarations for the CRUD targets come after every base rule", () => {
  // Arrange: this is the actual defect — a media block placed before the base
  // rule it was meant to override.
  const lastBase = Math.max(
    ...RULES.filter(
      (rule) =>
        rule.selector === ".data-pane__btn" &&
        rule.media === null &&
        "min-height" in rule.declarations,
    ).map((rule) => rule.order),
  );
  const phoneRule = RULES.find(
    (rule) =>
      rule.selector === ".data-pane__btn" &&
      rule.media !== null &&
      rule.declarations["min-height"] === "44px",
  );
  // Act / Assert
  assert.ok(phoneRule, "a phone rule must keep the 44px target");
  assert.ok(
    phoneRule!.order > lastBase,
    "the 44px phone rule must be declared after the base rule it overrides",
  );
});

console.log(
  "\nAll data-pane mobile target checks passed (" + passed + " assertion-groups).",
);
