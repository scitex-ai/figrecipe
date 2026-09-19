/** Hit-testing and selection decisions for the plot hitmap overlay.
 *
 * The hitmap PNG paints one flat colour per plot element (matplotlib artists,
 * axes, text, …) and the backend ships a `color_map` of element key to rgb. A
 * click therefore resolves as: pointer -> raster pixel -> colour -> element key.
 * Every decision in that chain lives here, free of React and of the @scitex/ui
 * alias, so it runs (and is asserted) under plain
 * `node --experimental-strip-types` — see tests/hitmapSelect.test.ts.
 * The overlay component is a thin shell that samples pixels and renders.
 */

/** RGBA sample, straight out of CanvasRenderingContext2D.getImageData(). */
export type PixelSample = ArrayLike<number> | null | undefined;

export interface SurfaceSize {
  width: number;
  height: number;
}

export interface Point {
  x: number;
  y: number;
}

/** `{ elementKey: { rgb: [r, g, b], label, type, axes_index, ... } }`. */
export type ColorMap = Record<string, unknown>;

/** "#rrggbb" for an [r, g, b] triple, or null when a channel is not a colour byte. */
export function rgbToHex(rgb: ArrayLike<unknown> | null | undefined): string | null {
  if (!rgb || rgb.length < 3) return null;
  const bytes: number[] = [];
  for (let i = 0; i < 3; i += 1) {
    const channel = rgb[i];
    if (typeof channel !== "number" || !Number.isFinite(channel)) return null;
    bytes.push(Math.max(0, Math.min(255, Math.round(channel))));
  }
  return `#${bytes.map((b) => b.toString(16).padStart(2, "0")).join("")}`;
}

/** Reverse lookup colour -> element key.
 *
 * Entries whose rgb is missing or malformed are skipped rather than throwing:
 * the Python side reserves some ids (background, non-selectable axes) that are
 * deliberately absent from the map, and a single bad entry must not cost the
 * user every other element on the plot. */
export function buildHexToElementKey(colorMap: ColorMap | null | undefined): Record<string, string> {
  const map: Record<string, string> = {};
  if (!colorMap) return map;
  for (const [key, info] of Object.entries(colorMap)) {
    const hex = rgbToHex((info as { rgb?: readonly unknown[] } | null | undefined)?.rgb);
    if (hex) map[hex] = key;
  }
  return map;
}

/** Human-readable name for an element key: the colorMap label, else the raw key
 * (labels live in the colorMap, so this is the only place that knows them). */
export function elementLabel(colorMap: ColorMap | null | undefined, key: string | null): string {
  if (!key) return "";
  const label = (colorMap?.[key] as { label?: unknown } | undefined)?.label;
  return typeof label === "string" && label.length > 0 ? label : key;
}

/** Pointer position (CSS px inside the overlay box) -> hitmap raster pixel, or
 * null when it falls outside the raster.
 *
 * WHY this guard has to come first: getImageData() THROWS on out-of-range
 * coordinates, and a pointer at the very edge of the box reports exactly
 * width/height — so a click near the border would otherwise take the canvas
 * down instead of being the no-op the user expects. */
export function hitmapPixelCoords(
  surface: SurfaceSize | null | undefined,
  pointer: Point,
  box: { width: number; height: number },
): Point | null {
  if (!surface || !(surface.width > 0) || !(surface.height > 0)) return null;
  if (!(box.width > 0) || !(box.height > 0)) return null;
  if (!Number.isFinite(pointer.x) || !Number.isFinite(pointer.y)) return null;
  const x = Math.floor((pointer.x * surface.width) / box.width);
  const y = Math.floor((pointer.y * surface.height) / box.height);
  if (x < 0 || y < 0 || x >= surface.width || y >= surface.height) return null;
  return { x, y };
}

/** The element key a sampled hitmap pixel resolves to; null means "no element
 * here" (empty background, a transparent pixel, or a colour the colorMap does
 * not know).
 *
 * `ready` is false until the hitmap PNG has been decoded onto the scratch
 * canvas: before that every sample would read back as transparent black and we
 * must not resolve anything. */
export function resolveElementKey(input: {
  ready: boolean;
  pixel: PixelSample;
  hexToKey: Record<string, string>;
}): string | null {
  if (!input.ready) return null;
  const pixel = input.pixel;
  if (!pixel || pixel.length < 4) return null;
  const alpha = pixel[3];
  if (typeof alpha !== "number" || !Number.isFinite(alpha) || alpha <= 0) return null;
  const hex = rgbToHex(pixel);
  if (!hex) return null;
  return input.hexToKey[hex] ?? null;
}

