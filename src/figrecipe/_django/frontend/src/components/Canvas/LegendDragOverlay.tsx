/**
 * LegendDragOverlay — drag a legend to reposition it on the canvas.
 *
 * Rendered over a legend element's bbox (image-pixel coords inside the figure
 * container, which the canvas scales by `zoom`). Dragging reports the legend's
 * new top-left in image pixels via onDragEnd; the parent (PlacedFigure) converts
 * that to an axes-fraction anchor and calls moveLegend → update_legend_position.
 * Modeled on PanelLetterOverlay's drag handling.
 */

import { useCallback, useRef, useState } from "react";

interface Props {
  /** Legend bbox in image pixels (x, y = top-left). */
  bbox: { x: number; y: number; width: number; height: number };
  /** Canvas zoom (client px per image px) — to convert drag deltas. */
  zoom: number;
  /** Called on drop with the legend's new top-left in image pixels. */
  onDragEnd: (imgX: number, imgY: number) => void;
}

export function LegendDragOverlay({ bbox, zoom, onDragEnd }: Props) {
  const [drag, setDrag] = useState<{ dx: number; dy: number } | null>(null);
  const origin = useRef<{ mx: number; my: number } | null>(null);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      e.preventDefault();
      origin.current = { mx: e.clientX, my: e.clientY };
      setDrag({ dx: 0, dy: 0 });

      const move = (ev: MouseEvent) => {
        if (!origin.current) return;
        // client px → image px (the canvas is scaled by zoom)
        const dx = (ev.clientX - origin.current.mx) / zoom;
        const dy = (ev.clientY - origin.current.my) / zoom;
        setDrag({ dx, dy });
      };
      const up = (ev: MouseEvent) => {
        window.removeEventListener("mousemove", move);
        window.removeEventListener("mouseup", up);
        if (origin.current) {
          const dx = (ev.clientX - origin.current.mx) / zoom;
          const dy = (ev.clientY - origin.current.my) / zoom;
          origin.current = null;
          setDrag(null);
          // Only commit a real move (ignore stray clicks).
          if (Math.abs(dx) > 1 || Math.abs(dy) > 1) {
            onDragEnd(bbox.x + dx, bbox.y + dy);
          }
        }
      };
      window.addEventListener("mousemove", move);
      window.addEventListener("mouseup", up);
    },
    [bbox.x, bbox.y, zoom, onDragEnd],
  );

  return (
    <div
      className={`legend-drag-overlay${drag ? " dragging" : ""}`}
      style={{
        position: "absolute",
        left: bbox.x + (drag?.dx ?? 0),
        top: bbox.y + (drag?.dy ?? 0),
        width: bbox.width,
        height: bbox.height,
        cursor: "move",
      }}
      onMouseDown={handleMouseDown}
      title="Drag to move legend"
    />
  );
}
