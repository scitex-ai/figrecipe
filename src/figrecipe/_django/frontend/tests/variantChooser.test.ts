/** Node test for the category → variant chooser decisions (card
 * figrecipe-data-column-and-plot-variant-ux-20260916).
 *
 * The chooser replaces the rail's read-only hover list (TODO 130): it shows a
 * category's variants as thumbnails and lets you pick one. The reveal gesture,
 * the on-screen placement and the keyboard contract are pure decisions in
 * `variantChooser`, so they are checked here without a browser.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/variantChooser.test.ts
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  chooserAvailable,
  chooserOffersDataRoute,
  chooserPlacement,
  choiceKeyAction,
  revealMode,
  variantChoices,
} from "../src/components/Gallery/variantChooser.ts";
import type { GalleryData } from "../src/components/Gallery/useGalleryTemplates.ts";

// The shape the live gallery serves (handlers/gallery.py): line/categorical/
// distribution/special hold several variants, scatter/statistical/contour one,
// vector NONE.
const data: GalleryData = {
  categories: {
    line: [
      { name: "plot_plot", label: "Line", icon: "i", path: "a", has_thumbnail: true },
      { name: "plot_fill_between", label: "Fill Between", icon: "i", path: "b", has_thumbnail: false },
      { name: "plot_stackplot", label: "Stack", icon: "i", path: "c", has_thumbnail: true },
    ],
    scatter: [
      { name: "plot_scatter", label: "Scatter", icon: "i", path: "d", has_thumbnail: true },
    ],
    vector: [],
  },
};

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

console.log("variant chooser (category -> variant thumbnails):");

// ---- the variants a category offers -------------------------------------

ok("multi-variant category -> every variant, in gallery order", () => {
  assert.deepEqual(
    variantChoices(data, "line").map((c) => c.name),
    ["plot_plot", "plot_fill_between", "plot_stackplot"],
  );
});

ok("a choice carries what the panel and addTemplate need", () => {
  const [first] = variantChoices(data, "line");
  // Structural GalleryTemplate: addTemplate(tmpl) consumes name/path, the
  // panel shows label/icon and decides <img> vs placeholder on has_thumbnail.
  assert.equal(first.label, "Line");
  assert.equal(first.path, "a");
  assert.equal(first.has_thumbnail, true);
});

ok("single-variant category -> that one", () => {
  assert.deepEqual(
    variantChoices(data, "scatter").map((c) => c.name),
    ["plot_scatter"],
  );
});

ok("category with no templates / unknown category -> empty", () => {
  assert.deepEqual(variantChoices(data, "vector"), []);
  assert.deepEqual(variantChoices(data, "nope"), []);
});

ok("gallery not loaded yet -> empty (do not offer an undetermined set)", () => {
  assert.deepEqual(variantChoices(null, "line"), []);
});

ok("chooserAvailable: only when loaded AND the category has variants", () => {
  assert.equal(chooserAvailable(data, "line"), true);
  assert.equal(chooserAvailable(data, "vector"), false);
  assert.equal(chooserAvailable(data, null), false);
  assert.equal(chooserAvailable(null, "line"), false);
});

// ---- reveal gesture ------------------------------------------------------

ok("fine pointer with hover -> hover reveal (desktop)", () => {
  assert.equal(revealMode({ hover: true, coarse: false }), "hover");
});

ok("coarse pointer -> tap reveal (phone/tablet)", () => {
  assert.equal(revealMode({ hover: false, coarse: true }), "tap");
});

ok("no hover reported -> tap reveal (keyboard-only/unknown device)", () => {
  assert.equal(revealMode({ hover: false, coarse: false }), "tap");
});

ok("touch laptop (coarse AND hover) -> tap: a touch user cannot hold a hover", () => {
  assert.equal(revealMode({ hover: true, coarse: true }), "tap");
});

// ---- placement -----------------------------------------------------------

const rail = { top: 100, left: 0, right: 56, bottom: 140, width: 56, height: 40 };
const panel = { width: 240, height: 200 };
const viewport = { width: 1280, height: 800 };

ok("room to the right of the rail -> right, vertically centred on the item", () => {
  const p = chooserPlacement(rail, panel, viewport);
  assert.equal(p.side, "right");
  assert.equal(p.left, rail.right + 8);
  assert.equal(p.top, 120 - 100); // centre 120, minus half the panel height
});

ok("no room right but room left -> flips to the left, fully visible", () => {
  const wide = { width: 420, height: 200 };
  const nearRight = { top: 100, left: 900, right: 1000, bottom: 140, width: 100, height: 40 };
  const p = chooserPlacement(nearRight, wide, viewport);
  assert.equal(p.side, "left");
  assert.equal(p.left, nearRight.left - 8 - wide.width);
  assert.ok(p.left >= 8);
});

ok("phone width where the panel still fits -> sits right of the rail, not clamped", () => {
  const p = chooserPlacement(rail, panel, { width: 320, height: 640 });
  assert.equal(p.side, "right");
  assert.equal(p.left, rail.right + 8);
  assert.ok(p.left + panel.width <= 320 - 8);
});

ok("viewport narrower than the panel -> pinned to the left margin, still finite", () => {
  const p = chooserPlacement(rail, panel, { width: 200, height: 640 });
  // maxLeft collapses to the margin: pinning it there keeps the heading and the
  // first column of thumbnails readable instead of drifting off the right edge.
  assert.equal(p.left, 8);
  assert.ok(Number.isFinite(p.top));
  assert.ok(p.maxHeight > 0);
});

ok("item near the top -> top clamped to the margin (never negative)", () => {
  const p = chooserPlacement({ top: 0, left: 0, right: 56, bottom: 20, width: 56, height: 20 }, panel, viewport);
  assert.equal(p.top, 8);
});

ok("item near the bottom -> top clamped so the panel stays on screen", () => {
  const p = chooserPlacement({ top: 780, left: 0, right: 56, bottom: 800, width: 56, height: 20 }, panel, viewport);
  assert.equal(p.top, viewport.height - panel.height - 8);
  assert.ok(p.top + panel.height <= viewport.height - 8 + 0.0001);
});

ok("a deliberately tiny viewport still yields a usable, finite panel", () => {
  const p = chooserPlacement(rail, panel, { width: 100, height: 80 });
  assert.ok(Number.isFinite(p.top) && Number.isFinite(p.left));
  assert.ok(p.left >= 8 && p.top >= 8);
  assert.ok(p.maxHeight >= 120);
});

ok("maxHeight leaves room above and below the panel", () => {
  const p = chooserPlacement(rail, panel, viewport);
  assert.equal(p.maxHeight, viewport.height - 16);
});

// ---- keyboard contract ---------------------------------------------------

ok("arrows move and wrap at both ends", () => {
  assert.equal(choiceKeyAction("ArrowDown", 0, 3).index, 1);
  assert.equal(choiceKeyAction("ArrowDown", 2, 3).index, 0);
  assert.equal(choiceKeyAction("ArrowRight", 0, 2).index, 1);
  assert.equal(choiceKeyAction("ArrowUp", 0, 3).index, 2);
  assert.equal(choiceKeyAction("ArrowLeft", 1, 2).index, 0);
});

ok("Home/End jump to the ends", () => {
  assert.deepEqual(choiceKeyAction("Home", 2, 4), { index: 0, action: "move" });
  assert.deepEqual(choiceKeyAction("End", 0, 4), { index: 3, action: "move" });
});

ok("Enter and Space choose the highlighted variant", () => {
  assert.deepEqual(choiceKeyAction("Enter", 1, 3), { index: 1, action: "choose" });
  assert.deepEqual(choiceKeyAction(" ", 2, 3), { index: 2, action: "choose" });
});

ok("Escape dismisses, Tab keeps the browser's focus handling", () => {
  assert.deepEqual(choiceKeyAction("Escape", 1, 3), { index: 1, action: "dismiss" });
  assert.deepEqual(choiceKeyAction("Tab", 1, 3), { index: 1, action: "ignore" });
  assert.deepEqual(choiceKeyAction("x", 1, 3), { index: 1, action: "ignore" });
});

ok("an empty list can never choose", () => {
  assert.deepEqual(choiceKeyAction("Enter", 4, 0), { index: 0, action: "ignore" });
  assert.deepEqual(choiceKeyAction("ArrowDown", 0, 0), { index: 0, action: "ignore" });
});

ok("a stale index is clamped, so a rebuilt list cannot choose the wrong variant", () => {
  assert.deepEqual(choiceKeyAction("Enter", 99, 3), { index: 2, action: "choose" });
  assert.deepEqual(choiceKeyAction("Enter", -5, 3), { index: 0, action: "choose" });
  assert.deepEqual(choiceKeyAction("ArrowDown", 99, 3), { index: 0, action: "move" });
});

// ---- the data route the chooser has to carry on touch --------------------

ok("data route offered only for a plottable kind AND a loaded table", () => {
  assert.equal(chooserOffersDataRoute("bar", true), true);
  assert.equal(chooserOffersDataRoute("bar", false), false);
  // "grid"/"special" have no data kind: nothing to plot from columns.
  assert.equal(chooserOffersDataRoute(null, true), false);
  assert.equal(chooserOffersDataRoute(null, false), false);
});

// ---- conformance: the rail must actually be wired to the chooser ----------

const sql = (rel: string) =>
  readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), "..", "src", rel),
    "utf8",
  );

ok("the rail threads the anchor + pin into the chooser", () => {
  const rail = sql("components/PlotTypeNav/PlotTypeNav.tsx");
  assert.match(rail, /<VariantChooser[\s\S]*anchor=\{reveal\.anchor\}/);
  assert.match(rail, /pinned=\{reveal\.pinned\}/);
  // The reveal decision is the pure helper, not something re-derived in JSX.
  assert.match(rail, /revealMode\(usePointerCaps\(\)\)/);
  // The old read-only label list must be gone with the panel it belonged to.
  assert.doesNotMatch(rail, /plot-type-nav__hover/);
});

ok("the chooser is portalled and named for assistive tech", () => {
  const panel = sql("components/Gallery/VariantChooser.tsx");
  // Inside the scrolling phone layout an in-flow panel was clipped.
  assert.match(panel, /createPortal\(/);
  assert.match(panel, /document\.body/);
  assert.match(panel, /role="dialog"/);
  assert.match(panel, /aria-label=\{interpolate\(gettext\("%s variants"\), \[familyLabel\]\)\}/);
});

// ---- conformance: the module must stay node-runnable ---------------------

ok("module is dependency-free (no react / @scitex/ui import)", () => {
  const src = readFileSync(
    join(
      dirname(fileURLToPath(import.meta.url)),
      "..",
      "src",
      "components",
      "Gallery",
      "variantChooser.ts",
    ),
    "utf8",
  );
  // Only `import type` may cross into files that need the app alias; a VALUE
  // import of react or @scitex/ui would make this test unrunnable, which is the
  // whole reason the decision lives in its own module.
  const valueImports = src
    .split("\n")
    .filter((l) => /^import\b/.test(l) && !/^import\s+type\b/.test(l));
  assert.deepEqual(valueImports, [
    'import { familyHasExamples, familyTemplates } from "./familyExamples.ts";',
  ]);
});

console.log("\n" + passed + " assertion-groups passed");
