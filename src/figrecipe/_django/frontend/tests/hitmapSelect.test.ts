/** Node test for the plot hitmap's pixel -> element -> selection logic.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/hitmapSelect.test.ts
 *
 * The module under test decides what a click on the hitmap overlay means: which
 * pixel to sample, whether that colour belongs to an element, and what the
 * selection should become. It must survive a not-yet-loaded raster, an
 * out-of-range pixel, a transparent pixel and a colour that is in no colorMap —
 * all four used to be either a crash or a silently stale selection.
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  DEFAULT_FOCUS_POINT,
  buildHexToElementKey,
  elementLabel,
  focusPointToPixels,
  hitmapPixelCoords,
  isFocusKey,
  moveFocusPoint,
  resolveElementKey,
  rgbToHex,
  selectionAfterClear,
  selectionAfterHit,
} from "../src/components/Canvas/hitmapSelect.ts";

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

const here = dirname(fileURLToPath(import.meta.url));
const SRC = join(here, "..", "src");
const read = (rel: string) => readFileSync(join(SRC, rel), "utf8");

// ── colorMap -> reverse lookup ────────────────────────────────────────────

// The backend ships { elementKey: { rgb: [r, g, b], label, type, ... } }.
const COLOR_MAP = {
  ax0_line_0: { rgb: [255, 107, 107], label: "signal", type: "line", axes_index: 0 },
  ax0_scatter_1: { rgb: [16, 32, 48], label: "points", type: "scatter", axes_index: 0 },
  "ax0_axes": { label: "axes", type: "axes", axes_index: 0 }, // no rgb: not selectable
};

console.log("hitmapSelect:");

ok("an exact colour hit resolves to its element key", () => {
  // Arrange
  const hexToKey = buildHexToElementKey(COLOR_MAP);
  // Act
  const key = resolveElementKey({
    ready: true,
    pixel: [255, 107, 107, 255],
    hexToKey,
  });
  // Assert
  assert.equal(key, "ax0_line_0");
});

ok("a colour in no colorMap entry resolves to nothing, not to a crash", () => {
  // Arrange
  const hexToKey = buildHexToElementKey(COLOR_MAP);
  // Act — white background, and the reserved (rgb-less) axes entry
  const background = resolveElementKey({ ready: true, pixel: [255, 255, 255, 255], hexToKey });
  const axes = resolveElementKey({ ready: true, pixel: [64, 64, 64, 255], hexToKey });
  // Assert
  assert.equal(background, null);
  assert.equal(axes, null);
});

ok("a transparent pixel (alpha 0) is background, whatever its colour", () => {
  // Arrange
  const hexToKey = buildHexToElementKey(COLOR_MAP);
  // Act
  const hit = resolveElementKey({ ready: true, pixel: [255, 107, 107, 0], hexToKey });
  // Assert
  assert.equal(hit, null);
});

ok("a raster that has not loaded yet never resolves an element", () => {
  // Arrange — the scratch canvas is blank until the PNG's onload fires
  const hexToKey = buildHexToElementKey(COLOR_MAP);
  // Act
  const beforeLoad = resolveElementKey({
    ready: false,
    pixel: [255, 107, 107, 255],
    hexToKey,
  });
  const noPixel = resolveElementKey({ ready: true, pixel: null, hexToKey });
  const shortPixel = resolveElementKey({ ready: true, pixel: [255, 107], hexToKey });
  // Assert
  assert.equal(beforeLoad, null);
  assert.equal(noPixel, null);
  assert.equal(shortPixel, null);
});

ok("malformed colorMap entries are skipped, the rest still resolve", () => {
  // Arrange
  const hexToKey = buildHexToElementKey({
    good: { rgb: [1, 2, 3] },
    noRgb: { label: "text" },
    shortRgb: { rgb: [9, 9] },
    nanRgb: { rgb: ["a", "b", "c"] },
  });
  // Act
  const good = resolveElementKey({ ready: true, pixel: [1, 2, 3, 255], hexToKey });
  // Assert
  assert.equal(good, "good");
  assert.deepEqual(Object.keys(hexToKey), ["#010203"]);
});

ok("rgbToHex clips and pads channels into a 6-digit hex", () => {
  // Arrange / Act / Assert
  assert.equal(rgbToHex([0, 15, 255]), "#000fff");
  assert.equal(rgbToHex([300, -5, 128.6]), "#ff0081");
  assert.equal(rgbToHex(null), null);
});

// ── pointer -> raster pixel ───────────────────────────────────────────────

const SURFACE = { width: 1000, height: 2000 };
const BOX = { width: 500, height: 1000 };

ok("a pointer maps to the matching raster pixel across the scale", () => {
  // Arrange
  const pointer = { x: 250, y: 500 };
  // Act — box is half the raster, so 2x
  const pixel = hitmapPixelCoords(SURFACE, pointer, BOX);
  // Assert
  assert.deepEqual(pixel, { x: 500, y: 1000 });
});

ok("out-of-range coordinates are rejected instead of throwing in getImageData", () => {
  // Arrange — the last CSS px column/row reports exactly width/height
  const right = { x: BOX.width, y: 0 };
  const bottom = { x: 0, y: BOX.height };
  const negative = { x: -1, y: 10 };
  // Act / Assert
  assert.equal(hitmapPixelCoords(SURFACE, right, BOX), null);
  assert.equal(hitmapPixelCoords(SURFACE, bottom, BOX), null);
  assert.equal(hitmapPixelCoords(SURFACE, negative, BOX), null);
});

ok("a not-yet-sized or zero-sized surface yields no pixel", () => {
  // Arrange / Act / Assert
  assert.equal(hitmapPixelCoords({ width: 0, height: 0 }, { x: 1, y: 1 }, BOX), null);
  assert.equal(hitmapPixelCoords(null, { x: 1, y: 1 }, BOX), null);
  assert.equal(hitmapPixelCoords(SURFACE, { x: 1, y: 1 }, { width: 0, height: 0 }), null);
  assert.equal(hitmapPixelCoords(SURFACE, { x: NaN, y: 1 }, BOX), null);
});

// ── selection transitions ─────────────────────────────────────────────────

ok("a hit on a different element selects it", () => {
  // Arrange / Act
  const outcome = selectionAfterHit(null, "ax0_bar_2");
  // Assert
  assert.deepEqual(outcome, { kind: "select", elementId: "ax0_bar_2" });
});

ok("re-selecting the same element is a no-op", () => {
  // Arrange / Act
  const outcome = selectionAfterHit("ax0_bar_2", "ax0_bar_2");
  // Assert
  assert.deepEqual(outcome, { kind: "unchanged" });
});

ok("clicking empty background clears the selection", () => {
  // Arrange / Act
  const outcome = selectionAfterHit("ax0_bar_2", null);
  // Assert
  assert.deepEqual(outcome, { kind: "clear" });
});

ok("clicking empty background with nothing selected stays a no-op", () => {
  // Arrange / Act
  const outcome = selectionAfterHit(null, null);
  // Assert
  assert.deepEqual(outcome, { kind: "unchanged" });
});

ok("Escape clears, and does nothing when already clear", () => {
  // Arrange / Act / Assert
  assert.deepEqual(selectionAfterClear("ax0_title_0"), { kind: "clear" });
  assert.deepEqual(selectionAfterClear(null), { kind: "unchanged" });
});

// ── keyboard reticle ──────────────────────────────────────────────────────

ok("arrow keys move the reticle and clamp it inside the surface", () => {
  // Arrange
  const centre = DEFAULT_FOCUS_POINT;
  // Act
  const right = moveFocusPoint(centre, "ArrowRight", 0.1);
  const up = moveFocusPoint(centre, "ArrowUp", 0.1);
  const overRight = moveFocusPoint({ x: 0.95, y: 0.5 }, "ArrowRight", 0.1);
  const overDown = moveFocusPoint({ x: 0.5, y: 0.95 }, "ArrowDown", 0.1);
  // Assert
  assert.deepEqual(right, { x: 0.6, y: 0.5 });
  assert.deepEqual(up, { x: 0.5, y: 0.4 });
  assert.deepEqual(overRight, { x: 1, y: 0.5 });
  assert.deepEqual(overDown, { x: 0.5, y: 1 });
});

ok("the reticle falls back to the centre for a NaN point or step", () => {
  // Arrange / Act
  const moved = moveFocusPoint({ x: NaN, y: NaN }, "ArrowLeft", NaN);
  // Assert
  assert.deepEqual(moved, { x: 0.48, y: 0.5 });
});

ok("only the four arrow keys count as focus movement", () => {
  // Arrange / Act / Assert
  assert.equal(isFocusKey("ArrowLeft"), true);
  assert.equal(isFocusKey("Enter"), false);
  assert.equal(isFocusKey("a"), false);
});

ok("the reticle converts to a CSS-px point inside the box", () => {
  // Arrange / Act
  const point = focusPointToPixels({ x: 0.25, y: 0.5 }, BOX);
  // Assert
  assert.deepEqual(point, { x: 125, y: 500 });
});

// ── labels ────────────────────────────────────────────────────────────────

ok("an element is named by its colorMap label, else by its key", () => {
  // Arrange / Act / Assert
  assert.equal(elementLabel(COLOR_MAP, "ax0_line_0"), "signal");
  assert.equal(elementLabel(COLOR_MAP, "ax7_unknown"), "ax7_unknown");
  assert.equal(elementLabel(COLOR_MAP, null), "");
});

// ── conformance: the logic stays importable outside React ─────────────────

ok("hitmapSelect has no React / @scitex-ui import", () => {
  // Arrange
  const src = read("components/Canvas/hitmapSelect.ts");
  // Act / Assert
  assert.doesNotMatch(
    src,
    /from\s*["']react["']|from\s*["'].*@scitex\/ui|from\s*["'].*\/(HitmapOverlay|Canvas)/,
    "hitmapSelect.ts must stay dependency-free so it runs under " +
      "node --experimental-strip-types",
  );
});

// ------------------------------------------------------- component contracts

const overlaySource = readFileSync(
  join(here, "..", "src", "components", "Canvas", "HitmapOverlay.tsx"),
  "utf8",
);

ok("a touch tap selects, on the same path a click takes", () => {
  // Arrange / Act / Assert -- bound to pointerup, gated off the mouse so the
  // click path stays its single handler, and sharing applySelection.
  assert.match(overlaySource, /onPointerUp=\{handlePointerUp\}/);
  assert.match(overlaySource, /if \(event\.pointerType === "mouse"\) return;/);
  assert.match(
    overlaySource,
    /const handlePointerUp = useCallback\([\s\S]*?applySelection\(hit\)/,
  );
});

ok("a selection opens the property controls", () => {
  // Arrange / Act / Assert -- one place applies every selection (click, tap,
  // keyboard), so the Details pane cannot follow one gesture but not another.
  assert.match(
    overlaySource,
    /if \(outcome\.kind === "select"\) \{[\s\S]*?showEditorPane\("details"\)/,
  );
});

console.log("\nAll hitmapSelect checks passed (" + passed + " assertion-groups).");
