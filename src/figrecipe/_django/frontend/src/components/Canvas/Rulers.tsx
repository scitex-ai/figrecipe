/**
 * SVG Rulers — exact port from vis_app RulerSvgGenerators.ts.
 *
 * Renders at full canvas resolution (scales with zoom/pan transform).
 * Tick intervals, positions, colors — identical to vis_app.
 * Click any label to toggle mm/inch.
 */

import { useMemo } from "react";
import { useEditorStore } from "../../store/useEditorStore";
import { gettext, interpolate } from "@scitex/sdk/ui/ts/_base/gettext.ts";

export const RULER_SIZE = 60;
export const COLUMN_WIDTH_MM = 90; // 90mm = 1 column (journal standard)

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

  // 0 tick: bare number (the unit is shown once per axis, at the far end —
  // a unit on every tick collides at fit zoom: "0mm10mm").
  svg += `<line x1="0" y1="40" x2="0" y2="${rulerHeight}" stroke="${majorColor}" stroke-width="1.5"/>`;
  svg += `<text x="3" y="35" text-anchor="start" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer"><title>${interpolate(gettext("%s (click to toggle inch)"), ["0mm"])}</title>0</text>`;

  for (let mm = 1; mm <= maxMm; mm++) {
    const x = mmToPx(mm);
    if (mm % 10 === 0) {
      svg += `<line x1="${x}" y1="40" x2="${x}" y2="${rulerHeight}" stroke="${majorColor}" stroke-width="1.5"/>`;
      svg += `<text x="${x}" y="35" text-anchor="middle" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer"><title>${interpolate(gettext("%s (click to toggle inch)"), [mm + "mm"])}</title>${mm}</text>`;
    } else if (mm % 5 === 0) {
      svg += `<line x1="${x}" y1="48" x2="${x}" y2="${rulerHeight}" stroke="${majorColor}" stroke-width="1"/>`;
    } else {
      svg += `<line x1="${x}" y1="54" x2="${x}" y2="${rulerHeight}" stroke="${minorColor}" stroke-width="0.5"/>`;
    }
  }

  // Column width markers: only the guided columns (0.5 / 1.5 — the dotted
  // canvas guides live there). 1.0/2.0 duplicated the mm scale beneath them.
  const colMarkers = [
    { mm: COLUMN_WIDTH_MM * 0.5, label: interpolate(gettext("%s col"), ["0.5"]) },
    { mm: COLUMN_WIDTH_MM * 1.5, label: interpolate(gettext("%s col"), ["1.5"]) },
  ];
  colMarkers.forEach(({ mm, label }) => {
    const x = mmToPx(mm);
    if (x <= width) {
      svg += `<text x="${x}" y="12" text-anchor="middle" font-size="11" fill="${columnLabelColor}" font-weight="500">${label}</text>`;
    }
  });

  // The unit, once per axis, at the far end of the label row.
  svg += `<text x="${width - 4}" y="12" text-anchor="end" font-size="11" fill="${columnLabelColor}" font-weight="600">mm</text>`;

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
      svg += `<text x="3" y="35" text-anchor="start" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer"><title>${interpolate(gettext("%s (click to toggle mm)"), ['0"'])}</title>0</text>`;
    } else {
      svg += `<text x="${x}" y="35" text-anchor="middle" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer"><title>${interpolate(gettext("%s (click to toggle mm)"), [inch + '"'])}</title>${inch}</text>`;
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

  // Column markers in inch (guided columns only — see mm generator).
  const colMarkersInch = [
    { inch: (COLUMN_WIDTH_MM * 0.5) / 25.4, label: interpolate(gettext("%s col"), ["0.5"]) },
    { inch: (COLUMN_WIDTH_MM * 1.5) / 25.4, label: interpolate(gettext("%s col"), ["1.5"]) },
  ];
  colMarkersInch.forEach(({ inch, label }) => {
    const x = inchToPx(inch);
    if (x <= width) {
      svg += `<text x="${x}" y="12" text-anchor="middle" font-size="11" fill="${columnLabelColor}" font-weight="500">${label}</text>`;
    }
  });

  // The unit, once per axis, at the far end of the label row.
  svg += `<text x="${width - 4}" y="12" text-anchor="end" font-size="11" fill="${columnLabelColor}" font-weight="600">in</text>`;

  return svg;
}

