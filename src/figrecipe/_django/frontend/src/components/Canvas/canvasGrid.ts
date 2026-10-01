/** Zoom-aware grid ladder for the canvas page.
 *
 * The page is a fixed 300 dpi sheet (1 mm = 11.811 canvas px) that the view
 * transform scales, so ONE fixed background grid cannot work: at zoom 0.1 a
 * 1 mm grid lands on 1.2 screen px (a solid smear) and at zoom 5.0 the same
 * tile is a moiré of fat lines. This module picks the rung of the 1-2-5 ladder
 * that keeps the minor grid inside a legible on-screen band, so the board always
 * reads as millimetre paper instead of noise.
 *
 * Pure and React-free: the CanvasGrid component only turns a plan into CSS —
 * see tests/canvasGrid.test.ts.
 */

/** 1 mm at 300 dpi — the same constant the ruler and the vis_app grid use. */
export const MM_PX = 11.811023622047244;

/** Minor-grid spacing must land at or above this many SCREEN px; below it the
 * lines merge into a block and the grid stops being readable. */
export const MIN_SCREEN_SPACING_PX = 10;

/** 0.5 mm … 100 mm: the rungs the physical grid is built from. */
const LADDER = [0.5, 1, 2, 5, 10, 20, 50, 100] as const;

export type GridLevelName = "fine" | "coarse";

export interface GridPlan {
  /** "coarse" once the drawn grid is 5× the millimetre grid or more. */
  level: GridLevelName;
  /** Minor-line spacing in canvas px, before the view scale. */
  minor: number;
  /** Major-line spacing: a decade above the minor grid (mm-paper convention). */
  major: number;
  /** The minor spacing as it will appear on screen (minor × zoom). */
  minorScreen: number;
}

/** Grid colours, identical to the fixed CSS grid this layer replaces. */
export const GRID_COLORS: Record<"light" | "dark", { minor: string; major: string }> = {
  light: { minor: "#ccc8c4", major: "#aaa6a2" },
  dark: { minor: "#505050", major: "#707070" },
};

/** Choose the grid rung for a zoom level. Non-finite or non-positive zooms fall
 * back to 1:1 rather than producing a NaN spacing (and therefore a blank page). */
export function gridPlanForZoom(zoom: number): GridPlan {
  const safeZoom = Number.isFinite(zoom) && zoom > 0 ? zoom : 1;
  const unit =
    LADDER.find((mm) => MM_PX * mm * safeZoom >= MIN_SCREEN_SPACING_PX) ??
    LADDER[LADDER.length - 1];
  const minor = MM_PX * unit;
  return {
    level: unit >= 5 ? "coarse" : "fine",
    minor,
    major: minor * 10,
    minorScreen: minor * safeZoom,
  };
}

/** Stroke width (canvas px) that renders as a ~1 screen px hairline.
 *
 * WHY counter-scaled: the grid layer lives INSIDE the transformed page so it
 * pans and zooms for free — which also means a fixed stroke would be 0.1 px at
 * zoom 0.1 (invisible) and 5 px at zoom 5.0 (a slab). */
export function gridStrokeWidth(zoom: number): number {
  const safeZoom = Number.isFinite(zoom) && zoom > 0 && zoom <= 20 ? zoom : 1;
  return 1 / safeZoom;
}

/** A repeating tile holding one grid line along its top and left edges.
 *
 * The line hugs the tile border so adjacent tiles join into a continuous grid;
 * `spacing` is the tile's own size, which is what makes the grid scale with the
 * view instead of the viewport. */
export function gridTileDataUrl(spacing: number, color: string, strokeWidth: number): string {
  const size = Number.isFinite(spacing) && spacing > 0 ? spacing : MM_PX;
  const width = Number.isFinite(strokeWidth) && strokeWidth > 0 ? strokeWidth : 1;
  const svg =
    `<svg xmlns='http://www.w3.org/2000/svg' width='${size}' height='${size}'>` +
    `<path d='M ${size} 0 L 0 0 L 0 ${size}' fill='none' stroke='${color}' stroke-width='${width}'/>` +
    `</svg>`;
  return `url("data:image/svg+xml,${encodeURIComponent(svg)}")`;
}
