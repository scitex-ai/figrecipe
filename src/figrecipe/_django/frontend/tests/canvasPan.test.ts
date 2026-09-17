/** Node test for the canvas pan/zoom gesture maths.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/canvasPan.test.ts
 *
 * The module under test is the arithmetic behind every canvas gesture: mouse
 * left-drag, middle/right-drag, one-finger pan and two-finger pinch. The
 * interesting assertions are that mouse and touch are the SAME arithmetic, that
 * a gesture owned by a figure never pans the view, and that no gesture can put
 * a NaN or an out-of-range zoom into the transform that draws the canvas.
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  FINE_DRAG_FACTOR,
  MAX_ZOOM,
  MIN_ZOOM,
  applyPan,
  canStartCanvasPan,
  clampZoom,
  dragView,
  panDelta,
  pinchDistance,
  pinchMidpoint,
  pinchUpdate,
  pointerKindOf,
  sanitizeView,
} from "../src/components/Canvas/canvasPan.ts";

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

const here = dirname(fileURLToPath(import.meta.url));
const SRC = join(here, "..", "src");
const read = (rel: string) => readFileSync(join(SRC, rel), "utf8");

/** Both mouse and touch events carry clientX/clientY — that shared shape is why
 * one pan helper can serve both. */
const pointOf = (event: { clientX: number; clientY: number }) => ({
  x: event.clientX,
  y: event.clientY,
});

console.log("canvasPan:");

// ── drag pan ──────────────────────────────────────────────────────────────

ok("a mouse drag pans by exactly the pointer delta", () => {
  // Arrange
  const view = { zoom: 0.35, panX: 10, panY: -20 };
  const start = { x: 100, y: 100 };
  const end = { x: 140, y: 70 };
  // Act
  const after = dragView(view, start, end);
  // Assert
  assert.deepEqual(after, { zoom: 0.35, panX: 50, panY: -50 });
});

ok("a single-finger touch drag of the same delta pans identically", () => {
  // Arrange — one mouse gesture and one touch gesture over the same path
  const view = { zoom: 0.35, panX: 10, panY: -20 };
  const mouseSamples = [
    { clientX: 320, clientY: 210 },
    { clientX: 284, clientY: 166 },
  ];
  const touchSamples = [
    { clientX: 320, clientY: 210 },
    { clientX: 284, clientY: 166 },
  ];
  // Act
  const fromMouse = dragView(view, pointOf(mouseSamples[0]), pointOf(mouseSamples[1]));
  const fromTouch = dragView(view, pointOf(touchSamples[0]), pointOf(touchSamples[1]));
  // Assert
  assert.deepEqual(fromMouse, fromTouch);
  assert.deepEqual(fromTouch, { zoom: 0.35, panX: -26, panY: -64 });
});

ok("a drag keeps the zoom untouched and never invents a NaN", () => {
  // Arrange
  const view = { zoom: 2.5, panX: 0, panY: 0 };
  // Act
  const after = dragView(view, { x: NaN, y: 0 }, { x: 10, y: 10 });
  // Assert
  assert.equal(after.zoom, 2.5);
  assert.deepEqual(after, { zoom: 2.5, panX: 0, panY: 0 });
  assert.ok(Number.isFinite(after.panX) && Number.isFinite(after.panY));
});

ok("Alt drags at 10% speed, like the ruler pan", () => {
  // Arrange / Act
  const fine = panDelta({ x: 0, y: 0 }, { x: 100, y: -40 }, true);
  const coarse = panDelta({ x: 0, y: 0 }, { x: 100, y: -40 }, false);
  // Assert
  assert.deepEqual(fine, { dx: 100 * FINE_DRAG_FACTOR, dy: -40 * FINE_DRAG_FACTOR });
  assert.deepEqual(coarse, { dx: 100, dy: -40 });
});

ok("applyPan adds the delta and keeps the rest of the view", () => {
  // Arrange
  const view = { zoom: 1.5, panX: 4, panY: 8 };
  // Act
  const after = applyPan(view, { dx: -2, dy: 3 });
  // Assert
  assert.deepEqual(after, { zoom: 1.5, panX: 2, panY: 11 });
});

// ── which gesture may pan ─────────────────────────────────────────────────

ok("a drag that starts on a figure produces no pan", () => {
  // Arrange
  const view = { zoom: 1, panX: 12, panY: 34 };
  // Act — the pointerdown is refused, so the hook never applies a drag
  const starts = canStartCanvasPan("figure", { kind: "mouse", button: 0 });
  const after = starts ? dragView(view, { x: 0, y: 0 }, { x: 80, y: 60 }) : view;
  // Assert
  assert.equal(starts, false);
  assert.deepEqual(after, view);
});

