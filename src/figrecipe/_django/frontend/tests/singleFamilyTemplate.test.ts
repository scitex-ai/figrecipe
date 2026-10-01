/** Node test for the one-operation plot-selection decision (TODO 129).
 *
 * The rail now adds a family's template directly when that family ships exactly
 * one template, instead of opening a one-tile gallery. That decision lives in
 * the pure helper `singleFamilyTemplate` / `addFamilyDirectly`. This script
 * exercises it under Node's strip-types (no React/DOM/network):
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/singleFamilyTemplate.test.ts
 */

import assert from "node:assert/strict";

import {
  singleFamilyTemplate,
  addFamilyDirectly,
} from "../src/components/Gallery/singleFamilyTemplate.ts";
import type { GalleryData } from "../src/components/Gallery/useGalleryTemplates";

// A shape matching the real gallery manifest (handlers/gallery.py
// GALLERY_TEMPLATES, filtered by available_categories to on-disk templates).
const data: GalleryData = {
  categories: {
    line: [
      { name: "plot_plot", label: "Line", icon: "fa-chart-line", path: "a", has_thumbnail: true },
      { name: "plot_fill_between", label: "Fill Between", icon: "fa-chart-line", path: "b", has_thumbnail: true },
      { name: "plot_stackplot", label: "Stack", icon: "fa-chart-line", path: "c", has_thumbnail: true },
    ],
    scatter: [
      { name: "plot_scatter", label: "Scatter", icon: "fa-braille", path: "d", has_thumbnail: true },
    ],
    statistical: [
      { name: "plot_errorbar", label: "Error Bar", icon: "fa-square-root-variable", path: "e", has_thumbnail: true },
    ],
    contour: [
      { name: "plot_contourf", label: "Contour", icon: "fa-layer-group", path: "f", has_thumbnail: true },
    ],
    special: [
      { name: "plot_pie", label: "Pie", icon: "fa-chart-pie", path: "g", has_thumbnail: true },
      { name: "plot_specgram", label: "Spectrogram", icon: "fa-wave-square", path: "h", has_thumbnail: true },
    ],
    // "vector" is deliberately absent: available_categories drops empty
    // categories, so a family the rail lists can be missing from `data`.
  },
};

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log(`  ok - ${name}`);
}

console.log("singleFamilyTemplate / addFamilyDirectly:");

ok("single-template family -> returns that template (add directly)", () => {
  const t = singleFamilyTemplate(data, "scatter");
  assert.ok(t);
  assert.equal(t!.name, "plot_scatter");
  assert.equal(addFamilyDirectly(data, "scatter"), true);
});

ok("single-template family (statistical) -> error bar, add directly", () => {
  assert.equal(singleFamilyTemplate(data, "statistical")!.name, "plot_errorbar");
});

ok("single-template family (contour) -> contourf, add directly", () => {
  assert.equal(singleFamilyTemplate(data, "contour")!.name, "plot_contourf");
});

ok("multi-template family -> null (open the gallery)", () => {
  assert.equal(singleFamilyTemplate(data, "line"), null);
  assert.equal(addFamilyDirectly(data, "line"), false);
  assert.equal(singleFamilyTemplate(data, "special"), null);
});

ok("family absent from data (e.g. 'vector') -> null, NOT a crash", () => {
  assert.equal(singleFamilyTemplate(data, "vector"), null);
  assert.equal(addFamilyDirectly(data, "vector"), false);
});

ok("unknown family -> null", () => {
  assert.equal(singleFamilyTemplate(data, "does-not-exist"), null);
});

ok("null / not-loaded data -> null (rail falls back to gallery until fetched)", () => {
  assert.equal(singleFamilyTemplate(null, "scatter"), null);
  assert.equal(addFamilyDirectly(null, "scatter"), false);
});

ok("empty category (length 0) -> null (do not add directly)", () => {
  const empty: GalleryData = { categories: { scatter: [] } };
  assert.equal(singleFamilyTemplate(empty, "scatter"), null);
  assert.equal(addFamilyDirectly(empty, "scatter"), false);
});

console.log(`\n${passed} assertion-groups passed`);
