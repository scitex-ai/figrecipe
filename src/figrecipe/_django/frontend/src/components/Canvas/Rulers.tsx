/**
 * SVG Rulers — exact port from vis_app RulerSvgGenerators.ts.
 *
 * Renders at full canvas resolution (scales with zoom/pan transform).
 * Tick intervals, positions, colors — identical to vis_app.
 * Click any label to toggle mm/inch.
 */

import { useMemo } from "react";
import { useEditorStore } from "../../store/useEditorStore";
import { gettext, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

export const RULER_SIZE = 60;
const COLUMN_WIDTH_MM = 90; // 90mm = 1 column (journal standard)

// ── Theme colors (vis_app RulerSvgGenerators.ts) ──────────

function getRulerColors(isDark: boolean) {
  return {
    majorColor: isDark ? "#ccc" : "#888",
    textColor: isDark ? "#aaa" : "#555",
    minorColor: isDark ? "#666" : "#aaa",
    columnLabelColor: isDark ? "#aaa" : "#555",
  };
}

// ── SVG Generators (direct port from vis_app) ─────────────

function generateHorizontalRulerMm(
  width: number,
  dpi: number,
  rulerHeight: number,
  isDark: boolean,
): string {
  const pxToMm = (px: number) => (px / dpi) * 25.4;
  const mmToPx = (mm: number) => (mm * dpi) / 25.4;
  const { majorColor, textColor, minorColor, columnLabelColor } =
    getRulerColors(isDark);

  const maxMm = pxToMm(width);
  let svg = "";

  // 0mm tick
  svg += `<line x1="0" y1="40" x2="0" y2="${rulerHeight}" stroke="${majorColor}" stroke-width="1.5"/>`;
  svg += `<text x="3" y="35" text-anchor="start" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer"><title>${interpolate(gettext("%s (click to toggle inch)"), ["0mm"])}</title>0mm</text>`;

  for (let mm = 1; mm <= maxMm; mm++) {
    const x = mmToPx(mm);
    if (mm % 10 === 0) {
      svg += `<line x1="${x}" y1="40" x2="${x}" y2="${rulerHeight}" stroke="${majorColor}" stroke-width="1.5"/>`;
      svg += `<text x="${x}" y="35" text-anchor="middle" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer"><title>${interpolate(gettext("%s (click to toggle inch)"), [mm + "mm"])}</title>${mm}mm</text>`;
    } else if (mm % 5 === 0) {
      svg += `<line x1="${x}" y1="48" x2="${x}" y2="${rulerHeight}" stroke="${majorColor}" stroke-width="1"/>`;
    } else {
      svg += `<line x1="${x}" y1="54" x2="${x}" y2="${rulerHeight}" stroke="${minorColor}" stroke-width="0.5"/>`;
    }
  }

  // Column width markers (vis_app: 0.5, 1.0, 1.5, 2.0 col)
  const colMarkers = [
    { mm: COLUMN_WIDTH_MM * 0.5, label: interpolate(gettext("%s col"), ["0.5"]) },
    { mm: COLUMN_WIDTH_MM * 1.0, label: interpolate(gettext("%s col"), ["1.0"]) },
    { mm: COLUMN_WIDTH_MM * 1.5, label: interpolate(gettext("%s col"), ["1.5"]) },
    { mm: COLUMN_WIDTH_MM * 2.0, label: interpolate(gettext("%s col"), ["2.0"]) },
  ];
  colMarkers.forEach(({ mm, label }) => {
    const x = mmToPx(mm);
    if (x <= width) {
      svg += `<text x="${x}" y="12" text-anchor="middle" font-size="11" fill="${columnLabelColor}" font-weight="500">${label}</text>`;
    }
  });

  return svg;
}

function generateHorizontalRulerInch(
  width: number,
  dpi: number,
  rulerHeight: number,
  isDark: boolean,
): string {
  const inchToPx = (inch: number) => inch * dpi;
  const { majorColor, textColor, minorColor, columnLabelColor } =
    getRulerColors(isDark);

  const maxInch = width / dpi;
  let svg = "";

  for (let inch = 0; inch <= maxInch; inch++) {
    const x = inchToPx(inch);
    svg += `<line x1="${x}" y1="40" x2="${x}" y2="${rulerHeight}" stroke="${majorColor}" stroke-width="1.5"/>`;
    if (inch === 0) {
      svg += `<text x="3" y="35" text-anchor="start" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer"><title>${interpolate(gettext("%s (click to toggle mm)"), ['0"'])}</title>0"</text>`;
    } else {
      svg += `<text x="${x}" y="35" text-anchor="middle" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer"><title>${interpolate(gettext("%s (click to toggle mm)"), [inch + '"'])}</title>${inch}"</text>`;
    }
  }

  // Fractional inch markers (1/2, 1/4, 1/8, 1/16) — exact vis_app
  const fractions = [
    { divisor: 2, y: 48, stroke: majorColor, width: "1" },
    { divisor: 4, y: 51, stroke: majorColor, width: "0.8" },
    { divisor: 8, y: 54, stroke: minorColor, width: "0.6" },
    { divisor: 16, y: 56, stroke: minorColor, width: "0.4" },
  ];
  fractions.forEach((frac) => {
    for (let inch = 0; inch <= maxInch; inch++) {
      for (let i = 1; i < frac.divisor; i++) {
        if (i % 2 === 0 && frac.divisor > 2) continue;
        if (i % 4 === 0 && frac.divisor > 4) continue;
        if (i % 8 === 0 && frac.divisor > 8) continue;
        const x = inchToPx(inch + i / frac.divisor);
        if (x <= width) {
          svg += `<line x1="${x}" y1="${frac.y}" x2="${x}" y2="${rulerHeight}" stroke="${frac.stroke}" stroke-width="${frac.width}"/>`;
        }
      }
    }
  });

  // Column markers in inch
  const colMarkersInch = [
    { inch: (COLUMN_WIDTH_MM * 0.5) / 25.4, label: interpolate(gettext("%s col"), ["0.5"]) },
    { inch: (COLUMN_WIDTH_MM * 1.0) / 25.4, label: interpolate(gettext("%s col"), ["1.0"]) },
    { inch: (COLUMN_WIDTH_MM * 1.5) / 25.4, label: interpolate(gettext("%s col"), ["1.5"]) },
    { inch: (COLUMN_WIDTH_MM * 2.0) / 25.4, label: interpolate(gettext("%s col"), ["2.0"]) },
  ];
  colMarkersInch.forEach(({ inch, label }) => {
    const x = inchToPx(inch);
    if (x <= width) {
      svg += `<text x="${x}" y="12" text-anchor="middle" font-size="11" fill="${columnLabelColor}" font-weight="500">${label}</text>`;
    }
  });

  return svg;
}

function generateVerticalRulerMm(
  height: number,
  dpi: number,
  rulerWidth: number,
  isDark: boolean,
): string {
  const pxToMm = (px: number) => (px / dpi) * 25.4;
  const mmToPx = (mm: number) => (mm * dpi) / 25.4;
  const { majorColor, textColor, minorColor } = getRulerColors(isDark);

  const maxMm = pxToMm(height);
  let svg = "";

  // 0mm tick
  svg += `<line x1="40" y1="0" x2="${rulerWidth}" y2="0" stroke="${majorColor}" stroke-width="1.5"/>`;
  svg += `<text x="30" y="8" text-anchor="middle" dominant-baseline="middle" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer" transform="rotate(-90, 30, 8)"><title>${interpolate(gettext("%s (click to toggle inch)"), ["0mm"])}</title>0mm</text>`;

  for (let mm = 1; mm <= maxMm; mm++) {
    const y = mmToPx(mm);
    if (mm % 10 === 0) {
      svg += `<line x1="40" y1="${y}" x2="${rulerWidth}" y2="${y}" stroke="${majorColor}" stroke-width="1.5"/>`;
      svg += `<text x="30" y="${y}" text-anchor="middle" dominant-baseline="middle" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer" transform="rotate(-90, 30, ${y})"><title>${interpolate(gettext("%s (click to toggle inch)"), [mm + "mm"])}</title>${mm}mm</text>`;
    } else if (mm % 5 === 0) {
      svg += `<line x1="48" y1="${y}" x2="${rulerWidth}" y2="${y}" stroke="${majorColor}" stroke-width="1"/>`;
    } else {
      svg += `<line x1="54" y1="${y}" x2="${rulerWidth}" y2="${y}" stroke="${minorColor}" stroke-width="0.5"/>`;
    }
  }

  return svg;
}

function generateVerticalRulerInch(
  height: number,
  dpi: number,
  rulerWidth: number,
  isDark: boolean,
): string {
  const inchToPx = (inch: number) => inch * dpi;
  const { majorColor, textColor, minorColor } = getRulerColors(isDark);

  const maxInch = height / dpi;
  let svg = "";

  for (let inch = 0; inch <= maxInch; inch++) {
    const y = inchToPx(inch);
    svg += `<line x1="40" y1="${y}" x2="${rulerWidth}" y2="${y}" stroke="${majorColor}" stroke-width="1.5"/>`;
    if (inch === 0) {
      svg += `<text x="30" y="8" text-anchor="middle" dominant-baseline="middle" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer" transform="rotate(-90, 30, 8)"><title>${interpolate(gettext("%s (click to toggle mm)"), ['0"'])}</title>0"</text>`;
    } else {
      svg += `<text x="30" y="${y}" text-anchor="middle" dominant-baseline="middle" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer" transform="rotate(-90, 30, ${y})"><title>${interpolate(gettext("%s (click to toggle mm)"), [inch + '"'])}</title>${inch}"</text>`;
    }
  }

  // Fractional inch markers
  const fractions = [
    { divisor: 2, x: 48, stroke: majorColor, width: "1" },
    { divisor: 4, x: 51, stroke: majorColor, width: "0.8" },
    { divisor: 8, x: 54, stroke: minorColor, width: "0.6" },
    { divisor: 16, x: 56, stroke: minorColor, width: "0.4" },
  ];
  fractions.forEach((frac) => {
    for (let inch = 0; inch <= maxInch; inch++) {
      for (let i = 1; i < frac.divisor; i++) {
        if (i % 2 === 0 && frac.divisor > 2) continue;
        if (i % 4 === 0 && frac.divisor > 4) continue;
        if (i % 8 === 0 && frac.divisor > 8) continue;
        const y = inchToPx(inch + i / frac.divisor);
        if (y <= height) {
          svg += `<line x1="${frac.x}" y1="${y}" x2="${rulerWidth}" y2="${y}" stroke="${frac.stroke}" stroke-width="${frac.width}"/>`;
        }
      }
    }
  });

  return svg;
}

// ── React Components ──────────────────────────────────────

interface HRulerProps {
  canvasWidth: number;
  dpi: number;
  gridArea: string;
  onMouseDown?: (e: React.MouseEvent) => void;
  onDoubleClick?: (e: React.MouseEvent) => void;
}

export function HorizontalRuler({ canvasWidth, dpi, gridArea, onMouseDown, onDoubleClick }: HRulerProps) {
  const darkMode = useEditorStore((s) => s.darkMode);
  const rulerUnit = useEditorStore((s) => s.rulerUnit);
  const toggleRulerUnit = useEditorStore((s) => s.toggleRulerUnit);

  const svgContent = useMemo(() => {
    if (rulerUnit === "mm")
      return generateHorizontalRulerMm(canvasWidth, dpi, RULER_SIZE, darkMode);
    return generateHorizontalRulerInch(canvasWidth, dpi, RULER_SIZE, darkMode);
  }, [canvasWidth, dpi, rulerUnit, darkMode]);

  return (
    <div className="ruler ruler-horizontal" style={{ gridArea }} onMouseDown={onMouseDown} onDoubleClick={onDoubleClick}>
      <svg
        width={canvasWidth}
        height={RULER_SIZE}
        viewBox={`0 0 ${canvasWidth} ${RULER_SIZE}`}
        style={{ width: canvasWidth, height: RULER_SIZE, display: "block" }}
        onClick={toggleRulerUnit}
        dangerouslySetInnerHTML={{ __html: svgContent }}
      />
    </div>
  );
}

interface VRulerProps {
  canvasHeight: number;
  dpi: number;
  gridArea: string;
  onMouseDown?: (e: React.MouseEvent) => void;
  onDoubleClick?: (e: React.MouseEvent) => void;
}

export function VerticalRuler({ canvasHeight, dpi, gridArea, onMouseDown, onDoubleClick }: VRulerProps) {
  const darkMode = useEditorStore((s) => s.darkMode);
  const rulerUnit = useEditorStore((s) => s.rulerUnit);
  const toggleRulerUnit = useEditorStore((s) => s.toggleRulerUnit);

  const svgContent = useMemo(() => {
    if (rulerUnit === "mm")
      return generateVerticalRulerMm(canvasHeight, dpi, RULER_SIZE, darkMode);
    return generateVerticalRulerInch(canvasHeight, dpi, RULER_SIZE, darkMode);
  }, [canvasHeight, dpi, rulerUnit, darkMode]);

  return (
    <div className="ruler ruler-vertical" style={{ gridArea }} onMouseDown={onMouseDown} onDoubleClick={onDoubleClick}>
      <svg
        width={RULER_SIZE}
        height={canvasHeight}
        viewBox={`0 0 ${RULER_SIZE} ${canvasHeight}`}
        style={{ width: RULER_SIZE, height: canvasHeight, display: "block" }}
        onClick={toggleRulerUnit}
        dangerouslySetInnerHTML={{ __html: svgContent }}
      />
    </div>
  );
}
