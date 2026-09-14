/** Panel letter badge (A, B, C...) — draggable, editable.
 * Default position: top-left of figure. Drag to reposition.
 * Double-click to edit text. Uses Arial 10pt bold (publication style).
 * Snaps center-to-center with other panel labels (2mm threshold).
 */

import { useCallback, useEffect, useRef, useState } from "react";
import type { SnapGuide } from "../../hooks/useSnap";
import { CANVAS_H, CANVAS_W } from "../../hooks/useSnap";
import { useEditorStore } from "../../store/useEditorStore";
import { getPanelColorByLetter } from "../../utils/panelColors";
import { gettext } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

/** Absolute canvas position of another panel label's center. */
export interface LabelSnapTarget {
  cx: number; // center X in canvas coords
  cy: number; // center Y in canvas coords
}

interface Props {
  letter?: string;
  position?: { x: number; y: number };
  /** Current canvas zoom (to compensate mouse delta). */
  zoom?: number;
  /** Absolute position of this figure on canvas (for snap coord conversion). */
  figureOrigin?: { x: number; y: number };
  /** Other panel labels' absolute centers for snap alignment. */
  snapTargets?: LabelSnapTarget[];
  onChange: (letter: string) => void;
  onMove: (x: number, y: number) => void;
}

const DEFAULT_POS = { x: 8, y: 6 };
/** Snap threshold in pixels (~2mm at 300 DPI). */
const LABEL_SNAP_PX = 2 * (300 / 25.4); // ~24px
/** Approximate label size for center calculation. */
const LABEL_W = 14;
const LABEL_H = 14;

export function PanelLetterOverlay({
  letter,
  position,
  zoom = 1,
  figureOrigin,
  snapTargets,
  onChange,
  onMove,
}: Props) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(letter ?? "");
  const [dragging, setDragging] = useState(false);
  const [snapped, setSnapped] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dragOrigin = useRef<{
    mx: number;
    my: number;
    ox: number;
    oy: number;
  } | null>(null);

  const pos = position ?? DEFAULT_POS;

  useEffect(() => setText(letter ?? ""), [letter]);
  useEffect(() => {
    if (editing) inputRef.current?.select();
  }, [editing]);

  const save = useCallback(() => {
    setEditing(false);
    if (text.trim()) onChange(text.trim());
  }, [text, onChange]);

  // ── Snap helper: snap label position to other labels ────
  const applyLabelSnap = useCallback(
    (
      rawX: number,
      rawY: number,
    ): { x: number; y: number; snapped: boolean; guides: SnapGuide[] } => {
      if (!snapTargets?.length || !figureOrigin) {
        return { x: rawX, y: rawY, snapped: false, guides: [] };
      }
      // This label's center in absolute canvas coords
      const myCx = figureOrigin.x + rawX + LABEL_W / 2;
      const myCy = figureOrigin.y + rawY + LABEL_H / 2;

      let snapX = rawX;
      let snapY = rawY;
      let didSnap = false;
      const guides: SnapGuide[] = [];

      let bestDx = LABEL_SNAP_PX;
      let bestDy = LABEL_SNAP_PX;
      let snapCx = myCx;
      let snapCy = myCy;

      for (const t of snapTargets) {
        // X alignment (vertical guide)
        const dx = Math.abs(myCx - t.cx);
        if (dx < bestDx) {
          bestDx = dx;
          snapX = t.cx - figureOrigin.x - LABEL_W / 2;
          snapCx = t.cx;
          didSnap = true;
        }
        // Y alignment (horizontal guide)
        const dy = Math.abs(myCy - t.cy);
        if (dy < bestDy) {
          bestDy = dy;
          snapY = t.cy - figureOrigin.y - LABEL_H / 2;
          snapCy = t.cy;
          didSnap = true;
        }
      }

      // Build guide lines spanning the canvas
      if (bestDx < LABEL_SNAP_PX) {
        guides.push({
          x1: snapCx,
          y1: 0,
          x2: snapCx,
          y2: CANVAS_H,
          type: "label",
        });
      }
      if (bestDy < LABEL_SNAP_PX) {
        guides.push({
          x1: 0,
          y1: snapCy,
          x2: CANVAS_W,
          y2: snapCy,
          type: "label",
        });
      }

      return { x: snapX, y: snapY, snapped: didSnap, guides };
    },
    [snapTargets, figureOrigin],
  );

  // ── Drag handling ───────────────────────────────────────
  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (editing) return;
      e.stopPropagation();
      e.preventDefault();
      dragOrigin.current = {
        mx: e.clientX,
        my: e.clientY,
        ox: pos.x,
        oy: pos.y,
      };
      setDragging(true);

      const handleMove = (ev: MouseEvent) => {
        if (!dragOrigin.current) return;
        const dx = (ev.clientX - dragOrigin.current.mx) / zoom;
        const dy = (ev.clientY - dragOrigin.current.my) / zoom;
        const rawX = dragOrigin.current.ox + dx;
        const rawY = dragOrigin.current.oy + dy;
        const snap = applyLabelSnap(rawX, rawY);
        setSnapped(snap.snapped);
        useEditorStore.setState({ activeSnapGuides: snap.guides });
        onMove(snap.x, snap.y);
      };

      const handleUp = () => {
        setDragging(false);
        setSnapped(false);
        useEditorStore.setState({ activeSnapGuides: [] });
        dragOrigin.current = null;
        window.removeEventListener("mousemove", handleMove);
        window.removeEventListener("mouseup", handleUp);
      };

      window.addEventListener("mousemove", handleMove);
      window.addEventListener("mouseup", handleUp);
    },
    [editing, pos.x, pos.y, zoom, onMove, applyLabelSnap],
  );

  if (!letter) return null;

  if (editing) {
    return (
      <input
        ref={inputRef}
        className="panel-letter-input"
        style={{ left: pos.x, top: pos.y }}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onBlur={save}
        onKeyDown={(e) => {
          if (e.key === "Enter") save();
          if (e.key === "Escape") {
            setText(letter);
            setEditing(false);
          }
          e.stopPropagation();
        }}
        onClick={(e) => e.stopPropagation()}
        onMouseDown={(e) => e.stopPropagation()}
      />
    );
  }

  const panelColor = getPanelColorByLetter(letter);

  return (
    <span
      className={`panel-letter${dragging ? " dragging" : ""}${snapped ? " snapped" : ""}`}
      style={{
        left: pos.x,
        top: pos.y,
        backgroundColor: panelColor,
        color: "#fff",
        textShadow: "0 1px 2px rgba(0,0,0,0.5)",
      }}
      onMouseDown={handleMouseDown}
      onDoubleClick={(e) => {
        e.stopPropagation();
        setEditing(true);
      }}
      title={gettext("Drag to move, double-click to edit")}
    >
      {letter}
    </span>
  );
}
