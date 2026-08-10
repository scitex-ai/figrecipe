/** Data table panel — displays plot data with CSV import/export.
 *
 * Uses scitex-ui's shared DataTable for rendering.
 * figrecipe adds: tabs, import/export, editor store integration.
 */

import { useCallback, useMemo, useRef } from "react";
import { DataTable as StxDataTable } from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/data-table";
import type { Dataset } from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/data-table";
import { api } from "../../api/client";
import { useEditorStore } from "../../store/useEditorStore";

export function DataTable() {
  const { datatableTabs, activeTabId, showToast, loadDatatable } =
    useEditorStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const tabs = Object.values(datatableTabs);
  const activeTab = activeTabId ? datatableTabs[activeTabId] : null;

  // Convert figrecipe tab data to scitex-ui Dataset format
  const dataset: Dataset | undefined = useMemo(() => {
    if (!activeTab) return undefined;
    return {
      columns: activeTab.columns.map((c) => c.name),
      rows: activeTab.rows.map((row) => {
        const obj: Record<string, string | number> = {};
        activeTab.columns.forEach((col, i) => {
          obj[col.name] = row[i] ?? "";
        });
        return obj;
      }),
    };
  }, [activeTab]);

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
      } catch (e) {
        showToast(`Import failed: ${e}`, "error");
      }
    },
    [showToast, loadDatatable],
  );

  return (
    <div className="datatable-panel">
      <div className="datatable-panel__header">
        <h3>Data</h3>
        <div className="datatable-panel__actions">
          <button
            className="pane-header-btn"
            onClick={() => fileInputRef.current?.click()}
            title="Import CSV"
          >
            <i className="fas fa-upload" />
          </button>
          <button
            className="pane-header-btn"
            onClick={handleExportCsv}
            title="Export CSV"
            disabled={tabs.length === 0}
          >
            <i className="fas fa-download" />
          </button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.tsv,.json"
          style={{ display: "none" }}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleImportCsv(file);
            e.target.value = "";
          }}
        />
      </div>

      {tabs.length === 0 ? (
        <div className="datatable-panel__empty">
          <p>No data available</p>
          <p className="datatable-panel__hint">
            Plot data will appear here when a figure is loaded
          </p>
        </div>
      ) : (
        <>
          <div className="datatable-panel__tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={`datatable-panel__tab${tab.id === activeTabId ? " active" : ""}`}
                onClick={() => useEditorStore.setState({ activeTabId: tab.id })}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {dataset && (
            <StxDataTable data={dataset} showRowNumbers sortable resizable />
          )}
        </>
      )}
    </div>
  );
}
