/**
 * Main canvas — vis_app architecture.
 *
 * Outer container captures zoom/pan events.
 * Inner .vis-rulers-area (3x3 grid) gets CSS transform.
 * Rulers and canvas move as one object.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useContextMenu } from "../../hooks/useContextMenu";
import { CANVAS_H, CANVAS_W, DPI } from "../../hooks/useSnap";
import { useEditorStore } from "../../store/useEditorStore";
import { ContextMenu } from "../ContextMenu/ContextMenu";
import { CanvasGrid } from "./CanvasGrid";
import { PlacedFigure } from "./PlacedFigure";
import { HorizontalRuler, VerticalRuler } from "./Rulers";
import { SnapGuides } from "./SnapGuides";
import { useZoomPan } from "./useZoomPan";
import { gettext } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

// ── Main Canvas ──────────────────────────────────────────────
export function Canvas() {
  const {
    placedFigures,
    rulerUnit,
    toggleRulerUnit,
    selectFigure,
    darkMode,
    activeSnapGuides,
  } = useEditorStore();

  const {
    menu,
    show: showContextMenu,
    hide: hideContextMenu,
  } = useContextMenu();

  // ── Marquee selection state ───────────────────────────
  const [marquee, setMarquee] = useState<{
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  } | null>(null);
  const canvasRef = useRef<HTMLDivElement>(null);

  const outerRef = useRef<HTMLDivElement>(null);
  const {
    zoom,
    zoomIn,
    zoomOut,
    zoomToFit,
    resetView,
    transformStyle,
    isPanning,
    handleRulerMouseDown,
    handleRulerDoubleClick,
  } = useZoomPan(outerRef);

  // Expose zoom controls to store for toolbar access
  const fitCanvas = useCallback(() => {
    zoomToFit(CANVAS_W, CANVAS_H);
  }, [zoomToFit]);

  useEffect(() => {
    useEditorStore.setState({
      zoomControls: { zoomIn, zoomOut, zoomToFit: fitCanvas, resetView },
    });
  }, [zoomIn, zoomOut, fitCanvas, resetView]);

  // Auto-fit once per FIGURE SET, remembered in the session store rather than in
  // a component ref: the canvas unmounts on every editor tab switch, so a ref
  // came back as "not yet fitted" on each remount and the refit discarded the
  // viewport the user had panned to — measured live at 1440px: a 180/90 pan
  // returned as 0/0 after Canvas -> Plot -> Canvas. Keyed by the figures present,
  // so a genuinely different figure is still fitted on arrival.
  const figuresKey = placedFigures.map((figure) => figure.id).join("|");
  useEffect(() => {
    const store = useEditorStore.getState();
    if (store.canvasFitKey === figuresKey) return;
    store.setCanvasFitKey(figuresKey);
    if (placedFigures.length > 0) zoomToFit(CANVAS_W, CANVAS_H);
  }, [figuresKey, placedFigures.length, zoomToFit]);

  // Mousedown on empty canvas → the view pans (useZoomPan reads the same
  // mousedown). Shift+left-drag keeps the marquee for rubber-band selection, and
  // a plain click (no movement) still clears the figure selection the way the
  // marquee's click branch used to.
  const handleCanvasMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 0) return;
      // Only start on the canvas itself, not on child elements
      if (e.target !== e.currentTarget) return;

      if (!e.shiftKey) {
        const startX = e.clientX;
        const startY = e.clientY;
        const handleUp = (ev: MouseEvent) => {
          document.removeEventListener("mouseup", handleUp);
          if (Math.abs(ev.clientX - startX) + Math.abs(ev.clientY - startY) < 4) {
            selectFigure(null);
          }
        };
        document.addEventListener("mouseup", handleUp);
        return;
      }

      const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
      const startX = (e.clientX - rect.left) / zoom;
      const startY = (e.clientY - rect.top) / zoom;

      setMarquee({ x1: startX, y1: startY, x2: startX, y2: startY });

      const handleMove = (ev: MouseEvent) => {
        const curX = (ev.clientX - rect.left) / zoom;
        const curY = (ev.clientY - rect.top) / zoom;
        setMarquee({ x1: startX, y1: startY, x2: curX, y2: curY });
      };

      const handleUp = (ev: MouseEvent) => {
        const endX = (ev.clientX - rect.left) / zoom;
        const endY = (ev.clientY - rect.top) / zoom;
        const selX = Math.min(startX, endX);
        const selY = Math.min(startY, endY);
        const selW = Math.abs(endX - startX);
        const selH = Math.abs(endY - startY);

        if (selW > 5 || selH > 5) {
          // Marquee drag — select intersecting figures
          const state = useEditorStore.getState();
          const ids = state.placedFigures
            .filter((fig) => {
              const fx = fig.x;
              const fy = fig.y;
              const fw = fig.imgSize.width;
              const fh = fig.imgSize.height;
              return (
                fx < selX + selW &&
                fx + fw > selX &&
                fy < selY + selH &&
                fy + fh > selY
              );
            })
            .map((fig) => fig.id);
          if (ids.length > 0) {
            useEditorStore.setState({
              selectedFigureIds: ids,
              selectedFigureId: ids[0],
              selectedElement: null,
              selectedBbox: null,
            });
          } else {
            selectFigure(null);
          }
        } else {
          // Simple click — deselect all
          selectFigure(null);
        }

        setMarquee(null);
        document.removeEventListener("mousemove", handleMove);
        document.removeEventListener("mouseup", handleUp);
      };

      document.addEventListener("mousemove", handleMove);
      document.addEventListener("mouseup", handleUp);
    },
    [zoom, selectFigure],
  );

  // Right-click on canvas → context menu (no figure selected)
  const handleCanvasContextMenu = useCallback(
    (e: React.MouseEvent) => {
      showContextMenu(e, null);
    },
    [showContextMenu],
  );

  // Right-click on figure → context menu with figure ID
  const handleFigureContextMenu = useCallback(
    (e: React.MouseEvent, figureId: string) => {
      showContextMenu(e, figureId);
    },
    [showContextMenu],
  );

  return (
    <div
      className={`canvas-outer${isPanning ? " panning" : ""}`}
      ref={outerRef}
    >
      {/* The entire rulers-area transforms together (vis_app architecture) */}
      <div className="vis-rulers-area" style={transformStyle}>
        {/* Top row: corner-tl | ruler-h | corner-tr */}
        <div
          className="ruler-corner ruler-corner--tl"
          onClick={toggleRulerUnit}
          onMouseDown={handleRulerMouseDown}
          onDoubleClick={handleRulerDoubleClick}
          title={`Units: ${rulerUnit} (click to toggle)`}
        >
          {rulerUnit}
        </div>
        <HorizontalRuler
          canvasWidth={CANVAS_W}
          dpi={DPI}
          gridArea="ruler-h"
          onMouseDown={handleRulerMouseDown}
          onDoubleClick={handleRulerDoubleClick}
        />
        <div
          className="ruler-corner ruler-corner--tr"
          onMouseDown={handleRulerMouseDown}
          onDoubleClick={handleRulerDoubleClick}
        />

        {/* Middle row: ruler-v | canvas | ruler-r */}
        <VerticalRuler
          canvasHeight={CANVAS_H}
          dpi={DPI}
          gridArea="ruler-v"
          onMouseDown={handleRulerMouseDown}
          onDoubleClick={handleRulerDoubleClick}
        />
        <div
          ref={canvasRef}
          className="vis-canvas-container"
          data-canvas-theme={darkMode ? "dark" : "light"}
          style={{ width: CANVAS_W, height: CANVAS_H }}
          onMouseDown={handleCanvasMouseDown}
          onContextMenu={handleCanvasContextMenu}
        >
          {/* Grid first: it is the page ruling, everything else sits on it */}
          <CanvasGrid zoom={zoom} dark={darkMode} />
          {placedFigures.length === 0 ? (
            <div className="canvas-empty">
              <p>{gettext("No figure loaded")}</p>
              <p className="canvas-empty__hint">
                {gettext("Select a file from the browser or create a new figure")}
              </p>
            </div>
          ) : (
            <>
              {placedFigures.map((fig, idx) => (
                <PlacedFigure
                  key={fig.id}
                  figure={fig}
                  zoom={zoom}
                  figureIndex={idx}
                  onContextMenu={handleFigureContextMenu}
                />
              ))}
              <SnapGuides
                guides={activeSnapGuides}
                canvasWidth={CANVAS_W}
                canvasHeight={CANVAS_H}
              />
            </>
          )}
          {marquee && (
            <div
              className="marquee-selection"
              style={{
                left: Math.min(marquee.x1, marquee.x2),
                top: Math.min(marquee.y1, marquee.y2),
                width: Math.abs(marquee.x2 - marquee.x1),
                height: Math.abs(marquee.y2 - marquee.y1),
              }}
            />
          )}
        </div>
        <VerticalRuler
          canvasHeight={CANVAS_H}
          dpi={DPI}
          gridArea="ruler-r"
          onMouseDown={handleRulerMouseDown}
          onDoubleClick={handleRulerDoubleClick}
        />

        {/* Bottom row: corner-bl | ruler-b | corner-br */}
        <div
          className="ruler-corner ruler-corner--bl"
          onMouseDown={handleRulerMouseDown}
          onDoubleClick={handleRulerDoubleClick}
        />
        <HorizontalRuler
          canvasWidth={CANVAS_W}
          dpi={DPI}
          gridArea="ruler-b"
          onMouseDown={handleRulerMouseDown}
          onDoubleClick={handleRulerDoubleClick}
        />
        <div
          className="ruler-corner ruler-corner--br"
          onMouseDown={handleRulerMouseDown}
          onDoubleClick={handleRulerDoubleClick}
        />
      </div>

      {/* Zoom indicator — fixed in outer container */}
      <div className="canvas-zoom-indicator visible">
        {Math.round(zoom * 100)}%
      </div>

      {/* Context menu overlay */}
      {menu.visible && (
        <ContextMenu
          x={menu.x}
          y={menu.y}
          figureId={menu.figureId}
          onClose={hideContextMenu}
        />
      )}
    </div>
  );
}