function generateVerticalRulerMm(
  height: number,
  dpi: number,
  rulerWidth: number,
  isDark: boolean,
  mirror = false,
): string {
  const pxToMm = (px: number) => (px / dpi) * 25.4;
  const mmToPx = (mm: number) => (mm * dpi) / 25.4;
  const { majorColor, textColor, minorColor } = getRulerColors(isDark);
  // Mirrored (right-hand) ruler: the tick roots sit at x=0 (page edge) and
  // grow right; labels sit at rulerWidth-30. Otherwise roots at the right.
  const root = (x: number) => (mirror ? rulerWidth - x : x);
  const edge = mirror ? 0 : rulerWidth;
  const labelX = mirror ? rulerWidth - 30 : 30;

  const maxMm = pxToMm(height);
  let svg = "";

  // 0 tick: bare number (unit once per axis, at the far end).
  svg += `<line x1="${root(40)}" y1="0" x2="${edge}" y2="0" stroke="${majorColor}" stroke-width="1.5"/>`;
  svg += `<text x="${labelX}" y="8" text-anchor="middle" dominant-baseline="middle" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer" transform="rotate(-90, ${labelX}, 8)"><title>${interpolate(gettext("%s (click to toggle inch)"), ["0mm"])}</title>0</text>`;

  for (let mm = 1; mm <= maxMm; mm++) {
    const y = mmToPx(mm);
    if (mm % 10 === 0) {
      svg += `<line x1="${root(40)}" y1="${y}" x2="${edge}" y2="${y}" stroke="${majorColor}" stroke-width="1.5"/>`;
      svg += `<text x="${labelX}" y="${y}" text-anchor="middle" dominant-baseline="middle" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer" transform="rotate(-90, ${labelX}, ${y})"><title>${interpolate(gettext("%s (click to toggle inch)"), [mm + "mm"])}</title>${mm}</text>`;
    } else if (mm % 5 === 0) {
      svg += `<line x1="${root(48)}" y1="${y}" x2="${edge}" y2="${y}" stroke="${majorColor}" stroke-width="1"/>`;
    } else {
      svg += `<line x1="${root(54)}" y1="${y}" x2="${edge}" y2="${y}" stroke="${minorColor}" stroke-width="0.5"/>`;
    }
  }

  // The unit, once per axis, at the far (bottom) end.
  svg += `<text x="${labelX}" y="${height - 6}" text-anchor="middle" dominant-baseline="middle" font-size="11" fill="${textColor}" font-weight="600" transform="rotate(-90, ${labelX}, ${height - 6})">mm</text>`;

  return svg;
}

function generateVerticalRulerInch(
  height: number,
  dpi: number,
  rulerWidth: number,
  isDark: boolean,
  mirror = false,
): string {
  const inchToPx = (inch: number) => inch * dpi;
  const { majorColor, textColor, minorColor } = getRulerColors(isDark);
  const root = (x: number) => (mirror ? rulerWidth - x : x);
  const edge = mirror ? 0 : rulerWidth;
  const labelX = mirror ? rulerWidth - 30 : 30;

  const maxInch = height / dpi;
  let svg = "";

  for (let inch = 0; inch <= maxInch; inch++) {
    const y = inchToPx(inch);
    svg += `<line x1="${root(40)}" y1="${y}" x2="${edge}" y2="${y}" stroke="${majorColor}" stroke-width="1.5"/>`;
    if (inch === 0) {
      svg += `<text x="${labelX}" y="8" text-anchor="middle" dominant-baseline="middle" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer" transform="rotate(-90, ${labelX}, 8)"><title>${interpolate(gettext("%s (click to toggle mm)"), ['0"'])}</title>0</text>`;
    } else {
      svg += `<text x="${labelX}" y="${y}" text-anchor="middle" dominant-baseline="middle" font-size="11" fill="${textColor}" class="ruler-label" style="cursor:pointer" transform="rotate(-90, ${labelX}, ${y})"><title>${interpolate(gettext("%s (click to toggle mm)"), [inch + '"'])}</title>${inch}</text>`;
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
          svg += `<line x1="${root(frac.x)}" y1="${y}" x2="${edge}" y2="${y}" stroke="${frac.stroke}" stroke-width="${frac.width}"/>`;
        }
      }
    }
  });

  // The unit, once per axis, at the far (bottom) end.
  svg += `<text x="${labelX}" y="${height - 6}" text-anchor="middle" dominant-baseline="middle" font-size="11" fill="${textColor}" font-weight="600" transform="rotate(-90, ${labelX}, ${height - 6})">in</text>`;

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
  /** Right-hand ruler: ticks + labels face the page (left edge) instead of out. */
  mirror?: boolean;
  onMouseDown?: (e: React.MouseEvent) => void;
  onDoubleClick?: (e: React.MouseEvent) => void;
}

export function VerticalRuler({ canvasHeight, dpi, gridArea, mirror, onMouseDown, onDoubleClick }: VRulerProps) {
  const darkMode = useEditorStore((s) => s.darkMode);
  const rulerUnit = useEditorStore((s) => s.rulerUnit);
  const toggleRulerUnit = useEditorStore((s) => s.toggleRulerUnit);

  const svgContent = useMemo(() => {
    if (rulerUnit === "mm")
      return generateVerticalRulerMm(canvasHeight, dpi, RULER_SIZE, darkMode, mirror);
    return generateVerticalRulerInch(canvasHeight, dpi, RULER_SIZE, darkMode, mirror);
  }, [canvasHeight, dpi, rulerUnit, darkMode, mirror]);

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
