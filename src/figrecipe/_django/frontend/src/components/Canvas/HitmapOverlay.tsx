/** Interactive plot hitmap overlay.
 *
 * The backend renders a hitmap PNG (one flat colour per plot element) plus a
 * colorMap of element key to rgb. This overlay samples that PNG under the
 * pointer, resolves the colour to an element key and selects it, so a plot on
 * the canvas can be picked like an object instead of guessed at in the
 * Properties pane.
 *
 * Every decision — which pixel, whether it belongs to an element, what the
 * selection becomes next, where the keyboard reticle is — lives in
 * ./hitmapSelect, which is React-free and covered by
 * tests/hitmapSelect.test.ts. This file only samples pixels and renders.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  gettext,
  interpolate,
} from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";
import { useEditorStore } from "../../store/useEditorStore";
import { showEditorPane } from "../mobilePanes";
import {
  DEFAULT_FOCUS_POINT,
  buildHexToElementKey,
  elementLabel,
  focusPointToPixels,
  hitmapPixelCoords,
  isFocusKey,
  moveFocusPoint,
  resolveElementKey,
  selectionAfterClear,
  selectionAfterHit,
} from "./hitmapSelect";
import type { FocusPoint, Point } from "./hitmapSelect";

interface Props {
  /** Element key resolved from the hitmap; the host figure selects it. */
  onSelect: (elementId: string) => void;
  /** The selection must be dropped (empty background click or Escape). */
  onClear: () => void;
}

