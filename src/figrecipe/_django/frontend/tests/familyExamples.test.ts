/** Node test for the rail hover-panel example list (TODO 130).
 *
 * The hover panel is informational: it previews the templates a family holds,
 * distinct from click behavior (TODO 128/129). The decision is the pure helper
 * `familyExamples`. Run under Node strip-types (no React/DOM/SelectorNav):
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/familyExamples.test.ts
 */

import assert from "node:assert/strict";

import {
  familyTemplates,
  familyExampleLabels,
  familyHasExamples,
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

console.log("familyExamples (TODO 130 hover panel):");

ok("multi-template family -> all its labels", () => {
  assert.deepEqual(familyExampleLabels(data, "line"), ["Line", "Fill Between", "Stack"]);
  assert.deepEqual(familyTemplates(data, "line").map((t) => t.name), [
    "plot_plot",
    "plot_fill_between",
    "plot_stackplot",
  ]);
});

ok("single-template family -> that one label", () => {
  assert.deepEqual(familyExampleLabels(data, "scatter"), ["Scatter"]);
  assert.deepEqual(familyExampleLabels(data, "statistical"), ["Error Bar"]);
});

ok("family with no templates (vector) -> empty, panel suppressed", () => {
  assert.deepEqual(familyExampleLabels(data, "vector"), []);
  assert.equal(familyHasExamples(data, "vector"), false);
});

ok("familyHasExamples: true when loaded + has templates", () => {
  assert.equal(familyHasExamples(data, "line"), true);
  assert.equal(familyHasExamples(data, "scatter"), true);
});

ok("data not loaded yet (null) -> empty, no panel (do not preview undetermined)", () => {
  assert.deepEqual(familyExampleLabels(null, "line"), []);
  assert.equal(familyHasExamples(null, "line"), false);
});

ok("unknown family -> empty", () => {
  assert.deepEqual(familyExampleLabels(data, "nope"), []);
  assert.equal(familyHasExamples(data, "nope"), false);
});

console.log("\n" + passed + " assertion-groups passed");
