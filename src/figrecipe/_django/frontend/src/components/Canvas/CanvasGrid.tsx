/** Zoom-aware canvas grid.
 *
 * Rendered INSIDE `.vis-canvas-container`, so it pans and zooms together with
 * the page it is drawn on (the transform scales the tiles for free). The rung of
 * the millimetre ladder is chosen from the current zoom in ./canvasGrid; the
 * layer itself is decoration only — canvas.css keeps it out of the pointer path.
 */

import { GRID_COLORS, gridPlanForZoom, gridStrokeWidth, gridTileDataUrl } from "./canvasGrid";

interface Props {
  /** Current view zoom — decides the grid rung and the hairline stroke. */
  zoom: number;
  dark: boolean;
}

export function CanvasGrid({ zoom, dark }: Props) {
  const plan = gridPlanForZoom(zoom);
  const colors = dark ? GRID_COLORS.dark : GRID_COLORS.light;
  const stroke = gridStrokeWidth(zoom);

  return (
    <div
      className={`canvas-grid-layer${plan.level === "coarse" ? " canvas-grid-layer--coarse" : ""}`}
      data-grid-level={plan.level}
      aria-hidden="true"
      style={{
        // Major first: the minor ruling has to stay readable where they cross.
        backgroundImage:
          `${gridTileDataUrl(plan.major, colors.major, stroke)}, ` +
          `${gridTileDataUrl(plan.minor, colors.minor, stroke)}`,
        backgroundSize: `${plan.major}px ${plan.major}px, ${plan.minor}px ${plan.minor}px`,
      }}
    />
  );
}
