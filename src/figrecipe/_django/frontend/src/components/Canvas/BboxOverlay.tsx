/**
 * SVG bbox overlay — renders colored hit regions for all figure elements.
 * Invisible by default; shows stroke/fill on hover (like Flask editor).
 * Polylines for lines, circles for scatter, rectangles for everything else.
 */

import type { BBox } from "../../types/editor";

// Z-order: axes lowest (rendered first), text/labels highest
const Z_ORDER: Record<string, number> = {
  axes: 0,
  figure: 0,
  fill: 1,
  image: 2,
  contour: 2,
  bar: 3,
  pie: 3,
  quiver: 3,
  line: 4,
  linecollection: 4,
  scatter: 5,
  xticks: 6,
  yticks: 6,
  title: 7,
  xlabel: 7,
  ylabel: 7,
  suptitle: 7,
  legend: 8,
  text: 9,
  panel_label: 9,
};

// Distinct colors per type (used as --element-color)
const TYPE_COLOR: Record<string, string> = {
  line: "#ff6b6b",
  linecollection: "#ff6b6b",
  scatter: "#ffd93d",
  bar: "#6bcb77",
  barh: "#6bcb77",
  title: "#4d96ff",
  xlabel: "#4d96ff",
  ylabel: "#4d96ff",
  suptitle: "#4d96ff",
  legend: "#c77dff",
  axes: "#555566",
  image: "#ff9f43",
  fill: "#48dbfb",
  pie: "#ff6b9d",
  text: "#b8e0ff",
  xticks: "#888899",
  yticks: "#888899",
};

function typeColor(type: string): string {
  return TYPE_COLOR[type] ?? "#aaaaaa";
}

interface Props {
  bboxes: Record<string, BBox>;
  onElementClick: (elementId: string) => void;
  imgWidth: number;
  imgHeight: number;
  alwaysVisible?: boolean;
  selectedElement?: string | null;
  /** Elements drawn from the badged table columns: hover visual, no click,
   *  no Details change. Selection wins when both name the same element. */
  emphasizedElements?: string[];
}

export function BboxOverlay({
  bboxes,
  onElementClick,
  imgWidth,
  imgHeight,
  alwaysVisible,
  selectedElement,
  emphasizedElements,
}: Props) {
  if (!bboxes || Object.keys(bboxes).length === 0 || !imgWidth || !imgHeight) {
    return null;
  }

  const sorted = Object.entries(bboxes)
    .filter(([key]) => key !== "_meta")
    .sort(([, a], [, b]) => (Z_ORDER[a.type] ?? 5) - (Z_ORDER[b.type] ?? 5));

  return (
    <svg
      className={`bbox-overlay${alwaysVisible ? " bbox-overlay--visible" : ""}`}
      viewBox={`0 0 ${imgWidth} ${imgHeight}`}
    >
      {sorted.map(([key, bbox]) => {
        const color = typeColor(bbox.type);
        const isSelected = key === selectedElement;
        const isEmphasized =
          !isSelected && (emphasizedElements ?? []).includes(key);
        const stateClass = isSelected
          ? " bbox-group--selected"
          : isEmphasized
            ? " bbox-group--emphasized"
            : "";
        const bboxExt = bbox as BBox & { points?: [number, number][] };
        const shortLabel = bbox.label ?? key.split("_").slice(1).join("_");

        const handleClick = (e: React.MouseEvent) => {
          e.stopPropagation();
          onElementClick(key);
        };

        // Line / LineCollection — polyline tracing the actual path
        if (
          (bbox.type === "line" || bbox.type === "linecollection") &&
          bboxExt.points &&
          bboxExt.points.length > 1
        ) {
          const pts = bboxExt.points.map(([x, y]) => `${x},${y}`).join(" ");
          const [lx, ly] = bboxExt.points[0];
          return (
            <g
              key={key}
              className={`bbox-group${stateClass}`}
              style={{ "--element-color": color } as React.CSSProperties}
              onClick={handleClick}
            >
              <polyline className="bbox-polyline" points={pts} />
              <text className="bbox-label" x={lx + 2} y={Math.max(ly - 4, 8)}>
                {bbox.type}:{shortLabel}
              </text>
            </g>
          );
        }

        // Scatter — individual circles per point (like Flask _createScatterShape)
        if (
          bbox.type === "scatter" &&
          bboxExt.points &&
          bboxExt.points.length > 0
        ) {
          const [lx, ly] = bboxExt.points[0];
          const hitRadius = 8;
          return (
            <g
              key={key}
              className={`bbox-group${stateClass}`}
              style={{ "--element-color": color } as React.CSSProperties}
              onClick={handleClick}
            >
              {bboxExt.points.map(([cx, cy], idx) => (
                <circle
                  key={idx}
                  className="bbox-circle"
                  cx={cx}
                  cy={cy}
                  r={hitRadius}
                />
              ))}
              <text className="bbox-label" x={lx + 5} y={Math.max(ly - 5, 8)}>
                {bbox.type}:{shortLabel}
              </text>
            </g>
          );
        }

        // All other elements — rectangle
        return (
          <g
            key={key}
            className={`bbox-group bbox-group--${bbox.type}${stateClass}`}
            style={{ "--element-color": color } as React.CSSProperties}
            onClick={handleClick}
          >
            <rect
              className={`bbox-rect${bbox.type === "axes" ? " bbox-rect--axes" : ""}`}
              x={bbox.x}
              y={bbox.y}
              width={Math.max(bbox.width, 4)}
              height={Math.max(bbox.height, 4)}
            />
            <text
              className="bbox-label"
              x={bbox.x + 2}
              y={Math.max(bbox.y - 2, 8)}
            >
              {bbox.type}:{shortLabel}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