export function HitmapOverlay({ onSelect, onClear }: Props) {
  const hitmapImage = useEditorStore((s) => s.hitmapImage);
  const colorMap = useEditorStore((s) => s.colorMap);
  const selectedElement = useEditorStore((s) => s.selectedElement);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  // `ready` mirrors ctxRef but has to be state: a ref alone would not re-render
  // the affordances that depend on the raster being loaded.
  const [ready, setReady] = useState(false);
  const [hoverKey, setHoverKey] = useState<string | null>(null);
  const [focused, setFocused] = useState(false);
  const [focusPoint, setFocusPoint] = useState<FocusPoint>(DEFAULT_FOCUS_POINT);

  // colour -> element key, rebuilt only when the colorMap changes
  const hexToElementKey = useMemo(() => buildHexToElementKey(colorMap), [colorMap]);

  // Draw the hitmap PNG onto a hidden scratch canvas: the only way to read the
  // pixel colours back out of it.
  useEffect(() => {
    setReady(false);
    ctxRef.current = null;
    if (!hitmapImage || !canvasRef.current) return;

    const img = new Image();
    img.onload = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext("2d", { willReadFrequently: true });
      if (!ctx) return;
      ctx.drawImage(img, 0, 0);
      ctxRef.current = ctx;
      setReady(true);
    };
    img.onerror = () => {
      // A broken hitmap must leave the overlay inert, not half-armed.
      ctxRef.current = null;
      setReady(false);
    };
    img.src = `data:image/png;base64,${hitmapImage}`;

    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [hitmapImage]);

  /** Element key under a CSS-px point inside the overlay box (null = background). */
  const keyAtBoxPoint = useCallback(
    (point: Point, box: { width: number; height: number }): string | null => {
      const canvas = canvasRef.current;
      const ctx = ctxRef.current;
      if (!canvas || !ctx) return null;
      const raster = hitmapPixelCoords(
        { width: canvas.width, height: canvas.height },
        point,
        box,
      );
      if (!raster) return null;

      let sample: Uint8ClampedArray | null = null;
      try {
        sample = ctx.getImageData(raster.x, raster.y, 1, 1).data;
      } catch {
        // A resized or tainted raster: "no element here" beats a thrown canvas.
        return null;
      }
      return resolveElementKey({ ready, pixel: sample, hexToKey: hexToElementKey });
    },
    [hexToElementKey, ready],
  );

  const pointInBox = useCallback(
    (event: { clientX: number; clientY: number }, box: DOMRect): Point => ({
      x: event.clientX - box.left,
      y: event.clientY - box.top,
    }),
    [],
  );

  /** Selection transitions in one place, so click, tap and Enter cannot diverge. */
  const applySelection = useCallback(
    (hit: string | null) => {
      const outcome = selectionAfterHit(selectedElement, hit);
      if (outcome.kind === "select") {
        onSelect(outcome.elementId);
        // The property controls follow the selection (operator acceptance 7692:
        // selecting a hit region must "open/synchronize the relevant property
        // controls"). On the phone layout that is the Details tab; on desktop
        // the Details pane is already on screen, so this is a no-op.
        showEditorPane("details");
      } else if (outcome.kind === "clear") onClear();
      // "unchanged" writes nothing — a stray click must not touch the store.
    },
    [onClear, onSelect, selectedElement],
  );

  const handleClick = useCallback(
    (event: React.MouseEvent<HTMLDivElement>) => {
      const box = event.currentTarget.getBoundingClientRect();
      const hit = keyAtBoxPoint(pointInBox(event, box), box);
      if (hit) {
        // Stop the click reaching PlacedFigure: its selectFigure() would wipe
        // the element selection we are making right now.
        event.stopPropagation();
      }
      applySelection(hit);
    },
    [applySelection, keyAtBoxPoint, pointInBox],
  );

  /** A finger tap. Bound to pointerup, not click: with `touch-action` set, a
   *  touch tap is not reliably delivered as a click, and the acceptance requires
   *  selection on touch as well as mouse. The mouse is excluded here so the
   *  click path above stays its single handler (one gesture, one selection). */
  const handlePointerUp = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      if (event.pointerType === "mouse") return;
      const box = event.currentTarget.getBoundingClientRect();
      const hit = keyAtBoxPoint(pointInBox(event, box), box);
      if (hit) event.stopPropagation();
      applySelection(hit);
    },
    [applySelection, keyAtBoxPoint, pointInBox],
  );

  const handlePointerMove = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      if (event.pointerType === "touch") return; // no hover on touch
      const box = event.currentTarget.getBoundingClientRect();
      setHoverKey(keyAtBoxPoint(pointInBox(event, box), box));
    },
    [keyAtBoxPoint, pointInBox],
  );

  // Keyboard path: arrows move the reticle, Enter/Space select what is under it,
  // Escape drops the selection. Tab focus is enough to reach the surface.
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLDivElement>) => {
      if (event.key === "Escape") {
        if (selectionAfterClear(selectedElement).kind === "clear") onClear();
        return;
      }

      const box = event.currentTarget.getBoundingClientRect();
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault(); // Space must not scroll the pane
        applySelection(keyAtBoxPoint(focusPointToPixels(focusPoint, box), box));
        return;
      }

      const key = event.key;
      if (isFocusKey(key)) {
        event.preventDefault();
        const direction = key;
        setFocusPoint((point) => moveFocusPoint(point, direction));
      }
    },
    [applySelection, focusPoint, keyAtBoxPoint, onClear, selectedElement],
  );

  const selectedLabel = elementLabel(colorMap, selectedElement);
  const hoveredLabel = elementLabel(colorMap, hoverKey);
  const title = !ready
    ? gettext("Plot hit regions are not loaded yet")
    : hoverKey
      ? interpolate(gettext("Select %s"), [hoveredLabel])
      : selectedElement
        ? interpolate(gettext("Selected: %s"), [selectedLabel])
        : gettext("Click a plot element to select it; Escape clears the selection");

  return (
    <div
      className={`hitmap-overlay${focused ? " hitmap-overlay--focused" : ""}`}
      style={{ cursor: hoverKey ? "pointer" : "default" }}
      role="button"
      tabIndex={0}
      aria-pressed={selectedElement !== null}
      aria-label={gettext("Plot hit regions")}
      title={title}
      onClick={handleClick}
      onPointerUp={handlePointerUp}
      onPointerMove={handlePointerMove}
      onPointerLeave={() => setHoverKey(null)}
      onFocus={() => setFocused(true)}
      onBlur={() => {
        setFocused(false);
        setHoverKey(null);
      }}
      onKeyDown={handleKeyDown}
    >
      <canvas ref={canvasRef} style={{ display: "none" }} />
      {selectedElement && (
        <span className="hitmap-overlay__selected">
          {interpolate(gettext("Selected: %s"), [selectedLabel])}
        </span>
      )}
      {focused && (
        <span
          className="hitmap-overlay__reticle"
          style={{ left: `${focusPoint.x * 100}%`, top: `${focusPoint.y * 100}%` }}
          aria-hidden="true"
        />
      )}
    </div>
  );
}
