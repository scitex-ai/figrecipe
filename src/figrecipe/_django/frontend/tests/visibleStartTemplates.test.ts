/** Node test for the empty-canvas cognitive-load reduction (TODO 131).
 *
 * The fallback "Start from an example" grid is now gated behind a disclosure:
 * collapsed (default) shows ZERO tiles; expanded shows ALL. The decision lives
 * in the pure helper `visibleStartTemplates`. Run under Node strip-types:
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/visibleStartTemplates.test.ts
 */

import assert from "node:assert/strict";

import {
  visibleStartTemplates,
  visibleStartTemplateCount,
} from "../src/components/Gallery/visibleStartTemplates.ts";
import type { GalleryTemplate } from "../src/components/Gallery/useGalleryTemplates.ts";

// The 18 templates the live gallery resolves (audit-observed count).
const t = (name: string): GalleryTemplate => ({
  name,
  label: name,
  icon: "fa-chart-line",
  path: name,
  has_thumbnail: false,
});
const ALL = Array.from({ length: 18 }, (_, i) => t(`plot_${i}`));

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log(`  ok - ${name}`);
}

console.log("visibleStartTemplates (TODO 131):");

ok("collapsed (default) shows ZERO tiles — the cognitive-load reduction", () => {
  assert.equal(visibleStartTemplates(ALL, false).length, 0);
  assert.equal(visibleStartTemplateCount(ALL, false), 0);
});

ok("expanded shows ALL tiles (one click away, nothing removed)", () => {
  assert.equal(visibleStartTemplates(ALL, true).length, 18);
  assert.equal(visibleStartTemplateCount(ALL, true), 18);
  assert.deepEqual(visibleStartTemplates(ALL, true), ALL);
});

ok("empty template list stays empty in both states", () => {
  assert.equal(visibleStartTemplateCount([], false), 0);
  assert.equal(visibleStartTemplateCount([], true), 0);
});

ok("collapsed is strictly fewer options than the always-on rail", () => {
  // The audit's core: collapsed fallback (0) + rail (10) = 10 options at once,
  // vs the old 18 tiles + 10 rail = 28. 0 < 18 is the figrecipe-side half.
  const rail = 10;
  const before = 18 + rail; // 28
  const after = visibleStartTemplateCount(ALL, false) + rail; // 10
  assert.ok(after < before, `expected ${after} < ${before}`);
});

console.log(`\n${passed} assertion-groups passed`);
