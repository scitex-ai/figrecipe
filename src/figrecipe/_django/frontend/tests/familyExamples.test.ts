/** Node test for a plot family's template list.
 *
 * The list feeds the rail's variant chooser (card
 * figrecipe-data-column-and-plot-variant-ux-20260916): which variants a
 * category offers, and whether the chooser should open for it at all. Run under
 * Node strip-types (no React/DOM/SelectorNav):
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/familyExamples.test.ts
 */

import assert from "node:assert/strict";

import {
  familyHasExamples,
  familyTemplates,
} from "../src/components/Gallery/familyExamples.ts";
import type { GalleryData } from "../src/components/Gallery/useGalleryTemplates.ts";

// Matches the live gallery (handlers/gallery.py GALLERY_TEMPLATES, filtered to
// on-disk templates): line/categorical/distribution/special have several,
// scatter/statistical/contour one each, vector NONE.
const data: GalleryData = {
  categories: {
    line: [
      { name: "plot_plot", label: "Line", icon: "i", path: "a", has_thumbnail: false },
      { name: "plot_fill_between", label: "Fill Between", icon: "i", path: "b", has_thumbnail: false },
      { name: "plot_stackplot", label: "Stack", icon: "i", path: "c", has_thumbnail: false },
    ],
    scatter: [{ name: "plot_scatter", label: "Scatter", icon: "i", path: "d", has_thumbnail: false }],
    vector: [],
    statistical: [{ name: "plot_errorbar", label: "Error Bar", icon: "i", path: "e", has_thumbnail: false }],
  },
};

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

console.log("family templates (variant chooser source):");

ok("multi-template family -> all its templates, in gallery order", () => {
  assert.deepEqual(
    familyTemplates(data, "line").map((t) => t.name),
    ["plot_plot", "plot_fill_between", "plot_stackplot"],
  );
  assert.deepEqual(
    familyTemplates(data, "line").map((t) => t.label),
    ["Line", "Fill Between", "Stack"],
  );
});

ok("single-template family -> that one", () => {
  assert.deepEqual(familyTemplates(data, "scatter").map((t) => t.label), ["Scatter"]);
  assert.deepEqual(familyTemplates(data, "statistical").map((t) => t.label), ["Error Bar"]);
});

ok("family with no templates (vector) -> empty, chooser suppressed", () => {
  assert.deepEqual(familyTemplates(data, "vector"), []);
  assert.equal(familyHasExamples(data, "vector"), false);
});

ok("familyHasExamples: true when loaded + has templates", () => {
  assert.equal(familyHasExamples(data, "line"), true);
  assert.equal(familyHasExamples(data, "scatter"), true);
});

ok("data not loaded yet (null) -> empty, no chooser (do not offer an undetermined set)", () => {
  assert.deepEqual(familyTemplates(null, "line"), []);
  assert.equal(familyHasExamples(null, "line"), false);
});

ok("unknown family -> empty", () => {
  assert.deepEqual(familyTemplates(data, "nope"), []);
  assert.equal(familyHasExamples(data, "nope"), false);
});

console.log("\n" + passed + " assertion-groups passed");