ok("left-drag pans on the empty board and on the page body", () => {
  // Arrange / Act / Assert
  assert.equal(canStartCanvasPan("board", { kind: "mouse", button: 0 }), true);
  assert.equal(canStartCanvasPan("page", { kind: "mouse", button: 0 }), true);
});

ok("shift+left-drag on the page stays with the marquee", () => {
  // Arrange / Act / Assert
  assert.equal(
    canStartCanvasPan("page", { kind: "mouse", button: 0, shiftKey: true }),
    false,
  );
});

ok("middle and right drag still pan anywhere, as before", () => {
  // Arrange / Act / Assert
  assert.equal(canStartCanvasPan("board", { kind: "mouse", button: 1 }), true);
  assert.equal(canStartCanvasPan("page", { kind: "mouse", button: 2 }), true);
  assert.equal(canStartCanvasPan("figure", { kind: "mouse", button: 1 }), true);
});

ok("one finger pans on the board and on the page", () => {
  // Arrange / Act / Assert
  assert.equal(canStartCanvasPan("board", { kind: "touch", button: 0 }), true);
  assert.equal(canStartCanvasPan("page", { kind: "touch", button: 0 }), true);
});

ok("one finger on a figure drags the figure instead of panning", () => {
  // Arrange / Act / Assert
  assert.equal(canStartCanvasPan("figure", { kind: "touch", button: 0 }), false);
});

ok("the ruler never pans from here (its own handlers already do)", () => {
  // Arrange / Act / Assert
  assert.equal(canStartCanvasPan("ruler", { kind: "mouse", button: 0 }), false);
  assert.equal(canStartCanvasPan("ruler", { kind: "touch", button: 0 }), false);
});

ok("an overlay that owns its clicks (context menu) never pans", () => {
  // Arrange / Act / Assert
  assert.equal(canStartCanvasPan("widget", { kind: "mouse", button: 0 }), false);
  assert.equal(canStartCanvasPan("widget", { kind: "touch", button: 0 }), false);
});

ok("a free-form pointerType normalises onto the gesture kinds", () => {
  // Arrange / Act / Assert — PointerEvent.pointerType is typed as a plain string
  assert.equal(pointerKindOf("touch"), "touch");
  assert.equal(pointerKindOf("pen"), "pen");
  assert.equal(pointerKindOf("mouse"), "mouse");
  assert.equal(pointerKindOf(""), "mouse"); // unknown input must not claim a finger
});

// ── pinch zoom ────────────────────────────────────────────────────────────

ok("pinching out scales about the fingers' centroid", () => {
  // Arrange — fingers 100 px apart, view at 1:1 from the origin
  const start = { a: { x: 100, y: 100 }, b: { x: 200, y: 100 }, view: { zoom: 1, panX: 0, panY: 0 } };
  // Act — 200 px apart, same centre
  const after = pinchUpdate(start, { x: 50, y: 100 }, { x: 250, y: 100 });
  // Assert
  assert.deepEqual(after, { zoom: 2, panX: -150, panY: -100 });
});

ok("a two-finger drag pans with the centroid without changing zoom", () => {
  // Arrange
  const start = { a: { x: 100, y: 100 }, b: { x: 200, y: 100 }, view: { zoom: 1, panX: 5, panY: 7 } };
  // Act — both fingers move by (+30, +40), distance unchanged
  const after = pinchUpdate(start, { x: 130, y: 140 }, { x: 230, y: 140 });
  // Assert
  assert.deepEqual(after, { zoom: 1, panX: 35, panY: 47 });
});

ok("pinch zoom clamps to [0.1, 5.0] in both directions", () => {
  // Arrange
  const start = { a: { x: 100, y: 100 }, b: { x: 200, y: 100 }, view: { zoom: 1, panX: 0, panY: 0 } };
  // Act — an absurd spread and an absurd squeeze
  const huge = pinchUpdate(start, { x: -5000, y: 100 }, { x: 5100, y: 100 });
  const tiny = pinchUpdate(start, { x: 149, y: 100 }, { x: 151, y: 100 });
  // Assert
  assert.equal(huge.zoom, MAX_ZOOM);
  assert.equal(tiny.zoom, MIN_ZOOM);
});

