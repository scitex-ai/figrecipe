/** Properties panel — orchestrator for element property editing.
 *
 * Three labeled zones, top to bottom:
 *   1. Selection card — WHAT is selected (element id/type/panel/call).
 *      Always visible; the Preset tab's Element Info rows live here now
 *      instead of behind a second tab, so identity never hides.
 *   2. Objects tree (in PropertiesPane, above) — WHERE things live.
 *   3. Tabbed editor — WHAT KIND of edit: Edit (was Current: labels,
 *      style, legend), Arrange (was Layout: align/distribute/panels),
 *      Display (was View: theme/zoom/guides).
 * Tabs always name the verb. No separate Preset tab.
 */

import { useCallback, useState } from "react";
import { api } from "../../api/client";
import { useEditorStore } from "../../store/useEditorStore";
import { StatsOverlay } from "../StatsOverlay/StatsOverlay";
import { AxesPositionSection } from "./AxesPositionSection";
import { ElementDetails } from "./ElementDetails";
import { LabelsSection } from "./LabelsSection";
import { LegendSection } from "./LegendSection";
import { PropRow } from "./PropRow";
import { PropSection } from "./PropSection";
import { SelectorNav } from "@scitex/sdk/ui/react/app/selector-nav";
import { gettext, gettext_noop, interpolate } from "@scitex/sdk/ui/ts/_base/gettext.ts";

type TabId = "edit" | "arrange" | "display";

