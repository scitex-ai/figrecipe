/** Context menu — right-click overlay for canvas figures.
 * Matches vis_app ContextMenuManager actions.
 */

import { useCallback } from "react";
import { api } from "../../api/client";
import { useEditorStore } from "../../store/useEditorStore";
import { gettext, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

interface Props {
  x: number;
  y: number;
  figureId: string | null;
  onClose: () => void;
}

export function ContextMenu({ x, y, figureId, onClose }: Props) {
  const {
    placedFigures,
    removeFigure,
    copyFigure,
    pasteFigure,
    bringToFront,
    sendToBack,
    alignFigures,
    groupFigures,
    ungroupFigures,
    showToast,
  } = useEditorStore();

  const figure = placedFigures.find((f) => f.id === figureId);
  const hasFigure = !!figure;
  const hasMultiple = placedFigures.length >= 2;

  // ── Actions ────────────────────────────────────────────────

  const handleDelete = useCallback(() => {
    if (figureId) removeFigure(figureId);
    onClose();
  }, [figureId, removeFigure, onClose]);

  const handleCopy = useCallback(() => {
    if (figureId) {
      useEditorStore.getState().selectFigure(figureId);
      copyFigure();
    }
    onClose();
  }, [figureId, copyFigure, onClose]);

  const handlePaste = useCallback(() => {
    pasteFigure();
    onClose();
  }, [pasteFigure, onClose]);

  const handleDuplicate = useCallback(() => {
    if (figureId) {
      useEditorStore.getState().selectFigure(figureId);
      copyFigure();
      pasteFigure();
    }
    onClose();
  }, [figureId, copyFigure, pasteFigure, onClose]);

  const handleBringToFront = useCallback(() => {
    if (figureId) bringToFront(figureId);
    onClose();
  }, [figureId, bringToFront, onClose]);

  const handleSendToBack = useCallback(() => {
    if (figureId) sendToBack(figureId);
    onClose();
  }, [figureId, sendToBack, onClose]);

  const handleGroup = useCallback(() => {
    const ids = placedFigures.map((f) => f.id);
    if (ids.length >= 2) groupFigures(ids);
    onClose();
  }, [placedFigures, groupFigures, onClose]);

  const handleUngroup = useCallback(() => {
    if (figure?.groupId) ungroupFigures(figure.groupId);
    onClose();
  }, [figure, ungroupFigures, onClose]);

  const handleExport = useCallback(
    async (fmt: string) => {
      onClose();
      try {
        const blob = await api.getBlob(`download/${fmt}`);
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `figure.${fmt}`;
        a.click();
        URL.revokeObjectURL(url);
      } catch (e) {
        showToast(interpolate(gettext("Export failed: %s"), [e]), "error");
      }
    },
    [showToast, onClose],
  );

  const handleAlign = useCallback(
    (mode: Parameters<typeof alignFigures>[0]) => {
      alignFigures(mode);
      onClose();
    },
    [alignFigures, onClose],
  );

  // ── Render ─────────────────────────────────────────────────

  return (
    <div
      className="context-menu"
      style={{ left: x, top: y }}
      onMouseDown={(e) => e.stopPropagation()}
    >
      {/* Clipboard */}
      <Item
        icon="fas fa-copy"
        label={gettext("Copy")}
        shortcut="Ctrl+C"
        disabled={!hasFigure}
        onClick={handleCopy}
      />
      <Item
        icon="fas fa-paste"
        label={gettext("Paste")}
        shortcut="Ctrl+V"
        onClick={handlePaste}
      />
      <Item
        icon="fas fa-trash-alt"
        label={gettext("Delete")}
        shortcut="Del"
        disabled={!hasFigure}
        onClick={handleDelete}
      />
      <Item
        icon="fas fa-clone"
        label={gettext("Duplicate")}
        shortcut="Ctrl+D"
        disabled={!hasFigure}
        onClick={handleDuplicate}
      />

      <div className="context-menu-divider" />

      {/* Layer ordering */}
      <Item
        icon="fas fa-layer-group"
        label={gettext("Bring to Front")}
        disabled={!hasFigure}
        onClick={handleBringToFront}
      />
      <Item
        icon="fas fa-layer-group"
        label={gettext("Send to Back")}
        disabled={!hasFigure}
        onClick={handleSendToBack}
      />

      <div className="context-menu-divider" />

      {/* Alignment */}
      <div className="context-menu-label">{gettext("Align")}</div>
      <Item
        icon="fas fa-align-left"
        label={gettext("Align Left")}
        disabled={!hasMultiple}
        onClick={() => handleAlign("left")}
      />
      <Item
        icon="fas fa-align-right"
        label={gettext("Align Right")}
        disabled={!hasMultiple}
        onClick={() => handleAlign("right")}
      />
      <Item
        icon="fas fa-arrow-up"
        label={gettext("Align Top")}
        disabled={!hasMultiple}
        onClick={() => handleAlign("top")}
      />
      <Item
        icon="fas fa-arrow-down"
        label={gettext("Align Bottom")}
        disabled={!hasMultiple}
        onClick={() => handleAlign("bottom")}
      />

      <div className="context-menu-divider" />

      {/* Group */}
      <Item
        icon="fas fa-object-group"
        label={gettext("Group All")}
        disabled={!hasMultiple}
        onClick={handleGroup}
      />
      <Item
        icon="fas fa-object-ungroup"
        label={gettext("Ungroup")}
        disabled={!figure?.groupId}
        onClick={handleUngroup}
      />

      <div className="context-menu-divider" />

      {/* Export */}
      <div className="context-menu-label">{gettext("Export")}</div>
      <Item
        icon="fas fa-file-image"
        label={gettext("Export PNG")}
        onClick={() => handleExport("png")}
      />
      <Item
        icon="fas fa-file-code"
        label={gettext("Export SVG")}
        onClick={() => handleExport("svg")}
      />
      <Item
        icon="fas fa-file-pdf"
        label={gettext("Export PDF")}
        onClick={() => handleExport("pdf")}
      />
    </div>
  );
}

/* ── Menu item helper ─────────────────────────────────────── */

function Item({
  icon,
  label,
  shortcut,
  disabled,
  onClick,
}: {
  icon: string;
  label: string;
  shortcut?: string;
  disabled?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      className="context-menu-item"
      disabled={disabled}
      onClick={onClick}
      type="button"
    >
      <i className={icon} />
      {label}
      {shortcut && <span className="context-menu-shortcut">{shortcut}</span>}
    </button>
  );
}
