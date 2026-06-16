/** Renders one figure on the canvas at its (x, y) position.
 * Wraps image + bbox overlay in a correctly-sized container
 * so bbox coordinates map 1:1 to the image pixels.
 * Integrates snap engine for axes/edge/center alignment.
 */

import { useCallback } from "react";
import { useDrag } from "../../hooks/useDrag";
import {
  CANVAS_H,
  CANVAS_W,
  applySnapping,
  getPanelBboxes,
} from "../../hooks/useSnap";
import type { SnapGuide } from "../../hooks/useSnap";
import { useEditorStore } from "../../store/useEditorStore";
import type { PlacedFigure as PlacedFigureType } from "../../types/editor";
import { getPanelColorByLetter } from "../../utils/panelColors";
import { BboxOverlay } from "./BboxOverlay";
import { LegendDragOverlay } from "./LegendDragOverlay";
import { CaptionOverlay } from "./CaptionOverlay";
import { PanelLetterOverlay } from "./PanelLetterOverlay";
import type { LabelSnapTarget } from "./PanelLetterOverlay";

interface Props {
  figure: PlacedFigureType;
  zoom: number;
  figureIndex: number;
  onContextMenu?: (e: React.MouseEvent, figureId: string) => void;
}

export function PlacedFigure({
  figure,
  zoom,
  figureIndex,
  onContextMenu,
}: Props) {
  const {
    selectedFigureId,
    selectedFigureIds,
    selectedElement,
    selectFigure,
    toggleFigureSelection,
    selectElement,
    showHitmap,
    moveFigure,
    moveLegend,
    snapEnabled,
  } = useEditorStore();
  const isSelected = selectedFigureId === figure.id;
  const isMultiSelected =
    selectedFigureIds.length > 1 && selectedFigureIds.includes(figure.id);

  // ── Drag-to-move ──────────────────────────────────────────
  const handleDragEnd = useCallback(
    (x: number, y: number) => moveFigure(figure.id, x, y),
    [figure.id, moveFigure],
  );

  // ── Snap function (reads latest store state) ──────────────
  const snapFn = useCallback(
    (
      rawX: number,
      rawY: number,
    ): { x: number; y: number; guides: SnapGuide[] } => {
      const state = useEditorStore.getState();
      if (!state.snapEnabled) {
        return { x: rawX, y: rawY, guides: [] };
      }
      const otherFigures = state.placedFigures.filter(
        (f) => f.id !== figure.id,
      );
      // Collect group sibling IDs to exclude from snap targets
      const excludeIds = figure.groupId
        ? state.placedFigures
            .filter((f) => f.groupId === figure.groupId && f.id !== figure.id)
            .map((f) => f.id)
        : undefined;
      const panelBboxes = getPanelBboxes(figure);
      return applySnapping(
        rawX,
        rawY,
        figure.imgSize.width,
        figure.imgSize.height,
        panelBboxes,
        otherFigures,
        CANVAS_W,
        CANVAS_H,
        excludeIds,
      );
    },
    [figure.id, figure.imgSize.width, figure.imgSize.height, figure.bboxes],
  );

  // ── Snap guides callback ──────────────────────────────────
  const handleSnapGuides = useCallback((guides: SnapGuide[]) => {
    useEditorStore.setState({ activeSnapGuides: guides });
  }, []);

  const { isDragging, dragOffset, onMouseDown } = useDrag(
    handleDragEnd,
    { x: figure.x, y: figure.y },
    {
      zoom,
      onDragStart: () => selectFigure(figure.id),
      snapFn: snapEnabled ? snapFn : undefined,
      onSnapGuidesChange: handleSnapGuides,
    },
  );

  // ── Click handlers ────────────────────────────────────────
  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      if (isDragging) return;
      if (e.ctrlKey || e.metaKey) {
        toggleFigureSelection(figure.id);
      } else {
        selectFigure(figure.id);
      }
    },
    [figure.id, selectFigure, toggleFigureSelection, isDragging],
  );

  const handleLetterChange = useCallback(
    (letter: string) => {
      useEditorStore.setState((s) => ({
        placedFigures: s.placedFigures.map((f) =>
          f.id === figure.id ? { ...f, panelLetter: letter } : f,
        ),
      }));
    },
    [figure.id],
  );

  const handleLetterMove = useCallback(
    (x: number, y: number) => {
      useEditorStore.setState((s) => ({
        placedFigures: s.placedFigures.map((f) =>
          f.id === figure.id ? { ...f, panelLetterPos: { x, y } } : f,
        ),
      }));
    },
    [figure.id],
  );

  // ── Label snap targets (other figures' label centers) ────
  const labelSnapTargets: LabelSnapTarget[] = useEditorStore((s) =>
    s.placedFigures
      .filter((f) => f.id !== figure.id && f.panelLetter)
      .map((f) => {
        const lp = f.panelLetterPos ?? { x: 8, y: 6 };
        return { cx: f.x + lp.x + 7, cy: f.y + lp.y + 7 };
      }),
  );

  const handleElementClick = useCallback(
    (elementId: string) => {
      const bbox =
        figure.bboxes[elementId] ??
        Object.values(figure.bboxes).find(
          (b) => b.label === elementId || b.call_id === elementId,
        );
      selectElement(elementId, bbox, figure.id);
    },
    [figure.id, figure.bboxes, selectElement],
  );

  // Legend drag → axes-fraction anchor → moveLegend.
  // The legend bbox carries ax_index; its parent axes bbox is "ax{N}_axes".
  // Convert the dropped top-left (image px) to axes fraction (y is bottom-up).
  const handleLegendDrop = useCallback(
    (axIndex: number, imgX: number, imgY: number) => {
      const axBox = figure.bboxes[`ax${axIndex}_axes`];
      if (!axBox || !axBox.width || !axBox.height) return;
      const x = (imgX - axBox.x) / axBox.width;
      const y = 1 - (imgY - axBox.y) / axBox.height;
      selectFigure(figure.id);
      void moveLegend(axIndex, x, y);
    },
    [figure.id, figure.bboxes, moveLegend, selectFigure],
  );

  // Legend elements (draggable). Each carries its ax_index.
  const legendBboxes = Object.entries(figure.bboxes).filter(
    ([key, b]) => b.type === "legend" && key !== "_meta",
  );

  // Visual position during drag
  const displayX = isDragging ? figure.x + dragOffset.dx : figure.x;
  const displayY = isDragging ? figure.y + dragOffset.dy : figure.y;

  const panelColor = getPanelColorByLetter(figure.panelLetter ?? "");

  return (
    <div
      className={`placed-figure${isSelected ? " selected" : ""}${isMultiSelected ? " multi-selected" : ""}${isDragging ? " dragging" : ""}${figure.groupId ? " grouped" : ""}`}
      style={
        {
          position: "absolute",
          left: displayX,
          top: displayY,
          width: figure.imgSize.width,
          "--panel-color": panelColor,
        } as React.CSSProperties
      }
      onClick={handleClick}
      onMouseDown={onMouseDown}
      onContextMenu={(e) => {
        e.stopPropagation();
        onContextMenu?.(e, figure.id);
      }}
    >
      <div
        style={{
          position: "relative",
          width: figure.imgSize.width,
          height: figure.imgSize.height,
        }}
      >
        <img
          className="canvas-image"
          src={`data:image/png;base64,${figure.previewImage}`}
          alt={figure.path}
          draggable={false}
          width={figure.imgSize.width}
          height={figure.imgSize.height}
        />
        <BboxOverlay
          bboxes={figure.bboxes}
          onElementClick={handleElementClick}
          imgWidth={figure.imgSize.width}
          imgHeight={figure.imgSize.height}
          alwaysVisible={showHitmap}
          selectedElement={isSelected ? selectedElement : null}
        />
        <PanelLetterOverlay
          letter={figure.panelLetter}
          position={figure.panelLetterPos}
          zoom={zoom}
          figureOrigin={{ x: displayX, y: displayY }}
          snapTargets={labelSnapTargets}
          onChange={handleLetterChange}
          onMove={handleLetterMove}
        />
        {legendBboxes.map(([key, b]) => (
          <LegendDragOverlay
            key={key}
            bbox={{ x: b.x, y: b.y, width: b.width, height: b.height }}
            zoom={zoom}
            onDragEnd={(imgX, imgY) =>
              handleLegendDrop(
                (b as { ax_index?: number }).ax_index ?? 0,
                imgX,
                imgY,
              )
            }
          />
        ))}
      </div>
      <CaptionOverlay
        figureId={figure.id}
        figureIndex={figureIndex}
        width={figure.imgSize.width}
      />
    </div>
  );
}
