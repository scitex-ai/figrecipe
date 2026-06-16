/**
 * Zoom/pan hook — exact port of vis_app ZoomPanManager + RulersManager dragging.
 *
 * Ctrl+Wheel: zoom to cursor position (vis_app: 0.999 ** deltaY)
 * Middle-mouse drag: pan
 * Right-click drag (>3px): pan
 * Ruler drag (left-click on ruler): pan (grab/grabbing cursor)
 * Alt modifier: 10% speed pan (vis_app RulersManager)
 * Double-click on ruler: reset pan to origin
 * Double right-click: reset view
 *
 * Initial zoom: 0.22 (vis_app CANVAS_CONSTANTS)
 * Transform: translate(panX, panY) scale(zoom) on .vis-rulers-area
 */

import { useCallback, useEffect, useRef, useState } from "react";

interface ZoomPanState {
  zoom: number;
  panX: number;
  panY: number;
}

const INITIAL_ZOOM = 0.22; // vis_app: canvasZoomLevel = 0.22
const MIN_ZOOM = 0.1;
const MAX_ZOOM = 5.0;
const ZOOM_SENSITIVITY = 0.999; // vis_app: 0.999 ** deltaY

export function useZoomPan(containerRef: React.RefObject<HTMLElement | null>) {
  const [state, setState] = useState<ZoomPanState>({
    zoom: INITIAL_ZOOM,
    panX: 0,
    panY: 0,
  });

  const [isPanning, setIsPanning] = useState(false);

  const stateRef = useRef(state);
  stateRef.current = state;

  // Pan tracking refs
  const isPanningRef = useRef(false);
  const panStart = useRef({ x: 0, y: 0 });
  const rightClickStart = useRef<{ x: number; y: number } | null>(null);
  const didDragPan = useRef(false); // Track if right-click resulted in pan drag

  // Zoom accumulator for rAF throttling
  const zoomDelta = useRef(0);
  const zoomMousePos = useRef({ x: 0, y: 0 });
  const rafId = useRef(0);

  const startPanning = useCallback((clientX: number, clientY: number) => {
    isPanningRef.current = true;
    setIsPanning(true);
    panStart.current = { x: clientX, y: clientY };
  }, []);

  const stopPanning = useCallback(() => {
    isPanningRef.current = false;
    setIsPanning(false);
    rightClickStart.current = null;
  }, []);

  const applyZoom = useCallback(() => {
    if (zoomDelta.current === 0) return;

    const s = stateRef.current;
    const oldZoom = s.zoom;
    let newZoom = oldZoom * ZOOM_SENSITIVITY ** zoomDelta.current;
    newZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, newZoom));

    const ratio = newZoom / oldZoom;
    const mx = zoomMousePos.current.x;
    const my = zoomMousePos.current.y;

    setState({
      zoom: newZoom,
      panX: mx - (mx - s.panX) * ratio,
      panY: my - (my - s.panY) * ratio,
    });

    zoomDelta.current = 0;
  }, []);

  // Wheel: Ctrl = zoom, plain = pan vertically, Shift = pan horizontally
  const handleWheel = useCallback(
    (e: WheelEvent) => {
      e.preventDefault();

      // Ctrl+Wheel → zoom to cursor
      if (e.ctrlKey || e.metaKey) {
        const container = containerRef.current;
        if (!container) return;

        const rect = container.getBoundingClientRect();
        zoomMousePos.current = {
          x: e.clientX - rect.left,
          y: e.clientY - rect.top,
        };
        zoomDelta.current += e.deltaY;

        cancelAnimationFrame(rafId.current);
        rafId.current = requestAnimationFrame(applyZoom);
        return;
      }

      // Plain wheel → pan (Shift swaps axes for horizontal scroll)
      const dx = e.shiftKey ? -e.deltaY : -e.deltaX;
      const dy = e.shiftKey ? 0 : -e.deltaY;
      setState((s) => ({ ...s, panX: s.panX + dx, panY: s.panY + dy }));
    },
    [containerRef, applyZoom],
  );

  // Mouse down → start pan (middle button or right button)
  const handleMouseDown = useCallback(
    (e: MouseEvent) => {
      // Middle mouse button
      if (e.button === 1) {
        e.preventDefault();
        startPanning(e.clientX, e.clientY);
      }
      // Right mouse button — track start for drag detection
      if (e.button === 2) {
        rightClickStart.current = { x: e.clientX, y: e.clientY };
      }
    },
    [startPanning],
  );

  // vis_app incremental pan: delta each frame, Alt = 10% speed
  const handleMouseMove = useCallback((e: MouseEvent) => {
    // Active panning (middle-mouse, right-drag, or ruler drag)
    if (isPanningRef.current) {
      let deltaX = e.clientX - panStart.current.x;
      let deltaY = e.clientY - panStart.current.y;

      if (e.altKey) {
        deltaX *= 0.1;
        deltaY *= 0.1;
      }

      // Update start point for next frame (vis_app incremental approach)
      panStart.current = { x: e.clientX, y: e.clientY };

      setState((s) => ({
        ...s,
        panX: s.panX + deltaX,
        panY: s.panY + deltaY,
      }));
      return;
    }

    // Right-click drag pan (threshold: 3px)
    if (rightClickStart.current && e.buttons === 2) {
      const dx = e.clientX - rightClickStart.current.x;
      const dy = e.clientY - rightClickStart.current.y;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
        isPanningRef.current = true;
        didDragPan.current = true;
        setIsPanning(true);
        panStart.current = { ...rightClickStart.current };
        rightClickStart.current = null;
      }
    }
  }, []);

  const handleMouseUp = useCallback(() => {
    stopPanning();
  }, [stopPanning]);

  // Prevent context menu
  const handleContextMenu = useCallback((e: MouseEvent) => {
    e.preventDefault();
  }, []);

  // Right-click (no drag) → reset pan to origin, keep zoom unchanged
  const handleDblClick = useCallback((e: MouseEvent) => {
    if (e.button === 2) {
      // Skip if this was a drag-pan release
      if (didDragPan.current) {
        didDragPan.current = false;
        return;
      }
      setState((s) => ({ ...s, panX: 0, panY: 0 }));
    }
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    el.addEventListener("wheel", handleWheel, { passive: false });
    el.addEventListener("mousedown", handleMouseDown);
    el.addEventListener("contextmenu", handleContextMenu);
    el.addEventListener("auxclick", handleDblClick);
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      el.removeEventListener("wheel", handleWheel);
      el.removeEventListener("mousedown", handleMouseDown);
      el.removeEventListener("contextmenu", handleContextMenu);
      el.removeEventListener("auxclick", handleDblClick);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
      cancelAnimationFrame(rafId.current);
    };
  }, [
    containerRef,
    handleWheel,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    handleContextMenu,
    handleDblClick,
  ]);

  // ── Ruler drag-to-pan (vis_app RulersManager.setupRulerDragging) ──

  const handleRulerMouseDown = useCallback(
    (e: React.MouseEvent) => {
      // Left button only
      if (e.button !== 0) return;
      e.preventDefault();
      startPanning(e.clientX, e.clientY);
    },
    [startPanning],
  );

  // Double-click on ruler → re-align the canvas to the top-left origin while
  // KEEPING the current zoom level (it used to also zoom-to-fit, which was a
  // surprising reset; double-click is "scroll back to origin", not "zoom").
  const handleRulerDoubleClick = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setState((s) => ({ ...s, panX: 0, panY: 0 }));
  }, []);

  // ── Programmatic controls ──────────────────────────────

  const zoomIn = useCallback(() => {
    setState((s) => ({
      ...s,
      zoom: Math.min(MAX_ZOOM, s.zoom * 1.2),
    }));
  }, []);

  const zoomOut = useCallback(() => {
    setState((s) => ({
      ...s,
      zoom: Math.max(MIN_ZOOM, s.zoom / 1.2),
    }));
  }, []);

  // vis_app ZoomPanManager.zoomToFit(): container - 40px buffer, min(zoomX, zoomY, 1.0), clamp 0.1-1.0
  const zoomToFit = useCallback(
    (contentWidth?: number, contentHeight?: number) => {
      const container = containerRef.current;
      if (!container) return;
      const containerWidth = container.clientWidth - 40;
      const containerHeight = container.clientHeight - 40;
      const cw = contentWidth ?? 2126;
      const ch = contentHeight ?? 2953;
      const zoomX = containerWidth / cw;
      const zoomY = containerHeight / ch;
      const fitZoom = Math.max(Math.min(zoomX, zoomY, 1.0), 0.1);
      setState({ zoom: fitZoom, panX: 0, panY: 0 });
    },
    [containerRef],
  );

  const resetView = useCallback(() => {
    setState({ zoom: INITIAL_ZOOM, panX: 0, panY: 0 });
  }, []);

  return {
    zoom: state.zoom,
    panX: state.panX,
    panY: state.panY,
    isPanning,
    zoomIn,
    zoomOut,
    zoomToFit,
    resetView,
    handleRulerMouseDown,
    handleRulerDoubleClick,
    transformStyle: {
      transform: `translate(${state.panX}px, ${state.panY}px) scale(${state.zoom})`,
      transformOrigin: "0 0",
    } as React.CSSProperties,
  };
}