export function Properties() {
  const {
    selectedElement,
    selectedBbox,
    calls: callsMap,
    showToast,
    refreshAfterMutation,
    placedFigures,
  } = useEditorStore();
  const [activeTab, setActiveTab] = useState<TabId>("edit");

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
      {/* Selected element info — or an empty state that says what to do
          next. The Objects tree above is always visible, so "from the tree"
          now names something on screen. */}
      {/* Zone 1 — Selection card: WHAT is selected. Identity rows
          (ex-Preset Element Info) live here, always visible, never behind
          a tab. Zone 2 (Objects tree) is above in PropertiesPane. */}
      {selectedElement ? (
        <div className="selected-item-info">
          <div className="selected-item-header">{selectedElement}</div>
          <div className="selected-item-identity">
            <span className="selected-item-identity-row">
              <span className="selected-item-identity-label">{gettext("Type")}</span>
              <span>{selectedBbox?.type ?? gettext("unknown")}</span>
            </span>
            {selectedBbox?.call_id && (
              <span className="selected-item-identity-row">
                <span className="selected-item-identity-label">{gettext("Call ID")}</span>
                <span>{selectedBbox.call_id}</span>
              </span>
            )}
            {axIndex !== undefined && (
              <span className="selected-item-identity-row">
                <span className="selected-item-identity-label">{gettext("Panel")}</span>
                <span>{interpolate(gettext("Axes %s"), [axIndex])}</span>
              </span>
            )}
          </div>
          {selectedBbox?.label && selectedBbox.label !== selectedElement && (
            <div className="selected-item-label">{selectedBbox.label}</div>
          )}
        </div>
      ) : (
        <div className="properties-panel__empty">
          <i
            className="fas fa-info-circle properties-empty-icon"
            aria-hidden="true"
          />
          <div className="properties-empty-title">
            {gettext("No selection")}
          </div>
          {placedFigures.length === 0 ? (
            <div className="properties-empty-hint">
              {gettext("No figures yet.")}
              {/* Operator UI batch: no "Go to Data" door in the Details pane.
                  The Data tab is its own full-width destination — Details
                  must not route there. The empty Panel + tree hint remain. */}
            </div>
          ) : (
            <div className="properties-empty-hint">
              {gettext("Select an item from the tree to view properties")}
            </div>
          )}
        </div>
      )}

      {/* Zone 3 — Tabbed editor. Tab labels name the verb. */}
      <div className="properties-tabs">
        <button
          className={`properties-tab${activeTab === "edit" ? " active" : ""}`}
          onClick={() => setActiveTab("edit")}
          type="button"
        >
          <i className="fas fa-edit" /> {gettext("Edit")}
        </button>
        <button
          className={`properties-tab${activeTab === "arrange" ? " active" : ""}`}
          onClick={() => setActiveTab("arrange")}
          type="button"
        >
          <i className="fas fa-th-large" /> {gettext("Arrange")}
        </button>
        <button
          className={`properties-tab${activeTab === "display" ? " active" : ""}`}
          onClick={() => setActiveTab("display")}
          type="button"
        >
          <i className="fas fa-eye" /> {gettext("Display")}
        </button>
      </div>

      <div className="properties-content">
        {activeTab === "edit" && (
          <>
            {!selectedElement ? null : (
              <>
                <ElementDetails />
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

        {activeTab === "arrange" && <LayoutTab />}
        {activeTab === "display" && <ViewTab />}
      </div>
    </div>
  );
}

/* ── Layout Tab — align, distribute, panels ──────────────── */

/* Align actions as SDK shared controls (operator batch
 * apps-figrecipe-ui-feedback-20261023 item 4): the bespoke Figure/Axes Align
 * button grids are gone, replaced by the same SelectorNav the plot-type
 * rail uses — one shared control, real <button>s (keyboard-operable),
 * icon + translated label. Labels follow the PLOT_TYPES gettext_noop
 * pattern (marked here, translated at render). */
const FIGURE_ALIGN_ITEMS = [
  { id: "left", icon: "fas fa-align-left", label: gettext_noop("Left") },
  { id: "right", icon: "fas fa-align-right", label: gettext_noop("Right") },
  { id: "top", icon: "fas fa-arrow-up", label: gettext_noop("Top") },
  { id: "bottom", icon: "fas fa-arrow-down", label: gettext_noop("Bottom") },
  { id: "center-h", icon: "fas fa-arrows-alt-h", label: gettext_noop("Ctr H") },
  { id: "center-v", icon: "fas fa-arrows-alt-v", label: gettext_noop("Ctr V") },
] as const;

const AXES_ALIGN_ITEMS = [
  { id: "axes-left", icon: "fas fa-align-left", label: gettext_noop("Ax Left") },
  { id: "axes-right", icon: "fas fa-align-right", label: gettext_noop("Ax Right") },
  { id: "axes-top", icon: "fas fa-arrow-up", label: gettext_noop("Ax Top") },
  { id: "axes-bottom", icon: "fas fa-arrow-down", label: gettext_noop("Ax Bot") },
] as const;

type AlignItemId =
  | (typeof FIGURE_ALIGN_ITEMS)[number]["id"]
  | (typeof AXES_ALIGN_ITEMS)[number]["id"];

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
        <SelectorNav
          items={FIGURE_ALIGN_ITEMS.map((item) => ({
            ...item,
            label: gettext(item.label),
          }))}
          activeId={null}
          onSelect={(id) => alignFigures(id as AlignItemId)}
          style={{ width: "100%" }}
        />
      </PropSection>

      <PropSection title={gettext("Axes Align")}>
        <SelectorNav
          items={AXES_ALIGN_ITEMS.map((item) => ({
            ...item,
            label: gettext(item.label),
          }))}
          activeId={null}
          onSelect={(id) => alignFigures(id as AlignItemId)}
          style={{ width: "100%" }}
        />
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
            <i className={darkMode ? "fas fa-moon" : "fas fa-circle-half-stroke"} />
            {darkMode ? gettext("Dark") : gettext("Light")}
          </button>
        </div>
      </PropSection>

      <PropSection title={gettext("Zoom")}>
        {/* Dead until the Figure canvas mounts and registers its controls
            (operator batch apps-figrecipe-ui-feedback-20261023 item 4): a
            click before that was a silent no-op, so the buttons stand down. */}
        <div className="details-btn-grid">
          <button
            className="details-btn"
            type="button"
            onClick={zoomControls?.zoomOut}
            disabled={!zoomControls}
          >
            <i className="fas fa-search-minus" /> {gettext("Out")}
          </button>
          <button
            className="details-btn"
            type="button"
            onClick={zoomControls?.zoomToFit}
            disabled={!zoomControls}
          >
            <i className="fas fa-compress-arrows-alt" /> {gettext("Fit")}
          </button>
          <button
            className="details-btn"
            type="button"
            onClick={zoomControls?.zoomIn}
            disabled={!zoomControls}
          >
            <i className="fas fa-search-plus" /> {gettext("In")}
          </button>
          <button
            className="details-btn"
            type="button"
            onClick={zoomControls?.resetView}
            disabled={!zoomControls}
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
