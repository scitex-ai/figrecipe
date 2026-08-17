/** FigureViewer — displays the rendered figure image with zoom/pan.
 *
 * Used in the Plot tab to show the matplotlib figure preview.
 * The Canvas tab uses CanvasPane instead (for composition layout).
 */

import { useRef, useState, useCallback } from "react";
import { useEditorStore } from "../../store/useEditorStore";
import { GalleryStart } from "../Gallery/GalleryStart";

export function FigureViewer() {
  const { placedFigures, selectedFigureId, loading } = useEditorStore();
  const [scale, setScale] = useState(1);
  const [translate, setTranslate] = useState({ x: 0, y: 0 });
  const dragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });

  // Show selected figure or first figure
  const figure =
    placedFigures.find((f) => f.id === selectedFigureId) ||
    placedFigures[0] ||
    null;
  const previewImage = figure?.previewImage;

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setScale((s) => Math.max(0.1, Math.min(10, s * delta)));
  }, []);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      dragging.current = true;
      dragStart.current = {
        x: e.clientX - translate.x,
        y: e.clientY - translate.y,
      };
    },
    [translate],
  );

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragging.current) return;
    setTranslate({
      x: e.clientX - dragStart.current.x,
      y: e.clientY - dragStart.current.y,
    });
  }, []);

  const handleMouseUp = useCallback(() => {
    dragging.current = false;
  }, []);

  const handleDoubleClick = useCallback(() => {
    setScale(1);
    setTranslate({ x: 0, y: 0 });
  }, []);

  // Nothing open yet. Showing the shipped examples here rather than an
  // instruction ("Select a recipe file...") matters because a NEW project has
  // no recipe file to select — the instruction named something the visitor did
  // not have, so the first screen of the tool showed neither a figure nor a
  // way to get one.
  if (!previewImage && !loading) {
    return (
      <div className="figure-viewer figure-viewer--start">
        <GalleryStart />
      </div>
    );
  }

  return (
    <div
      className="figure-viewer"
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onDoubleClick={handleDoubleClick}
      style={{ cursor: dragging.current ? "grabbing" : "grab" }}
    >
      {previewImage && (
        <img
          src={`data:image/png;base64,${previewImage}`}
          alt="Figure preview"
          draggable={false}
          style={{
            transform: `translate(${translate.x}px, ${translate.y}px) scale(${scale})`,
            transformOrigin: "center center",
            maxWidth: "100%",
            maxHeight: "100%",
            userSelect: "none",
          }}
        />
      )}
    </div>
  );
}