ok("a pinch that starts and ends inside the clamp range interpolates", () => {
  // Arrange
  const start = { a: { x: 0, y: 0 }, b: { x: 100, y: 0 }, view: { zoom: 2, panX: 0, panY: 0 } };
  // Act — 1.25x
  const after = pinchUpdate(start, { x: 0, y: 0 }, { x: 125, y: 0 });
  // Assert
  assert.equal(after.zoom, 2.5);
});

ok("no pinch input can produce NaN or Infinity", () => {
  // Arrange
  const view = { zoom: 0.22, panX: 13, panY: -8 };
  const samples = [
    [{ x: NaN, y: 0 }, { x: 0, y: NaN }],
    [{ x: Infinity, y: Infinity }, { x: 0, y: 0 }],
    [{ x: 5, y: 5 }, { x: 5, y: 5 }], // degenerate: both fingers on one point
    [{ x: 0, y: 0 }, { x: 0, y: 0 }],
  ];
  // Act / Assert
  for (const [a, b] of samples) {
    const after = pinchUpdate({ a: { x: 0, y: 0 }, b: { x: 10, y: 0 }, view }, a, b);
    assert.ok(Number.isFinite(after.zoom), "zoom must stay finite for " + JSON.stringify([a, b]));
    assert.ok(Number.isFinite(after.panX), "panX must stay finite");
    assert.ok(Number.isFinite(after.panY), "panY must stay finite");
    assert.ok(after.zoom >= MIN_ZOOM && after.zoom <= MAX_ZOOM);
  }
});

ok("a non-finite start view is repaired rather than propagated", () => {
  // Arrange
  const start = {
    a: { x: 0, y: 0 },
    b: { x: 100, y: 0 },
    view: { zoom: NaN, panX: NaN, panY: Infinity },
  };
  // Act
  const after = pinchUpdate(start, { x: 0, y: 0 }, { x: 100, y: 0 });
  // Assert
  assert.deepEqual(after, { zoom: MIN_ZOOM, panX: 0, panY: 0 });
});

ok("distance and midpoint follow the two fingers", () => {
  // Arrange / Act / Assert
  assert.equal(pinchDistance({ x: 0, y: 0 }, { x: 3, y: 4 }), 5);
  assert.equal(pinchDistance({ x: NaN, y: 0 }, { x: 3, y: 4 }), 0);
  assert.deepEqual(pinchMidpoint({ x: 0, y: 0 }, { x: 10, y: 20 }), { x: 5, y: 10 });
});

// ── clamping / sanitising ─────────────────────────────────────────────────

ok("clampZoom keeps [0.1, 5.0] and absorbs NaN/Infinity", () => {
  // Arrange / Act / Assert
  assert.equal(clampZoom(0.55), 0.55);
  assert.equal(clampZoom(0.01), MIN_ZOOM);
  assert.equal(clampZoom(99), MAX_ZOOM);
  assert.equal(clampZoom(NaN), MIN_ZOOM);
  assert.equal(clampZoom(Infinity), MAX_ZOOM);
  assert.equal(MIN_ZOOM, 0.1);
  assert.equal(MAX_ZOOM, 5.0);
});

ok("sanitizeView makes a view safe to put in a CSS transform", () => {
  // Arrange / Act
  const after = sanitizeView({ zoom: NaN, panX: NaN, panY: Infinity });
  // Assert
  assert.deepEqual(after, { zoom: MIN_ZOOM, panX: 0, panY: 0 });
});

// ── conformance: the logic stays importable outside React ─────────────────

ok("canvasPan has no React / @scitex-ui import", () => {
  // Arrange
  const src = read("components/Canvas/canvasPan.ts");
  // Act / Assert
  assert.doesNotMatch(
    src,
    /from\s*["']react["']|from\s*["'].*@scitex\/ui|from\s*["'].*\/(useZoomPan|Canvas)/,
    "canvasPan.ts must stay dependency-free so it runs under " +
      "node --experimental-strip-types",
  );
});

ok("the viewport is kept in the session store, not in the canvas component", () => {
  // Arrange / Act / Assert -- the canvas UNMOUNTS on a tab change, so a view
  // that lives only in component state is thrown away on every switch; the
  // acceptance requires it to survive the session.
  const hook = readFileSync(
    join(here, "..", "src", "components", "Canvas", "useZoomPan.ts"),
    "utf8",
  );
  assert.match(hook, /useEditorStore\.getState\(\)\.canvasView \?\? INITIAL_VIEW/);
  assert.match(hook, /setCanvasView\(state\)/);
});

console.log("\nAll canvasPan checks passed (" + passed + " assertion-groups).");
