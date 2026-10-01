/** Pan/zoom maths for the canvas pointer gestures.
 *
 * Pure (no DOM, no React) and shared by the mouse and the touch/pen paths, so
 * the same pixel delta provably pans the same distance whatever input produced
 * it — see tests/canvasPan.test.ts. The DOM glue lives in useZoomPan.
 *
 * Coordinate frame: pan is in untransformed container px and zoom is the view
 * scale, i.e. the element transform is `translate(panX, panY) scale(zoom)`.
 */

/** Zoom limits shared with the toolbar controls (vis_app constants). */
export const MIN_ZOOM = 0.1;
export const MAX_ZOOM = 5.0;

/** Alt = 10% speed (vis_app RulersManager) — applied to every drag path. */
export const FINE_DRAG_FACTOR = 0.1;

export interface Point {
  x: number;
  y: number;
}

export interface ViewState {
  zoom: number;
  panX: number;
  panY: number;
}

export interface Delta {
  dx: number;
  dy: number;
}

/** Where a pointerdown landed. A gesture that starts on a figure belongs to the
 * figure, not to the view; `widget` covers overlays that own their own clicks
 * (the context menu) which must never pan from under the user's pointer. */
export type GestureOrigin = "board" | "page" | "figure" | "ruler" | "widget";

export type PointerKind = "mouse" | "touch" | "pen";

/** PointerEvent.pointerType is typed as a free-form string; normalise it onto
 * the kinds we branch on. Anything unknown is treated as a mouse — the
 * conservative default, since it never pans where a figure drag is expected. */
export function pointerKindOf(pointerType: string): PointerKind {
  const kind = pointerType.toLowerCase();
  return kind === "touch" || kind === "pen" ? kind : "mouse";
}

export interface PointerInput {
  kind: PointerKind;
  /** DOM button: 0 = left, 1 = middle, 2 = right. */
  button: number;
  /** Shift+left-drag on the page is the marquee, so pan must not claim it. */
  shiftKey?: boolean;
}

/** Zoom clamp that also absorbs NaN/Infinity (a bad wheel delta must not poison
 * the view: `scale(NaN)` makes the whole layer disappear). */
export function clampZoom(zoom: number): number {
  if (Number.isNaN(zoom)) return MIN_ZOOM; // no direction to honour: pick the floor
  if (zoom === Infinity) return MAX_ZOOM;
  if (zoom === -Infinity) return MIN_ZOOM;
  return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom));
}

/** Last line of defence before the transform reaches the DOM. */
export function sanitizeView(view: ViewState): ViewState {
  return {
    zoom: clampZoom(view.zoom),
    panX: Number.isFinite(view.panX) ? view.panX : 0,
    panY: Number.isFinite(view.panY) ? view.panY : 0,
  };
}

function isPoint(point: Point | null | undefined): point is Point {
  return !!point && Number.isFinite(point.x) && Number.isFinite(point.y);
}

/** Screen-pixel movement of a drag between two pointer samples.
 * Identical for mouse and touch by construction — touch events carry the same
 * clientX/clientY, so there is no per-input scaling to drift apart. */
export function panDelta(start: Point, current: Point, altKey = false): Delta {
  if (!isPoint(start) || !isPoint(current)) return { dx: 0, dy: 0 };
  const factor = altKey ? FINE_DRAG_FACTOR : 1;
  return { dx: (current.x - start.x) * factor, dy: (current.y - start.y) * factor };
}

/** Apply a drag delta to the view, keeping the zoom untouched. */
export function applyPan(view: ViewState, delta: Delta): ViewState {
  if (!Number.isFinite(delta.dx) || !Number.isFinite(delta.dy)) return sanitizeView(view);
  return sanitizeView({ ...view, panX: view.panX + delta.dx, panY: view.panY + delta.dy });
}

/** One drag frame: the view after the pointer moved from `start` to `current`. */
export function dragView(
  view: ViewState,
  start: Point,
  current: Point,
  altKey = false,
): ViewState {
  return applyPan(view, panDelta(start, current, altKey));
}

/** Whether this pointerdown may start a canvas pan.
 *
 * WHY origin decides and not just the button: the same element hosts four
 * gestures — figure drag (left on a `.placed-figure`), page marquee
 * (shift+left on the page), ruler drag (its own React handlers) and the pan.
 * The button alone cannot separate them, so the region that was grabbed does.
 *
 * The middle/right answer mirrors the legacy unconditional pan those buttons
 * still get from useZoomPan; only the left button and touch are gated here. */
export function canStartCanvasPan(origin: GestureOrigin, pointer: PointerInput): boolean {
  // The ruler drag is already bound to its own React handlers; panning from
  // here as well would double every ruler movement.
  if (origin === "ruler") return false;

  // Middle/right-drag pans over anything, exactly as before (their own drag
  // detection lives in useZoomPan); this predicate only adds the left button.
  const isLeft = pointer.button === 0;
  if (!isLeft) return true;

  // A left drag that starts on a figure belongs to the figure: useDrag moves it
  // (mouse) and the same holds for the finger that landed on it. An overlay that
  // owns clicks (context menu) would otherwise pan under its own buttons.
  if (origin === "figure" || origin === "widget") return false;

  // Touch/pen have no marquee and no hover: one finger pans wherever it lands.
  if (pointer.kind !== "mouse") return true;

  // Shift+left-drag on the page keeps rubber-band marquee selection.
  if (origin === "page") return pointer.shiftKey !== true;
  return true;
}

export function pinchDistance(a: Point, b: Point): number {
  if (!isPoint(a) || !isPoint(b)) return 0;
  return Math.hypot(a.x - b.x, a.y - b.y);
}

export function pinchMidpoint(a: Point, b: Point): Point {
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
}

/** The two-finger gesture as it was when the second finger landed. */
export interface PinchStart {
  a: Point;
  b: Point;
  view: ViewState;
}

/** Two-finger update: scale the view about the fingers' centroid and follow the
 * centroid, so a two-finger drag pans while it pinches.
 *
 * Measured from the pinch start rather than frame to frame: accumulation would
 * let rounding drift the view, and the zoom is clamped to [MIN_ZOOM, MAX_ZOOM]
 * so an over-eager pinch cannot leave the user at an unusable scale. A
 * degenerate start (both fingers on one point) or non-finite input returns the
 * sanitized starting view instead of NaN. */
export function pinchUpdate(start: PinchStart, a: Point, b: Point): ViewState {
  const base = sanitizeView(start.view);
  const startDistance = pinchDistance(start.a, start.b);
  const distance = pinchDistance(a, b);
  if (!(startDistance > 0) || !(distance > 0)) return base;

  const zoom = clampZoom(base.zoom * (distance / startDistance));
  const ratio = zoom / base.zoom;
  const anchor = pinchMidpoint(start.a, start.b);
  const mid = pinchMidpoint(a, b);
  // The content point under the original centroid stays pinned to the moving
  // centroid: ratio scales it, `mid - anchor` pans with the fingers.
  const panX = mid.x - (anchor.x - base.panX) * ratio;
  const panY = mid.y - (anchor.y - base.panY) * ratio;
  return sanitizeView({ zoom, panX, panY });
}
