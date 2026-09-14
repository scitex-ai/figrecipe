/** Center pane — Canvas with figure dropdown and toolbar.
 * Gallery categories moved to PlotTypeNav sidebar.
 */

import { useState } from "react";
import { redo, undo } from "../../hooks/useUndoRedo";
import { useEditorStore } from "../../store/useEditorStore";
import { Canvas } from "../Canvas/Canvas";
import { ExportDialog } from "../ExportDialog/ExportDialog";
import { gettext, ngettext, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

export function CanvasPane() {
  const {
    placedFigures,
    selectedFigureId,
    save,
    restore,
    darkMode,
    setDarkMode,
    snapEnabled,
    showRulers,
    toggleSnap,
    toggleRulers,
    zoomControls,
    showHitmap,
    toggleHitmap,
  } = useEditorStore();
  const [exportOpen, setExportOpen] = useState(false);

  // Figure label: selected figure name or count. When the canvas holds no
  // figures the label used to be the bare token "No figures" with no
  // explanation — say what it means and how to get out of it.
  const selectedFig = placedFigures.find((f) => f.id === selectedFigureId);
  const figLabel = selectedFig
    ? (selectedFig.path.split("/").pop() ?? gettext("figure"))
    : placedFigures.length > 0
      ? interpolate(ngettext("%s figure", "%s figures", placedFigures.length), [placedFigures.length])
      : gettext("No figures yet");
  const figLabelTitle =
    placedFigures.length === 0
      ? gettext("No figures are on the canvas yet. Add one from the plot-type gallery or open a recipe from the file tree.")
      : undefined;

  return (
    <>
      {/* Pane header with figure dropdown + toolbar actions */}
      <div className="pane-header">
        {/* Figure dropdown */}
        <div className="figure-dropdown-container">
          <button
            className="figure-dropdown-toggle"
            type="button"
            title={figLabelTitle}
          >
            <i className="fas fa-paint-brush" />
            <span className="figure-dropdown-label">{figLabel}</span>
            <i className="fas fa-chevron-down" />
          </button>
        </div>

        {/* Toolbar actions (right-aligned) */}
        <div className="pane-header-buttons pane-header-right">
          {/* Undo / Redo */}
          <button
            className="pane-header-btn"
            type="button"
            title={gettext("Undo (Ctrl+Z)")}
            onClick={undo}
          >
            <i className="fas fa-undo" />
          </button>
          <button
            className="pane-header-btn"
            type="button"
            title={gettext("Redo (Ctrl+Shift+Z)")}
            onClick={redo}
          >
            <i className="fas fa-redo" />
          </button>

          <span className="toolbar-sep" />

          {/* Snap / Rulers */}
          <button
            className={`pane-header-btn${snapEnabled ? " pane-header-btn--active" : ""}`}
            type="button"
            title={snapEnabled ? gettext("Snap: ON") : gettext("Snap: OFF")}
            onClick={toggleSnap}
          >
            <i className="fas fa-magnet" />
          </button>
          <button
            className={`pane-header-btn${showRulers ? " pane-header-btn--active" : ""}`}
            type="button"
            title={gettext("Toggle rulers")}
            onClick={toggleRulers}
          >
            <i className="fas fa-ruler-combined" />
          </button>

          <span className="toolbar-sep" />

          {/* Zoom */}
          <button
            className="pane-header-btn"
            type="button"
            title={gettext("Zoom to fit")}
            onClick={zoomControls?.zoomToFit}
          >
            <i className="fas fa-compress-arrows-alt" />
          </button>

          {/* Hitmap */}
          <button
            className={`pane-header-btn${showHitmap ? " pane-header-btn--active" : ""}`}
            type="button"
            title={gettext("Toggle hit regions (debug)")}
            onClick={toggleHitmap}
          >
            <i className="fas fa-bullseye" />
          </button>

          <span className="toolbar-sep" />

          {/* Save / Restore / Export */}
          <button
            className="pane-header-btn"
            type="button"
            title={gettext("Save (Ctrl+S)")}
            onClick={save}
          >
            <i className="fas fa-save" />
          </button>
          <button
            className="pane-header-btn"
            type="button"
            title={gettext("Restore original")}
            onClick={restore}
          >
            <i className="fas fa-undo-alt" />
          </button>
          <button
            className="pane-header-btn"
            type="button"
            title={gettext("Export (PNG/SVG/PDF)")}
            onClick={() => setExportOpen(true)}
          >
            <i className="fas fa-download" />
          </button>

          <span className="toolbar-sep" />

          {/* Theme toggle */}
          <button
            className="pane-header-btn"
            type="button"
            title={darkMode ? gettext("Switch to light mode") : gettext("Switch to dark mode")}
            onClick={() => setDarkMode(!darkMode)}
          >
            <i className={darkMode ? "fas fa-moon" : "fas fa-sun"} />
          </button>
        </div>
      </div>

      {/* Canvas content */}
      <div className="pane-content canvas-content">
        <Canvas />
      </div>

      {/* Export dialog */}
      {exportOpen && <ExportDialog onClose={() => setExportOpen(false)} />}
    </>
  );
}
