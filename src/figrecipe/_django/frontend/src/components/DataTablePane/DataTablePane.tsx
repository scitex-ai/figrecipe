/** Left pane — Data table with vis_app pane-header.
 * Uses scitex-ui's shared DataTable component (no figrecipe-original table). */

import { useCallback, useRef } from "react";
import { DataTable } from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/data-table/DataTable";
import { api } from "../../api/client";
import { useEditorStore } from "../../store/useEditorStore";
import { getPanelColor } from "../../utils/panelColors";

interface DataTablePaneProps {
  onHeaderDoubleClick?: () => void;
}

export function DataTablePane({ onHeaderDoubleClick }: DataTablePaneProps) {
  const {
    datatableTabs,
    activeTabId,
    highlightedDataRows: _highlightedDataRows,
    placedFigures,
    removeFigure,
    showToast,
    loadDatatable,
    refreshAfterMutation,
  } = useEditorStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const tabs = Object.values(datatableTabs);
  const activeTab = activeTabId ? datatableTabs[activeTabId] : null;

  console.log(
    "[DataTablePane] tabs:",
    tabs.length,
    "activeTabId:",
    activeTabId,
    "activeTab:",
    activeTab
      ? { cols: activeTab.columns?.length, rows: activeTab.rows?.length }
      : null,
  );

  /** Close a tab and remove the corresponding figure from canvas. */
  const handleCloseTab = useCallback(
    (tabId: string) => {
      // Find figure that matches this tab by path, id, or fall back to selected/first
      const figure =
        placedFigures.find((f) => f.path === tabId || f.id === tabId) ??
        placedFigures.find(
          (f) => f.id === useEditorStore.getState().selectedFigureId,
        ) ??
        (placedFigures.length === 1 ? placedFigures[0] : null);
      if (figure) {
        removeFigure(figure.id);
      }
      // Always remove the tab
      useEditorStore.setState((s) => {
        const updated = { ...s.datatableTabs };
        delete updated[tabId];
        const remaining = Object.keys(updated);
        return {
          datatableTabs: updated,
          activeTabId: remaining.length > 0 ? remaining[0] : null,
        };
      });
    },
    [placedFigures, removeFigure],
  );

  const handleExportCsv = useCallback(async () => {
    try {
      const blob = await api.getBlob("download/csv");
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "data.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      showToast(`Export failed: ${e}`, "error");
    }
  }, [showToast]);

  const handleImportCsv = useCallback(
    async (file: File) => {
      try {
        const content = await file.text();
        const ext = file.name.split(".").pop()?.toLowerCase();
        const format = ext === "tsv" ? "tsv" : ext === "json" ? "json" : "csv";
        await api.post("datatable/import", { content, format });
        showToast("Imported data", "success");
        loadDatatable();
        refreshAfterMutation();
      } catch (e) {
        showToast(`Import failed: ${e}`, "error");
      }
    },
    [showToast, loadDatatable, refreshAfterMutation],
  );

  return (
    <>
      {/* vis_app .pane-header */}
      <div className="pane-header" onDoubleClick={onHeaderDoubleClick}>
        {/* Data dropdown */}
        <div className="data-dropdown-container">
          <button className="data-dropdown-toggle" type="button">
            <i className="fas fa-table" />
            <span className="data-dropdown-label">
              {tabs.length > 0
                ? `${tabs.length} table${tabs.length > 1 ? "s" : ""}`
                : "No tables"}
            </span>
            <i className="fas fa-chevron-down" />
          </button>
          <button
            className="pane-header-btn data-new-btn"
            type="button"
            onClick={() => fileInputRef.current?.click()}
            title="Import data"
          >
            <i className="fas fa-plus" />
          </button>
        </div>

        {/* WIP badge */}
        <span className="badge badge-wip">WIP</span>

        {/* Action buttons */}
        <div className="pane-header-buttons">
          <button
            className="pane-header-btn"
            onClick={handleExportCsv}
            title="Export CSV"
            disabled={tabs.length === 0}
            type="button"
          >
            <i className="fas fa-file-export" />
          </button>
          <button
            className="pane-header-btn"
            title="Sort (WIP)"
            type="button"
            disabled
          >
            <i className="fas fa-sort" />
          </button>
          <button
            className="pane-header-btn"
            title="Filter (WIP)"
            type="button"
            disabled
          >
            <i className="fas fa-filter" />
          </button>
          <button
            className="pane-header-btn"
            title="Keyboard shortcuts"
            type="button"
          >
            <i className="fas fa-keyboard" />
          </button>
        </div>

        {/* Vertical title with icon (visible only when collapsed via CSS) */}
        <span className="panel-title">
          <i className="fas fa-table" />
          Table
        </span>
      </div>

      {/* Hidden file input for CSV import */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,.tsv,.json,.xlsx"
        style={{ display: "none" }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleImportCsv(file);
          e.target.value = "";
        }}
      />

      {/* Pane content — uses shared scitex-ui DataTable */}
      <div className="pane-content">
        {tabs.length >= 1 && (
          <div className="datatable-panel__tabs">
            {tabs.map((tab, idx) => (
              <button
                key={tab.id}
                className={`datatable-panel__tab${tab.id === activeTabId ? " active" : ""}`}
                style={{
                  borderLeft: `3px solid ${getPanelColor(idx)}`,
                }}
                onClick={() => useEditorStore.setState({ activeTabId: tab.id })}
                type="button"
              >
                {tab.label}
                <span
                  className="datatable-panel__tab-close"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCloseTab(tab.id);
                  }}
                  title="Close tab and remove figure"
                >
                  &times;
                </span>
              </button>
            ))}
          </div>
        )}
        <DataTable
          data={
            activeTab
              ? {
                  columns: activeTab.columns.map((c) => c.name),
                  rows: activeTab.rows.map((row) => {
                    const obj: Record<string, string | number> = {};
                    activeTab.columns.forEach((col, ci) => {
                      obj[col.name] = row[ci] ?? "";
                    });
                    return obj;
                  }),
                }
              : undefined
          }
          style={{ flex: 1 }}
        />
      </div>
    </>
  );
}
