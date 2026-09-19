/**
 * Zoom/pan hook — exact port of vis_app ZoomPanManager + RulersManager dragging,
 * extended with the gestures that were missing: left-drag pan on the canvas body
 * and the touch gestures (one finger pans, two fingers pinch/pan).
 *
 * Ctrl+Wheel: zoom to cursor position (vis_app: 0.999 ** deltaY)
 * Left-drag on empty canvas: pan (grab/grabbing cursor) — a drag that starts on
 *   a figure moves the figure instead (useDrag owns it), and Shift+left-drag on
 *   the page keeps the marquee
 * Middle-mouse drag: pan
 * Right-click drag (>3px): pan
 * Ruler drag (left-click on ruler): pan (grab/grabbing cursor)
 * Touch: one finger pans, two fingers pinch-zoom about their centroid
 * Alt modifier: 10% speed pan (vis_app RulersManager)
 * Double-click on ruler: reset pan to origin
 * Double right-click: reset view
 *
 * Initial zoom: 0.22 (vis_app CANVAS_CONSTANTS)
 * Transform: translate(panX, panY) scale(zoom) on .vis-rulers-area
 *
 * The pan/zoom arithmetic itself lives in ./canvasPan (React-free, tested under
 * node --experimental-strip-types); this hook is the DOM glue around it.
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { useEditorStore } from "../../store/useEditorStore";
import {
  MIN_ZOOM,
  applyPan,
  canStartCanvasPan,
  clampZoom,
  panDelta,
  pinchUpdate,
  pointerKindOf,
  sanitizeView,
} from "./canvasPan";
import type { GestureOrigin, PinchStart, Point } from "./canvasPan";

interface ZoomPanState {
  zoom: number;
  panX: number;
  panY: number;
}

const INITIAL_ZOOM = 0.22; // vis_app: canvasZoomLevel = 0.22
const ZOOM_SENSITIVITY = 0.999; // vis_app: 0.999 ** deltaY

/** The view a fresh session opens on: vis_app's initial zoom, no pan. */
const INITIAL_VIEW: ZoomPanState = { zoom: INITIAL_ZOOM, panX: 0, panY: 0 };

/** Which surface a pointerdown landed on.
 *
 * WHY this has to be read from the target: the same canvas hosts figure drags
 * (useDrag), the marquee (React onMouseDown on the page) and the ruler drag (its
 * own React handlers), and stopPropagation() from those handlers cannot reach
 * this element's native listeners — they run earlier, during the native bubble.
 * So the region that was grabbed decides, not the button. */
function gestureOriginOf(target: EventTarget | null): GestureOrigin {
  if (!(target instanceof Element)) return "board";
  // Rulers first: they sit in the same grid as the page but pan by themselves.
  if (target.closest(".ruler")) return "ruler";
  if (target.closest(".placed-figure")) return "figure";
  // The context menu floats over the board and owns its clicks.
  if (target.closest(".context-menu")) return "widget";
  if (target.closest(".vis-canvas-container")) return "page";
  return "board";
}

