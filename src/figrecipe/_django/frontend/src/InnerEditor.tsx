/** InnerEditor — React editor content (without shell chrome).
 *
 * This is what gets mounted inside Workspace's appContent slot.
 * Two tabs:
 *   - Plot: DataTable | PlotTypeNav | FigureViewer | Details
 *   - Canvas: Canvas | Details
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { CanvasPane } from "./components/CanvasPane/CanvasPane";
import { DataTablePane } from "./components/DataTablePane/DataTablePane";
import { FigureViewer } from "./components/FigureViewer/FigureViewer";
import { PlotTypeNav } from "./components/PlotTypeNav/PlotTypeNav";
import { PropertiesPane } from "./components/PropertiesPane/PropertiesPane";
import { Spinner } from "./components/common/Spinner";
import { Toast } from "./components/common/Toast";
// Element inspector now provided by scitex-ui (imported in main.tsx)
import { useEmbeddedMessages } from "./hooks/useEmbeddedMessages";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";
import { usePanelResize } from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/usePanelResize";
import { AlertBanner } from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/alert-banner";
import { useSessionPersistence } from "./hooks/useSessionPersistence";
import { initUndoHistory } from "./hooks/useUndoRedo";
import { useEditorStore } from "./store/useEditorStore";

type AppTab = "plot" | "canvas";

interface InnerEditorProps {
  embedded?: boolean;
}

export function InnerEditor({ embedded = false }: InnerEditorProps) {
  const {
    loading,
    loadPreview,
    loadHitmap,
    loadFiles,
    loadThemes,
    loadDatatable,
    toast,
    clearToast,
  } = useEditorStore();

  const [activeTab, setActiveTab] = useState<AppTab>(() => {
    try {
      return (localStorage.getItem("figrecipe-app-tab") as AppTab) || "plot";
    } catch {
      return "plot";
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem("figrecipe-app-tab", activeTab);
    } catch {}
  }, [activeTab]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const hasRecipe = !!params.get("recipe");

    loadFiles();
    loadThemes();

    if (hasRecipe) {
      loadPreview();
      loadHitmap();
      loadDatatable();
    }
  }, [loadPreview, loadHitmap, loadFiles, loadThemes, loadDatatable]);

  // Global hooks (element inspector from scitex-ui, initialized in main.tsx)
  useKeyboardShortcuts();
  useSessionPersistence();
  useEmbeddedMessages(embedded);

  // Initialize undo history once on mount
  useEffect(() => {
    initUndoHistory();
  }, []);

  // Shell resizer handles overflow via getMaxAllowedWidth() — no React propagation needed

  // Ref for center pane (used by auto-collapse + context-zoom)
  const centerRef = useRef<HTMLElement | null>(null);

  // Center pane collapse — supports both double-click toggle AND
  // auto-collapse when resizer pushes width below threshold.
  const CENTER_MIN_WIDTH = 60;
  const [centerCollapsed, setCenterCollapsed] = useState(() => {
    try {
      return localStorage.getItem("figrecipe-center-collapsed") === "true";
    } catch {
      return false;
    }
  });
  const toggleCenter = useCallback(() => {
    setCenterCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem("figrecipe-center-collapsed", String(next));
      } catch {}
      return next;
    });
  }, []);

  // Auto-collapse center pane when it gets too narrow (e.g. right panel resized)
  useEffect(() => {
    const el = centerRef.current;
    if (!el || centerCollapsed) return;
    const obs = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect.width < CENTER_MIN_WIDTH && !centerCollapsed) {
          setCenterCollapsed(true);
          try {
            localStorage.setItem("figrecipe-center-collapsed", "true");
          } catch {}
        }
      }
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, [centerCollapsed]);

  // Create refs for cross-panel coordination (prevents pushing rightmost panel off-screen)
  const rightPanelRef = useRef<HTMLElement | null>(null);

  const dataPanel = usePanelResize({
    direction: "left",
    minWidth: 40,
    defaultWidth: 200,
    storageKey: "figrecipe-data-width",
    collapseKey: "figrecipe-data-collapsed",
    // Reserve space for right panel + PlotTypeNav (fixed ~60px)
    siblingRefs: [rightPanelRef],
    reservedWidth: 60,
  });

  const rightPanel = usePanelResize({
    direction: "right",
    minWidth: 40,
    defaultWidth: 240,
    storageKey: "figrecipe-right-width",
    collapseKey: "figrecipe-right-collapsed",
  });

  // Sync the shared ref with rightPanel's panelRef
  useEffect(() => {
    rightPanelRef.current = rightPanel.panelRef.current;
  });

  return (
    <div className="inner-editor">
      {/* ── Tab Switcher ────────────────────────────── */}
      <div className="inner-editor__tabs">
        <button
          className={`inner-editor__tab${activeTab === "plot" ? " inner-editor__tab--active" : ""}`}
          onClick={() => setActiveTab("plot")}
        >
          <i className="fas fa-chart-line" /> Plot
        </button>
        <button
          className={`inner-editor__tab${activeTab === "canvas" ? " inner-editor__tab--active" : ""}`}
          onClick={() => setActiveTab("canvas")}
        >
          <i className="fas fa-object-group" /> Canvas
        </button>
      </div>

      {/* ── Tab Content ─────────────────────────────── */}
      <div className="editor-body">
        {activeTab === "plot" && (
          <>
            {/* Pane 1 — Data Table */}
            <aside
              ref={dataPanel.panelRef as React.Ref<HTMLElement>}
              className={`split-pane split-pane-left${dataPanel.collapsed ? " collapsed" : ""}`}
              style={
                dataPanel.collapsed ? undefined : { width: dataPanel.width }
              }
            >
              <DataTablePane
                onHeaderDoubleClick={dataPanel.headerProps.onDoubleClick}
              />
            </aside>

            <div className="panel-resizer" {...dataPanel.resizerProps} />

            {/* Plot type selector nav — fixed width, not resizable */}
            <PlotTypeNav />

            {/* Pass-through resizer — propagates to DataTable (PlotTypeNav stays fixed) */}
            <div className="panel-resizer" {...dataPanel.resizerProps} />

            {/* Pane 2 — Figure Viewer (rendered image, not canvas) */}
            <main
              ref={centerRef as React.Ref<HTMLElement>}
              className={`split-pane split-pane-center${centerCollapsed ? " collapsed" : ""}`}
            >
              {centerCollapsed ? (
                <div className="pane-header" onDoubleClick={toggleCenter}>
                  <span className="panel-title">
                    <i className="fas fa-image" />
                    Viewer
                  </span>
                </div>
              ) : (
                <>
                  <div
                    className="pane-header pane-header--minimal"
                    onDoubleClick={toggleCenter}
                    title="Double-click to collapse"
                  >
                    <i className="fas fa-image" style={{ opacity: 0.5 }} />
                  </div>
                  <FigureViewer />
                </>
              )}
            </main>
          </>
        )}

        {activeTab === "canvas" && (
          <>
            {/* Canvas pane */}
            <main
              ref={centerRef as React.Ref<HTMLElement>}
              className={`split-pane split-pane-center${centerCollapsed ? " collapsed" : ""}`}
            >
              {centerCollapsed ? (
                <div className="pane-header" onDoubleClick={toggleCenter}>
                  <span className="panel-title">
                    <i className="fas fa-object-group" />
                    Canvas
                  </span>
                </div>
              ) : (
                <>
                  <div
                    className="pane-header pane-header--minimal"
                    onDoubleClick={toggleCenter}
                    title="Double-click to collapse"
                  >
                    <i
                      className="fas fa-object-group"
                      style={{ opacity: 0.5 }}
                    />
                  </div>
                  <CanvasPane />
                </>
              )}
            </main>
          </>
        )}

        {/* Resizer + Details grouped together and pushed to far right */}
        <div
          className="stx-layout-most-right"
          style={{ display: "flex", flexShrink: 0, marginLeft: "auto" }}
        >
          <div className="panel-resizer" {...rightPanel.resizerProps} />
          <aside
            ref={rightPanel.panelRef as React.Ref<HTMLElement>}
            className={`split-pane split-pane-right${rightPanel.collapsed ? " collapsed" : ""}`}
            style={
              rightPanel.collapsed ? undefined : { width: rightPanel.width }
            }
          >
            <PropertiesPane
              onHeaderDoubleClick={rightPanel.headerProps.onDoubleClick}
            />
          </aside>
        </div>
      </div>

      {loading && <Spinner />}
      <Toast />
      <AlertBanner
        open={toast?.type === "error"}
        type="error"
        message={toast?.type === "error" ? toast.message : ""}
        onDismiss={clearToast}
      />
    </div>
  );
}
