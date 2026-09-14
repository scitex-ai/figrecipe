/** Properties panel — orchestrator for element property editing.
 * Tabs: Current | Preset | Layout | View
 */

import { useCallback, useState } from "react";
import { api } from "../../api/client";
import { useEditorStore } from "../../store/useEditorStore";
import { StatsOverlay } from "../StatsOverlay/StatsOverlay";
import { AxesPositionSection } from "./AxesPositionSection";
import { LabelsSection } from "./LabelsSection";
import { LegendSection } from "./LegendSection";
import { PropRow } from "./PropRow";
import { PropSection } from "./PropSection";
import { gettext, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

type TabId = "current" | "preset" | "layout" | "view";

export function Properties() {
  const {
    selectedElement,
    selectedBbox,
    calls: callsMap,
    showToast,
    refreshAfterMutation,
  } = useEditorStore();
  const [activeTab, setActiveTab] = useState<TabId>("current");

  // Read calls from centralized store (loaded by selectElement action)
  const axKey =
    selectedBbox?.ax_index !== undefined ? String(selectedBbox.ax_index) : null;
  const calls = axKey ? (callsMap[axKey] ?? []) : [];

  const matchedCall = calls.find(
    (c) => c.call_id === selectedBbox?.call_id || c.call_id === selectedElement,
  );

  const handleParamUpdate = useCallback(
    async (callId: string, param: string, value: unknown) => {
      try {
        await api.post("update_call", { call_id: callId, param, value });
        refreshAfterMutation();
      } catch (e) {
        showToast(interpolate(gettext("Update failed: %s"), [e]), "error");
      }
    },
    [showToast, refreshAfterMutation],
  );

  const axIndex = selectedBbox?.ax_index;

  return (
    <div className="properties-panel">
      {/* Selected element info — or empty state */}
      {selectedElement ? (
        <div className="selected-item-info">
          <div className="selected-item-header">{selectedElement}</div>
          {selectedBbox?.label && selectedBbox.label !== selectedElement && (
            <div className="selected-item-label">{selectedBbox.label}</div>
          )}
        </div>
      ) : (
        <div className="selected-item-info">
          <div className="selected-item-header">
            <i className="fas fa-info-circle" style={{ opacity: 0.5 }} />{" "}
            {gettext("No selection")}
          </div>
          <div className="selected-item-label">
            {gettext("Select an item from the tree to view properties")}
          </div>
        </div>
      )}

      {/* Tabs — always visible (vis_app pattern) */}
      <div className="properties-tabs">
        <button
          className={`properties-tab${activeTab === "current" ? " active" : ""}`}
          onClick={() => setActiveTab("current")}
          type="button"
        >
          <i className="fas fa-edit" /> {gettext("Current")}
        </button>
        <button
          className={`properties-tab${activeTab === "preset" ? " active" : ""}`}
          onClick={() => setActiveTab("preset")}
          type="button"
        >
          <i className="fas fa-palette" /> {gettext("Preset")}
        </button>
        <button
          className={`properties-tab${activeTab === "layout" ? " active" : ""}`}
          onClick={() => setActiveTab("layout")}
          type="button"
        >
          <i className="fas fa-th-large" /> {gettext("Layout")}
        </button>
        <button
          className={`properties-tab${activeTab === "view" ? " active" : ""}`}
          onClick={() => setActiveTab("view")}
          type="button"
        >
          <i className="fas fa-eye" /> {gettext("View")}
        </button>
      </div>

      <div className="properties-content">
        {activeTab === "current" && (
          <>
            {!selectedElement ? null : (
              <>
                {axIndex !== undefined && <LabelsSection axIndex={axIndex} />}
                {axIndex !== undefined && (
                  <AxesPositionSection axIndex={axIndex} />
                )}

                {/* Style — from matched call kwargs */}
                {matchedCall && Object.keys(matchedCall.kwargs).length > 0 && (
                  <PropSection title={gettext("Style")}>
                    {Object.entries(matchedCall.kwargs).map(([key, val]) => {
                      if (val === null || val === undefined) return null;
                      const isColor =
                        typeof val === "string" &&
                        /^#[0-9a-fA-F]{3,8}$/.test(val);
                      const isNumber = typeof val === "number";
                      const isBool = typeof val === "boolean";
                      return (
                        <PropRow
                          key={key}
                          label={key}
                          value={val as string | number | boolean}
                          editable
                          type={
                            isColor
                              ? "color"
                              : isNumber
                                ? "number"
                                : isBool
                                  ? "checkbox"
                                  : "text"
                          }
                          onChange={(v) =>
                            handleParamUpdate(matchedCall.call_id, key, v)
                          }
                        />
                      );
                    })}
                  </PropSection>
                )}

                {axIndex !== undefined && <LegendSection axIndex={axIndex} />}
                {axIndex !== undefined && <StatsOverlay axIndex={axIndex} />}

                {calls.length > 0 && (
                  <PropSection title={gettext("Traces")} defaultOpen={false}>
                    {calls.map((c) => (
                      <div key={c.call_id} className="trace-item">
                        <span className="trace-label">
                          {c.method} — {c.call_id}
                        </span>
                      </div>
                    ))}
                  </PropSection>
                )}
              </>
            )}
          </>
        )}

        {activeTab === "preset" && selectedElement && (
          <PropSection title={gettext("Element Info")}>
            <PropRow label={gettext("ID")} value={selectedElement} />
            <PropRow label={gettext("Type")} value={selectedBbox?.type ?? gettext("unknown")} />
            {selectedBbox?.call_id && (
              <PropRow label={gettext("Call ID")} value={selectedBbox.call_id} />
            )}
            {axIndex !== undefined && (
              <PropRow label={gettext("Panel")} value={interpolate(gettext("Axes %s"), [axIndex])} />
            )}
          </PropSection>
        )}

        {activeTab === "layout" && <LayoutTab />}
        {activeTab === "view" && <ViewTab />}
      </div>
    </div>
  );
}

/* ── Layout Tab — align, distribute, panels ──────────────── */

function LayoutTab() {
  const {
    alignFigures,
    distributeFigures,
    reorderPanelLetters,
    groupFigures,
    ungroupFigures,
    placedFigures,
    selectedFigureId,
  } = useEditorStore();

  const selectedFig = placedFigures.find((f) => f.id === selectedFigureId);

  return (
    <>
      <PropSection title={gettext("Figure Align")}>
        <div className="details-btn-grid">
          <button
            className="details-btn"
            type="button"
            title={gettext("Align left")}
            onClick={() => alignFigures("left")}
          >
            <i className="fas fa-align-left" /> {gettext("Left")}
          </button>
          <button
            className="details-btn"
            type="button"
            title={gettext("Align right")}
            onClick={() => alignFigures("right")}
          >
            <i className="fas fa-align-right" /> {gettext("Right")}
          </button>
          <button
            className="details-btn"
            type="button"
            title={gettext("Align top")}
            onClick={() => alignFigures("top")}
          >
            <i className="fas fa-arrow-up" /> {gettext("Top")}
          </button>
          <button
            className="details-btn"
            type="button"
            title={gettext("Align bottom")}
            onClick={() => alignFigures("bottom")}
          >
            <i className="fas fa-arrow-down" /> {gettext("Bottom")}
          </button>
          <button
            className="details-btn"
            type="button"
            title={gettext("Center horizontal")}
            onClick={() => alignFigures("center-h")}
          >
            <i className="fas fa-arrows-alt-h" /> {gettext("Ctr H")}
          </button>
          <button
            className="details-btn"
            type="button"
            title={gettext("Center vertical")}
            onClick={() => alignFigures("center-v")}
          >
            <i className="fas fa-arrows-alt-v" /> {gettext("Ctr V")}
          </button>
        </div>
      </PropSection>

      <PropSection title={gettext("Axes Align")}>
        <div className="details-btn-grid">
          <button
            className="details-btn"
            type="button"
            onClick={() => alignFigures("axes-left")}
          >
            <i className="fas fa-align-left" /> {gettext("Ax Left")}
          </button>
          <button
            className="details-btn"
            type="button"
            onClick={() => alignFigures("axes-right")}
          >
            <i className="fas fa-align-right" /> {gettext("Ax Right")}
          </button>
          <button
            className="details-btn"
            type="button"
            onClick={() => alignFigures("axes-top")}
          >
            <i className="fas fa-arrow-up" /> {gettext("Ax Top")}
          </button>
          <button
            className="details-btn"
            type="button"
            onClick={() => alignFigures("axes-bottom")}
          >
            <i className="fas fa-arrow-down" /> {gettext("Ax Bot")}
          </button>
        </div>
      </PropSection>

      <PropSection title={gettext("Distribute")}>
        <div className="details-btn-grid">
          <button
            className="details-btn"
            type="button"
            onClick={() => distributeFigures("horizontal")}
          >
            <i className="fas fa-grip-lines-vertical" /> {gettext("Horizontal")}
          </button>
          <button
            className="details-btn"
            type="button"
            onClick={() => distributeFigures("vertical")}
          >
            <i className="fas fa-grip-lines" /> {gettext("Vertical")}
          </button>
        </div>
      </PropSection>

      <PropSection title={gettext("Panels")}>
        <div className="details-btn-grid">
          <button
            className="details-btn"
            type="button"
            title={gettext("Reorder panel letters by position")}
            onClick={reorderPanelLetters}
          >
            <i className="fas fa-sort-alpha-down" /> {gettext("Reorder")}
          </button>
          <button
            className="details-btn"
            type="button"
            title={gettext("Group all figures")}
            disabled={placedFigures.length < 2}
            onClick={() => {
              const ids = placedFigures.map((f) => f.id);
              if (ids.length >= 2) groupFigures(ids);
            }}
          >
            <i className="fas fa-object-group" /> {gettext("Group")}
          </button>
          <button
            className="details-btn"
            type="button"
            title={gettext("Ungroup selected")}
            disabled={!selectedFig?.groupId}
            onClick={() => {
              if (selectedFig?.groupId) ungroupFigures(selectedFig.groupId);
            }}
          >
            <i className="fas fa-object-ungroup" /> {gettext("Ungroup")}
          </button>
        </div>
      </PropSection>
    </>
  );
}

/* ── View Tab — theme, zoom, guides ──────────────────────── */

function ViewTab() {
  const {
    darkMode,
    currentTheme,
    themes,
    setDarkMode,
    switchTheme,
    snapEnabled,
    showRulers,
    rulerUnit,
    toggleSnap,
    toggleRulers,
    toggleRulerUnit,
    zoomControls,
    showHitmap,
    toggleHitmap,
  } = useEditorStore();

  return (
    <>
      <PropSection title={gettext("Theme")}>
        <div className="property-group" style={{ marginBottom: 12 }}>
          <label className="property-label">{gettext("Matplotlib Theme")}</label>
          <select
            className="property-select"
            value={currentTheme}
            onChange={(e) => switchTheme(e.target.value)}
          >
            {themes.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <div className="details-btn-grid">
          <button
            className={`details-btn${darkMode ? " details-btn--active" : ""}`}
            type="button"
            onClick={() => setDarkMode(!darkMode)}
          >
            <i className={darkMode ? "fas fa-moon" : "fas fa-sun"} />
            {darkMode ? gettext("Dark") : gettext("Light")}
          </button>
        </div>
      </PropSection>

      <PropSection title={gettext("Zoom")}>
        <div className="details-btn-grid">
          <button
            className="details-btn"
            type="button"
            onClick={zoomControls?.zoomOut}
          >
            <i className="fas fa-search-minus" /> {gettext("Out")}
          </button>
          <button
            className="details-btn"
            type="button"
            onClick={zoomControls?.zoomToFit}
          >
            <i className="fas fa-compress-arrows-alt" /> {gettext("Fit")}
          </button>
          <button
            className="details-btn"
            type="button"
            onClick={zoomControls?.zoomIn}
          >
            <i className="fas fa-search-plus" /> {gettext("In")}
          </button>
          <button
            className="details-btn"
            type="button"
            onClick={zoomControls?.resetView}
          >
            <i className="fas fa-undo-alt" /> {gettext("Reset")}
          </button>
        </div>
      </PropSection>

      <PropSection title={gettext("Guides")}>
        <div className="details-btn-grid">
          <button
            className={`details-btn${snapEnabled ? " details-btn--active" : ""}`}
            type="button"
            onClick={toggleSnap}
          >
            <i className="fas fa-magnet" /> {snapEnabled ? gettext("Snap ON") : gettext("Snap OFF")}
          </button>
          <button
            className={`details-btn${showRulers ? " details-btn--active" : ""}`}
            type="button"
            onClick={toggleRulers}
          >
            <i className="fas fa-ruler-combined" /> {gettext("Rulers")}
          </button>
          <button
            className="details-btn"
            type="button"
            onClick={toggleRulerUnit}
          >
            <i className="fas fa-ruler" /> {rulerUnit}
          </button>
          <button
            className={`details-btn${showHitmap ? " details-btn--active" : ""}`}
            type="button"
            onClick={toggleHitmap}
          >
            <i className="fas fa-bullseye" /> {gettext("Hitmap")}
          </button>
        </div>
      </PropSection>
    </>
  );
}