export function useZoomPan(containerRef: React.RefObject<HTMLElement | null>) {
  // Resume the viewport the session was in. The canvas UNMOUNTS when the editor
  // switches tabs (Canvas / Plot / Details), so component state alone would throw
  // the user's zoom and pan away on every tab change — operator acceptance 7694
  // requires the viewport to survive them.
  const [state, setState] = useState<ZoomPanState>(
    () => useEditorStore.getState().canvasView ?? INITIAL_VIEW,
  );

  const [isPanning, setIsPanning] = useState(false);

  const stateRef = useRef(state);
  stateRef.current = state;

  // Mirror every view change into the session store, so the next mount resumes
  // from here (and a fit/reset is persisted just like a manual pan).
  useEffect(() => {
    useEditorStore.getState().setCanvasView(state);
  }, [state]);

  // Pan tracking refs
  const isPanningRef = useRef(false);
  const panStart = useRef({ x: 0, y: 0 });
  const rightClickStart = useRef<{ x: number; y: number } | null>(null);
  const didDragPan = useRef(false); // Track if right-click resulted in pan drag

  // Touch/pen gesture state. Tracked by pointerId so one finger pans and two
  // pinch; the mouse deliberately does NOT come through here (it keeps the
  // mousemove path below, and handling both would pan twice per frame).
  const activePointers = useRef(new Map<number, Point>());
  const panPointerId = useRef<number | null>(null);
  const pinch = useRef<PinchStart | null>(null);

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
    const newZoom = clampZoom(oldZoom * ZOOM_SENSITIVITY ** zoomDelta.current);

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

  // Mouse down → start pan (left on the empty canvas, middle button, right button)
  const handleMouseDown = useCallback(
    (e: MouseEvent) => {
      // Left mouse button → pan, unless the gesture belongs to a figure or to
      // the marquee (see canStartCanvasPan).
      if (
        e.button === 0 &&
        canStartCanvasPan(gestureOriginOf(e.target), { kind: "mouse", button: 0, shiftKey: e.shiftKey })
      ) {
        e.preventDefault(); // don't start a text selection while dragging
        startPanning(e.clientX, e.clientY);
        return;
      }
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
    // Active panning (left-drag, middle-mouse, right-drag, or ruler drag)
    if (isPanningRef.current) {
      const delta = panDelta(panStart.current, { x: e.clientX, y: e.clientY }, e.altKey);

      // Update start point for next frame (vis_app incremental approach)
      panStart.current = { x: e.clientX, y: e.clientY };

      setState((s) => applyPan(s, delta));
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

  // ── Touch / pen gestures (Pointer Events) ─────────────────────────────
  //
  // One finger pans exactly like a mouse drag (same delta -> same pan, because
  // both go through canvasPan); a second finger turns the gesture into a pinch
  // that zooms about the fingers' centroid and pans with it. touch-action: none
  // on .canvas-outer (canvas.css) is what stops the browser from scrolling the
  // pane out from under us and delivering a pointercancel instead.

  const secondPointerDown = useCallback(() => {
    const points = [...activePointers.current.values()];
    if (points.length < 2) return;
    // Freeze the pinch against the CURRENT view, which may already have been
    // panned by the first finger: pinchUpdate is absolute from here.
    pinch.current = { a: points[0], b: points[1], view: stateRef.current };
    isPanningRef.current = false;
    setIsPanning(false);
  }, []);

  const handlePointerDown = useCallback(
    (e: PointerEvent) => {
      const kind = pointerKindOf(e.pointerType);
      if (kind === "mouse") return; // the mouse keeps its own mousemove path
      if (!canStartCanvasPan(gestureOriginOf(e.target), { kind, button: e.button })) {
        return;
      }
      // Also suppresses the compatibility mouse events, so a touch on the empty
      // canvas cannot fall through to the marquee or to a figure drag.
      e.preventDefault();

      activePointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (activePointers.current.size === 1) {
        panPointerId.current = e.pointerId;
        startPanning(e.clientX, e.clientY);
      } else if (activePointers.current.size === 2) {
        secondPointerDown();
      }
    },
    [secondPointerDown, startPanning],
  );

  const handlePointerMove = useCallback((e: PointerEvent) => {
    if (pointerKindOf(e.pointerType) === "mouse") return;
    if (!activePointers.current.has(e.pointerId)) return;
    activePointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY });

    if (pinch.current && activePointers.current.size >= 2) {
      const points = [...activePointers.current.values()];
      setState(pinchUpdate(pinch.current, points[0], points[1]));
      return;
    }

    if (panPointerId.current === e.pointerId && isPanningRef.current) {
      const delta = panDelta(panStart.current, { x: e.clientX, y: e.clientY });
      panStart.current = { x: e.clientX, y: e.clientY };
      setState((s) => applyPan(s, delta));
    }
  }, []);

  const handlePointerUp = useCallback(
    (e: PointerEvent) => {
      if (pointerKindOf(e.pointerType) === "mouse") return;
      if (!activePointers.current.delete(e.pointerId)) return;

      const remaining = [...activePointers.current.entries()];
      if (remaining.length === 0) {
        panPointerId.current = null;
        pinch.current = null;
        stopPanning();
        return;
      }
      // Pinch → one finger left: re-anchor on the remaining finger, or the view
      // would jump by however far the two fingers had travelled apart.
      panPointerId.current = remaining[0][0];
      pinch.current = null;
      startPanning(remaining[0][1].x, remaining[0][1].y);
    },
    [startPanning, stopPanning],
  );

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    el.addEventListener("wheel", handleWheel, { passive: false });
    el.addEventListener("mousedown", handleMouseDown);
    el.addEventListener("pointerdown", handlePointerDown);
    el.addEventListener("pointermove", handlePointerMove);
    el.addEventListener("pointerup", handlePointerUp);
    el.addEventListener("pointercancel", handlePointerUp);
    el.addEventListener("contextmenu", handleContextMenu);
    el.addEventListener("auxclick", handleDblClick);
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      el.removeEventListener("wheel", handleWheel);
      el.removeEventListener("mousedown", handleMouseDown);
      el.removeEventListener("pointerdown", handlePointerDown);
      el.removeEventListener("pointermove", handlePointerMove);
      el.removeEventListener("pointerup", handlePointerUp);
      el.removeEventListener("pointercancel", handlePointerUp);
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
    handlePointerDown,
    handlePointerMove,
    handlePointerUp,
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
      zoom: clampZoom(s.zoom * 1.2),
    }));
  }, []);

  const zoomOut = useCallback(() => {
    setState((s) => ({
      ...s,
      zoom: clampZoom(s.zoom / 1.2),
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
      const fitZoom = Math.max(Math.min(zoomX, zoomY, 1.0), MIN_ZOOM);
      setState({ zoom: fitZoom, panX: 0, panY: 0 });
    },
    [containerRef],
  );

  const resetView = useCallback(() => {
    setState({ zoom: INITIAL_ZOOM, panX: 0, panY: 0 });
  }, []);

  // Never hand a non-finite transform to the DOM: translate(NaNpx) drops the
  // whole rulers/canvas layer, and the grid ladder would degenerate with it.
  const view = sanitizeView(state);

  return {
    zoom: view.zoom,
    panX: view.panX,
    panY: view.panY,
    isPanning,
    zoomIn,
    zoomOut,
    zoomToFit,
    resetView,
    handleRulerMouseDown,
    handleRulerDoubleClick,
    transformStyle: {
      transform: `translate(${view.panX}px, ${view.panY}px) scale(${view.zoom})`,
      transformOrigin: "0 0",
    } as React.CSSProperties,
  };
}