/** What the store should do after a hit test. */
export type SelectionOutcome =
  | { kind: "select"; elementId: string }
  | { kind: "clear" }
  | { kind: "unchanged" };

/** Does the loaded hitmap belong to this figure?
 *
 * A hitmap raster is rendered server-side for ONE recipe — the one the editor
 * has open — and the store keeps exactly one of them. Without this identity the
 * overlay sampled that raster on every selected figure and resolved its colours
 * against that other figure's elements: clicking figure B selected (and then
 * edited) whatever element of figure A happened to share the pixel's colour.
 * Two figures placed from the SAME recipe are the same picture, which is why the
 * identity is the recipe and not the figure's id. */
export function hitmapMatchesFigure(
  hitmapRecipe: string | null | undefined,
  figureRecipe: string | null | undefined,
): boolean {
  if (!hitmapRecipe || !figureRecipe) return false;
  return hitmapRecipe === figureRecipe;
}

/** The element key under a sampled pixel, for THIS figure only.
 *
 * Same chain as resolveElementKey with the identity gate in front, so a raster
 * that depicts another recipe can never select anything here — and so a caller
 * cannot forget the gate. */
export function resolveFigureHit(input: {
  hitmapRecipe: string | null | undefined;
  figureRecipe: string | null | undefined;
  ready: boolean;
  pixel: PixelSample;
  hexToKey: Record<string, string>;
}): string | null {
  if (!hitmapMatchesFigure(input.hitmapRecipe, input.figureRecipe)) return null;
  return resolveElementKey({
    ready: input.ready,
    pixel: input.pixel,
    hexToKey: input.hexToKey,
  });
}

/** Selection transition for a click / Enter on `hit` (null = empty background).
 *
 * A miss CLEARS: leaving the previously clicked element highlighted while the
 * user clicks empty canvas is the stale-selection bug, and a miss with nothing
 * selected stays a no-op so a stray click never writes to the store. */
export function selectionAfterHit(current: string | null, hit: string | null): SelectionOutcome {
  if (hit) return hit === current ? { kind: "unchanged" } : { kind: "select", elementId: hit };
  return current ? { kind: "clear" } : { kind: "unchanged" };
}

/** Escape always drops the selection (nothing to do when it is already empty). */
export function selectionAfterClear(current: string | null): SelectionOutcome {
  return current ? { kind: "clear" } : { kind: "unchanged" };
}

/** Keyboard reticle position, as a fraction of the overlay box (0..1). */
export interface FocusPoint {
  x: number;
  y: number;
}

export const DEFAULT_FOCUS_POINT: FocusPoint = { x: 0.5, y: 0.5 };

/** Arrow-key step, in box fractions (2% ≈ a few px on a placed figure). */
export const FOCUS_STEP = 0.02;

export type FocusKey = "ArrowUp" | "ArrowDown" | "ArrowLeft" | "ArrowRight";

export function isFocusKey(key: string): key is FocusKey {
  return key === "ArrowUp" || key === "ArrowDown" || key === "ArrowLeft" || key === "ArrowRight";
}

/** Move the keyboard reticle, clamped to the box: the reticle must never leave
 * the surface, because a point outside it would hit-test outside the raster. */
export function moveFocusPoint(point: FocusPoint, key: FocusKey, step = FOCUS_STEP): FocusPoint {
  const delta = Number.isFinite(step) && step > 0 ? step : FOCUS_STEP;
  const next = {
    x: Number.isFinite(point.x) ? point.x : DEFAULT_FOCUS_POINT.x,
    y: Number.isFinite(point.y) ? point.y : DEFAULT_FOCUS_POINT.y,
  };
  if (key === "ArrowLeft") next.x -= delta;
  else if (key === "ArrowRight") next.x += delta;
  else if (key === "ArrowUp") next.y -= delta;
  else next.y += delta;
  return { x: Math.min(1, Math.max(0, next.x)), y: Math.min(1, Math.max(0, next.y)) };
}

/** The reticle's position in CSS px inside the overlay box. */
export function focusPointToPixels(
  focus: FocusPoint,
  box: { width: number; height: number },
): Point {
  return { x: focus.x * box.width, y: focus.y * box.height };
}
