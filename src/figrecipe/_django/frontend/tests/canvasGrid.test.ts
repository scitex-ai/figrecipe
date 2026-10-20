/** Node test for the zoom-aware canvas grid ladder.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/canvasGrid.test.ts
 *
 * The grid used to be one fixed CSS background: readable at 1:1, a solid smear
 * at zoom 0.1 and a moiré at zoom 5.0. The module under test picks the 1-2-5
 * rung whose on-screen spacing stays legible, and the assertions below pin that
 * band down at the three zoom levels the defect was reported at.
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  GRID_COLORS,
  MIN_SCREEN_SPACING_PX,
  MM_PX,
  gridPlanForZoom,
  gridStrokeWidth,
  gridTileDataUrl,
} from "../src/components/Canvas/canvasGrid.ts";

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

const here = dirname(fileURLToPath(import.meta.url));
const SRC = join(here, "..", "src");
const read = (rel: string) => readFileSync(join(SRC, rel), "utf8");

console.log("canvasGrid:");

// ── spacing per zoom ──────────────────────────────────────────────────────

ok("zoom 0.1 yields a positive finite coarse grid", () => {
  // Arrange / Act
  const plan = gridPlanForZoom(0.1);
  // Assert — 1 mm would be 1.2 screen px (a block), so the ladder steps up to 10 mm
  assert.equal(plan.level, "coarse");
  assert.equal(plan.minor, MM_PX * 10);
  assert.equal(plan.major, MM_PX * 100);
  assert.ok(plan.minor > 0 && Number.isFinite(plan.minor));
  assert.ok(plan.major > 0 && Number.isFinite(plan.major));
});

ok("zoom 1.0 yields the plain millimetre grid", () => {
  // Arrange / Act
  const plan = gridPlanForZoom(1.0);
  // Assert
  assert.equal(plan.level, "fine");
  assert.equal(plan.minor, MM_PX); // 1 mm = 11.811 canvas px
  assert.equal(plan.major, MM_PX * 10); // 10 mm
  assert.ok(plan.minor > 0 && Number.isFinite(plan.minor));
});

ok("zoom 5.0 yields a positive finite fine grid, not a moiré", () => {
  // Arrange / Act
  const plan = gridPlanForZoom(5.0);
  // Assert — half-millimetre rung keeps the lines ~30 screen px apart
  assert.equal(plan.level, "fine");
  assert.equal(plan.minor, MM_PX * 0.5);
  assert.ok(plan.minor > 0 && Number.isFinite(plan.minor));
  assert.ok(plan.major > plan.minor);
});

ok("the chosen rung is the FINEST one that stays legible", () => {
  // Arrange — the rung below 10 mm at zoom 0.1 would be 5 mm
  const tooFine = MM_PX * 5 * 0.1;
  // Act
  const plan = gridPlanForZoom(0.1);
  // Assert
  assert.ok(tooFine < MIN_SCREEN_SPACING_PX);
  assert.ok(plan.minorScreen >= MIN_SCREEN_SPACING_PX);
});

ok("every zoom in [0.1, 5.0] keeps the minor grid on screen", () => {
  // Arrange
  const zooms = [0.1, 0.15, 0.22, 0.35, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5];
  // Act / Assert
  for (const zoom of zooms) {
    const plan = gridPlanForZoom(zoom);
    assert.ok(
      plan.minorScreen >= MIN_SCREEN_SPACING_PX,
      "minor spacing at zoom " + zoom + " was " + plan.minorScreen + " px",
    );
    assert.ok(Number.isFinite(plan.minorScreen));
    assert.ok(plan.major / plan.minor === 10, "major grid is a decade above the minor one");
  }
});

ok("a degenerate zoom falls back to 1:1 instead of NaN", () => {
  // Arrange / Act / Assert
  for (const zoom of [0, -3, NaN, Infinity]) {
    const plan = gridPlanForZoom(zoom);
    assert.equal(plan.minor, MM_PX);
    assert.ok(Number.isFinite(plan.minor) && plan.minor > 0);
  }
});

ok("the coarse level only appears at the low end of the range", () => {
  // Arrange / Act / Assert — a 1 mm grid is a smear below ~0.42 zoom, so the
  // ladder answers with 5 mm (>= 5x the millimetre grid = "coarse") and 10 mm
  assert.equal(gridPlanForZoom(0.1).level, "coarse");
  assert.equal(gridPlanForZoom(0.15).level, "coarse");
  assert.equal(gridPlanForZoom(0.22).level, "coarse"); // INITIAL_ZOOM
  assert.equal(gridPlanForZoom(0.5).level, "fine");
  assert.equal(gridPlanForZoom(1).level, "fine");
  assert.equal(gridPlanForZoom(5).level, "fine");
});

// ── stroke + tile ─────────────────────────────────────────────────────────

ok("the stroke is counter-scaled so a line stays ~1 screen px", () => {
  // Arrange
  const zooms = [0.1, 1, 5];
  // Act / Assert
  for (const zoom of zooms) {
    const stroke = gridStrokeWidth(zoom);
    assert.ok(stroke > 0 && Number.isFinite(stroke));
    assert.ok(Math.abs(stroke * zoom - 1) < 1e-9, "screen stroke at zoom " + zoom);
  }
  assert.equal(gridStrokeWidth(NaN), 1);
});

ok("the tile URL carries the spacing, colour and stroke", () => {
  // Arrange / Act
  const tile = gridTileDataUrl(11.811, "#505050", 1);
  // Assert
  assert.match(tile, /^url\("data:image\/svg\+xml,/);
  assert.match(tile, /%23505050/, "colour must be URL-encoded");
  assert.doesNotMatch(tile, /[<>#]/, "no raw markup may leak into the CSS url()");
  assert.equal(gridTileDataUrl(NaN, "#505050", NaN), gridTileDataUrl(MM_PX, "#505050", 1));
});

ok("both themes keep the colours of the fixed grid they replace", () => {
  // Arrange / Act / Assert
  assert.deepEqual(GRID_COLORS.dark, { minor: "#505050", major: "#707070" });
  assert.deepEqual(GRID_COLORS.light, { minor: "#ccc8c4", major: "#aaa6a2" });
});

// ── conformance: the logic stays importable outside React ─────────────────

ok("canvasGrid has no React / @scitex-ui import", () => {
  // Arrange
  const src = read("components/Canvas/canvasGrid.ts");
  // Act / Assert
  assert.doesNotMatch(
    src,
    /from\s*["']react["']|from\s*["'].*@scitex\/ui|from\s*["'].*\/(CanvasGrid|Canvas)/,
    "canvasGrid.ts must stay dependency-free so it runs under " +
      "node --experimental-strip-types",
  );
});

console.log("\nAll canvasGrid checks passed (" + passed + " assertion-groups).");
