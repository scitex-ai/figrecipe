/** Ribbon toolbar — tabbed groups matching vis_app ribbon pattern.
 * Tabs: Home, Layout, Style, View.
 * Each tab shows a panel of grouped buttons.
 */

import { useState } from "react";
import { redo, undo } from "../../hooks/useUndoRedo";
import { useEditorStore } from "../../store/useEditorStore";
import { ExportDialog } from "../ExportDialog/ExportDialog";
import { RibbonButton } from "./RibbonButton";
import { RibbonGroup } from "./RibbonGroup";
import { gettext, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

type TabId = "home" | "layout" | "style" | "view";

export function Ribbon() {
  const [activeTab, setActiveTab] = useState<TabId>("home");

  return (
    <div className="ribbon">
      {/* Tab buttons */}
      <div className="ribbon-tabs">
        <Tab
          id="home"
          icon="fas fa-home"
          label={gettext("Home")}
          active={activeTab}
          onClick={setActiveTab}
        />
        <Tab
          id="layout"
          icon="fas fa-th-large"
          label={gettext("Layout")}
          active={activeTab}
          onClick={setActiveTab}
        />
        <Tab
          id="style"
          icon="fas fa-palette"
          label={gettext("Style")}
          active={activeTab}
          onClick={setActiveTab}
        />
        <Tab
          id="view"
          icon="fas fa-eye"
          label={gettext("View")}
          active={activeTab}
          onClick={setActiveTab}
        />
      </div>

      {/* Tab content panels */}
      <div className="ribbon-content">
        <HomePanel active={activeTab === "home"} />
        <LayoutPanel active={activeTab === "layout"} />
        <StylePanel active={activeTab === "style"} />
        <ViewPanel active={activeTab === "view"} />
      </div>
    </div>
  );
}

/* ── Tab button ───────────────────────────────────────────── */

function Tab({
  id,
  icon,
  label,
  active,
  onClick,
}: {
  id: TabId;
  icon: string;
  label: string;
  active: TabId;
  onClick: (id: TabId) => void;
}) {
  return (
    <button
      className={`ribbon-tab${active === id ? " active" : ""}`}
      onClick={() => onClick(id)}
      type="button"
    >
      <i className={icon} />
      {label}
    </button>
  );
}

/* ── Home Panel ───────────────────────────────────────────── */

function HomePanel({ active }: { active: boolean }) {
  const {
    save,
    restore,
    selectedFigureId,
    copyFigure,
    pasteFigure,
    removeFigure,
    clipboard,
  } = useEditorStore();
  const [exportOpen, setExportOpen] = useState(false);

  return (
    <div className={`ribbon-panel${active ? " active" : ""}`}>
      <RibbonGroup label={gettext("File")}>
        <RibbonButton
          icon="fas fa-save"
          label={gettext("Save")}
          onClick={save}
          title={gettext("Compose canvas figures and save (Ctrl+S)")}
        />
        <RibbonButton
          icon="fas fa-undo"
          label={gettext("Restore")}
          onClick={restore}
          title={gettext("Restore original")}
        />
        <RibbonButton
          icon="fas fa-download"
          label={gettext("Export")}
          onClick={() => setExportOpen(true)}
          title={gettext("Compose and export as PNG/SVG/PDF")}
        />
        {exportOpen && <ExportDialog onClose={() => setExportOpen(false)} />}
      </RibbonGroup>

      <RibbonGroup label={gettext("Undo")}>
        <RibbonButton
          icon="fas fa-undo"
          label={gettext("Undo")}
          onClick={undo}
          title={gettext("Undo (Ctrl+Z)")}
        />
        <RibbonButton
          icon="fas fa-redo"
          label={gettext("Redo")}
          onClick={redo}
          title={gettext("Redo (Ctrl+Shift+Z)")}
        />
      </RibbonGroup>

      <RibbonGroup label={gettext("Clipboard")} separator={false}>
        <RibbonButton
          icon="fas fa-copy"
          label={gettext("Copy")}
          onClick={copyFigure}
          disabled={!selectedFigureId}
          title={gettext("Copy (Ctrl+C)")}
        />
        <RibbonButton
          icon="fas fa-paste"
          label={gettext("Paste")}
          onClick={pasteFigure}
          disabled={!clipboard}
          title={gettext("Paste (Ctrl+V)")}
        />
        <RibbonButton
          icon="fas fa-trash-alt"
          label={gettext("Delete")}
          onClick={() => selectedFigureId && removeFigure(selectedFigureId)}
          disabled={!selectedFigureId}
          title={gettext("Delete (Del)")}
        />
      </RibbonGroup>
    </div>
  );
}

/* ── Layout Panel ─────────────────────────────────────────── */

function LayoutPanel({ active }: { active: boolean }) {
  const {
    snapEnabled,
    showRulers,
    rulerUnit,
    toggleSnap,
    toggleRulers,
    toggleRulerUnit,
    alignFigures,
    distributeFigures,
    reorderPanelLetters,
    groupFigures,
    ungroupFigures,
    placedFigures,
    selectedFigureId,
  } = useEditorStore();

  return (
    <div className={`ribbon-panel${active ? " active" : ""}`}>
      <RibbonGroup label={gettext("Figure Align")}>
        <RibbonButton
          icon="fas fa-align-left"
          label={gettext("Left")}
          onClick={() => alignFigures("left")}
        />
        <RibbonButton
          icon="fas fa-align-right"
          label={gettext("Right")}
          onClick={() => alignFigures("right")}
        />
        <RibbonButton
          icon="fas fa-arrow-up"
          label={gettext("Top")}
          onClick={() => alignFigures("top")}
        />
        <RibbonButton
          icon="fas fa-arrow-down"
          label={gettext("Bottom")}
          onClick={() => alignFigures("bottom")}
        />
        <RibbonButton
          icon="fas fa-arrows-alt-h"
          label={gettext("Ctr H")}
          onClick={() => alignFigures("center-h")}
        />
        <RibbonButton
          icon="fas fa-arrows-alt-v"
          label={gettext("Ctr V")}
          onClick={() => alignFigures("center-v")}
        />
      </RibbonGroup>

      <RibbonGroup label={gettext("Axes Align")}>
        <RibbonButton
          icon="fas fa-align-left"
          label={gettext("Ax Left")}
          onClick={() => alignFigures("axes-left")}
        />
        <RibbonButton
          icon="fas fa-align-right"
          label={gettext("Ax Right")}
          onClick={() => alignFigures("axes-right")}
        />
        <RibbonButton
          icon="fas fa-arrow-up"
          label={gettext("Ax Top")}
          onClick={() => alignFigures("axes-top")}
        />
        <RibbonButton
          icon="fas fa-arrow-down"
          label={gettext("Ax Bot")}
          onClick={() => alignFigures("axes-bottom")}
        />
      </RibbonGroup>

      <RibbonGroup label={gettext("Distribute")}>
        <RibbonButton
          icon="fas fa-grip-lines-vertical"
          label={gettext("Horiz")}
          onClick={() => distributeFigures("horizontal")}
        />
        <RibbonButton
          icon="fas fa-grip-lines"
          label={gettext("Vert")}
          onClick={() => distributeFigures("vertical")}
        />
      </RibbonGroup>

      <RibbonGroup label={gettext("Panels")}>
        <RibbonButton
          icon="fas fa-sort-alpha-down"
          label={gettext("Reorder")}
          onClick={reorderPanelLetters}
          title={gettext("Reorder panel letters by position (top-left → bottom-right)")}
        />
        <RibbonButton
          icon="fas fa-object-group"
          label={gettext("Group")}
          onClick={() => {
            const ids = placedFigures.map((f) => f.id);
            if (ids.length >= 2) groupFigures(ids);
          }}
          disabled={placedFigures.length < 2}
          title={gettext("Group all figures (Ctrl+G)")}
        />
        <RibbonButton
          icon="fas fa-object-ungroup"
          label={gettext("Ungroup")}
          onClick={() => {
            const sel = placedFigures.find((f) => f.id === selectedFigureId);
            if (sel?.groupId) ungroupFigures(sel.groupId);
          }}
          disabled={
            !selectedFigureId ||
            !placedFigures.find((f) => f.id === selectedFigureId)?.groupId
          }
          title={gettext("Ungroup selected figure's group")}
        />
      </RibbonGroup>

      <RibbonGroup label={gettext("Guides")} separator={false}>
        <RibbonButton
          icon="fas fa-magnet"
          label={gettext("Snap")}
          onClick={toggleSnap}
          active={snapEnabled}
          title={snapEnabled ? gettext("Snap: ON") : gettext("Snap: OFF")}
        />
        <RibbonButton
          icon="fas fa-ruler-combined"
          label={gettext("Rulers")}
          onClick={toggleRulers}
          active={showRulers}
        />
        <RibbonButton
          icon="fas fa-ruler"
          label={rulerUnit}
          onClick={toggleRulerUnit}
          title={interpolate(gettext("Unit: %s (click to toggle)"), [rulerUnit])}
        />
      </RibbonGroup>
    </div>
  );
}

/* ── Style Panel ──────────────────────────────────────────── */

function StylePanel({ active }: { active: boolean }) {
  const { darkMode, currentTheme, themes, setDarkMode, switchTheme } =
    useEditorStore();

  return (
    <div className={`ribbon-panel${active ? " active" : ""}`}>
      <RibbonGroup label={gettext("Theme")}>
        <select
          className="ribbon-select"
          value={currentTheme}
          onChange={(e) => switchTheme(e.target.value)}
        >
          {themes.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </RibbonGroup>

      <RibbonGroup label={gettext("Appearance")} separator={false}>
        <RibbonButton
          icon={darkMode ? "fas fa-moon" : "fas fa-sun"}
          label={darkMode ? gettext("Dark") : gettext("Light")}
          onClick={() => setDarkMode(!darkMode)}
          active={darkMode}
          title={darkMode ? gettext("Switch to light mode") : gettext("Switch to dark mode")}
        />
      </RibbonGroup>
    </div>
  );
}

/* ── View Panel ───────────────────────────────────────────── */

function ViewPanel({ active }: { active: boolean }) {
  const { zoomControls, showHitmap, toggleHitmap } = useEditorStore();

  return (
    <div className={`ribbon-panel${active ? " active" : ""}`}>
      <RibbonGroup label={gettext("Zoom")}>
        <RibbonButton
          icon="fas fa-search-minus"
          label={gettext("Out")}
          onClick={zoomControls?.zoomOut}
        />
        <RibbonButton
          icon="fas fa-compress-arrows-alt"
          label={gettext("Fit")}
          onClick={zoomControls?.zoomToFit}
        />
        <RibbonButton
          icon="fas fa-search-plus"
          label={gettext("In")}
          onClick={zoomControls?.zoomIn}
        />
        <RibbonButton
          icon="fas fa-undo-alt"
          label={gettext("Reset")}
          onClick={zoomControls?.resetView}
        />
      </RibbonGroup>

      <RibbonGroup label={gettext("Debug")} separator={false}>
        <RibbonButton
          icon="fas fa-bullseye"
          label={gettext("Hitmap")}
          onClick={toggleHitmap}
          active={showHitmap}
          title={gettext("Toggle hit regions")}
        />
      </RibbonGroup>
    </div>
  );
}
