/** InnerEditor — React editor content (without shell chrome).
 *
 * This is what gets mounted inside Workspace's appContent slot.
 * Stable panes: Data -> Plot -> Figure -> Details. Desktop tabs keep the
 * SigmaPlot-style full-width worksheet and the resizable Details column.
 *   - Plot: PlotTypeNav | FigureViewer | Objects + Details
 *   - Data: full-width DataTablePane (import, paste, sample, edit)
 *   - Canvas: Canvas | Objects + Details
 */

import { useEffect, useRef, useState } from "react";
import { CanvasPane } from "./components/CanvasPane/CanvasPane";
import { DataTablePane } from "./components/DataTablePane/DataTablePane";
import { FigureViewer } from "./components/FigureViewer/FigureViewer";
import { PlotTypeNav } from "./components/PlotTypeNav/PlotTypeNav";
import { PropertiesPane } from "./components/PropertiesPane/PropertiesPane";
import { ProjectScopeSelector } from "./components/ProjectScopeSelector";
import { Spinner } from "./components/common/Spinner";
import { Toast } from "./components/common/Toast";
// Element inspector now provided by scitex-ui (imported in main.tsx)
import { useEmbeddedMessages } from "./hooks/useEmbeddedMessages";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";
import { usePanelResize } from "@scitex/sdk/ui/react/app/usePanelResize.ts";
import { AlertBanner } from "@scitex/sdk/ui/react/app/alert-banner";
import { useSessionPersistence } from "./hooks/useSessionPersistence";
import { initUndoHistory } from "./hooks/useUndoRedo";
import { useEditorStore } from "./store/useEditorStore";
import { mountEditorPanes, releaseEditorPanes, showEditorPane, usePhoneLayout } from "./components/mobilePanes";
import { PANES_CHANGE } from "@scitex/sdk/ui/ts/app/panes";
import type { PanesChangeDetail } from "@scitex/sdk/ui/ts/app/panes";
import type { EditorPane } from "./components/mobilePanes";
import { gettext } from "@scitex/sdk/ui/ts/_base/gettext.ts";

type AppTab = "plot" | "data" | "canvas";

interface InnerEditorProps {
  embedded?: boolean;
  initialRecipe?: string;
  /**
   * Explicit figrecipe version for the header badge. Resolution order:
   * this prop (host/mount contract) -> #root[data-version] (standalone
   * Django view) -> __FIGRECIPE_VERSION__ (build-time from pyproject.toml,
   * covers the Hub #app-mount path where neither is stamped).
   */
  appVersion?: string;
}

export function InnerEditor({ embedded = false, appVersion, initialRecipe }: InnerEditorProps) {
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

  // figrecipe's own version for the header badge (distinct from the Hub global
  // header's Hub-version). Resolution: explicit prop -> #root[data-version] ->
  // build-derived __FIGRECIPE_VERSION__ (covers the #app-mount host path).
  const resolvedVersion = (() => {
    if (appVersion) return appVersion;
    try {
      const stamped = document.getElementById("root")?.getAttribute("data-version");
      if (stamped) return stamped;
    } catch {
      /* #root absent (host mount) */
    }
    try {
      return typeof __FIGRECIPE_VERSION__ !== "undefined" ? __FIGRECIPE_VERSION__ : "";
    } catch {
      return "";
    }
  })();
  const [activeTab, setActiveTab] = useState<AppTab>(() => {
    try {
      const stored = localStorage.getItem("figrecipe-app-tab") as AppTab;
      if (stored === "data") return "data";
      if (stored === "canvas") return "canvas";
      return "plot";
    } catch {
      return "plot";
    }
  });

  const [stepsDismissed, setStepsDismissed] = useState(() => {
    try {
      return localStorage.getItem("figrecipe-steps-dismissed") === "1";
    } catch {
      return false;
    }
  });
  const dismissSteps = () => {
    setStepsDismissed(true);
    try {
      localStorage.setItem("figrecipe-steps-dismissed", "1");
    } catch {}
  };

  useEffect(() => {
    try {
      localStorage.setItem("figrecipe-app-tab", activeTab);
    } catch {}
  }, [activeTab]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const hasRecipe = !!(initialRecipe || params.get("recipe"));

    loadFiles();
    loadThemes();

    if (hasRecipe) {
      loadPreview();
      loadHitmap();
      loadDatatable();
    }
  }, [initialRecipe, loadPreview, loadHitmap, loadFiles, loadThemes, loadDatatable]);

  // Global hooks (element inspector from scitex-ui, initialized in main.tsx)
  useKeyboardShortcuts();
  useSessionPersistence();
  useEmbeddedMessages(embedded);

  // Initialize undo history once on mount
  useEffect(() => {
    initUndoHistory();
  }, []);

  // Shell resizer handles overflow via getMaxAllowedWidth() — no React propagation needed

  // NOTE: the center (Viewer/Canvas) pane intentionally has NO collapse
  // toggle. A single-viewer pane has nothing to toggle between, and the
  // collapsed 40px "VIEWER" tab plus the 20px minimal header strip were
  // dead UI. The pane is always expanded; narrow screens fall back to the
  // phone tab layout (see usePhoneLayout) instead of collapsing.

  // Create refs for cross-panel coordination (prevents pushing rightmost panel off-screen)
  const rightPanel = usePanelResize({
    direction: "right",
    minWidth: 40,
    defaultWidth: 240,
    storageKey: "figrecipe-right-width",
    collapseKey: "figrecipe-right-collapsed",
  });

  // Hub phones: the columns become tabs (scitex-ui panes); collapse bars do not apply.
  const phone = usePhoneLayout();
  const [phonePane, setPhonePane] = useState<EditorPane>(() => {
    try {
      const stored = localStorage.getItem("figrecipe-app-tab");
      if (stored === "canvas") return "figure";
      if (stored === "plot") return "plot";
    } catch {}
    return "data";
  });
  const bodyRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const body = bodyRef.current;
    const host = body?.parentElement;
    if (!body || !host) return;
    const syncActivePane = (pane: string) => {
      setPhonePane(pane as EditorPane);
      if (pane === "data" || pane === "plot") setActiveTab(pane);
      else if (pane === "figure") setActiveTab("canvas");
      // Details stays beside the selected desktop page.
    };
    const onChange = (event: Event) => {
      if (event.target !== body) return;
      const detail = (event as CustomEvent<PanesChangeDetail>).detail;
      if (detail?.app === "figrecipe" && ["data", "plot", "figure", "details"].includes(detail.pane)) {
        syncActivePane(detail.pane);
      }
    };
    body.addEventListener(PANES_CHANGE, onChange);
    // SDK panes collect direct children once. Their nodes stay mounted below,
    // so switching desktop pages never invalidates the phone tab registry.
    const mounted = mountEditorPanes(host);
    if (mounted) {
      // SDK show() emits no event for the already-active pane. Align the
      // initial desktop tab before accepting named routes; phones keep the
      // SDK's restored selection.
      if (!mounted.single) mounted.show(activeTab === "canvas" ? "figure" : activeTab);
      syncActivePane(mounted.active);
    }
    return () => {
      body.removeEventListener(PANES_CHANGE, onChange);
      releaseEditorPanes(body);
    };
  }, []);
  const selectTab = (tab: AppTab) => {
    setActiveTab(tab);
    showEditorPane(tab === "canvas" ? "figure" : tab);
  };
  const plotActive = phone ? phonePane === "plot" : activeTab === "plot";
  const dataActive = phone ? phonePane === "data" : activeTab === "data";
  const canvasActive = phone ? phonePane === "figure" : activeTab === "canvas";
  const detailsCollapsed = rightPanel.collapsed && !phone;
  const paneAttrs = (
    id: string,
    label: string,
    order: number,
  ): Record<string, string | number> =>
    ({ "data-stx-pane": id, "data-stx-label": label, "data-stx-order": order });

  return (
    <div className="inner-editor" data-editor-tab={activeTab}>
      {/* ── App header (figrecipe-owned) — canonical .stx-app-header ─────
          Structure: title, then the shared project-selector slot, then
          (optional) app actions. The selector lives HERE (not the tab row)
          per the 0.22.0 placement contract; the scitex-ui slot CSS
          (.stx-app-header__slot--project-selector) pins it left-after-title
          on desktop and full-width on phones. The vestigial React Toolbar's
          "FigRecipe Editor" title is not in this render tree, so this is the
          only visible title (no duplication). */}
      <header className="stx-app-header">
        <span className="stx-app-header__title">{gettext("FigRecipe")}</span>
        {resolvedVersion && (
          <span className="stx-app-header__version">v{resolvedVersion}</span>
        )}
        <div className="stx-app-header__slot--project-selector">
          <ProjectScopeSelector />
        </div>
      </header>

      {/* ── Tab Switcher ────────────────────────────── */}
      <div className="inner-editor__tabs" role="tablist">
        <button
          className={`inner-editor__tab${activeTab === "data" ? " inner-editor__tab--active" : ""}`}
          onClick={() => selectTab("data")}
          role="tab"
          aria-selected={activeTab === "data"}
          title={gettext("Data table — its own full-width page")}
        >
          <i className="fas fa-table" /> {gettext("Data")}
        </button>
        <button
          className={`inner-editor__tab${activeTab === "plot" ? " inner-editor__tab--active" : ""}`}
          onClick={() => selectTab("plot")}
          role="tab"
          aria-selected={activeTab === "plot"}
        >
          <i className="fas fa-chart-line" /> {gettext("Plot")}
        </button>
        <button
          className={`inner-editor__tab${activeTab === "canvas" ? " inner-editor__tab--active" : ""}`}
          onClick={() => selectTab("canvas")}
          role="tab"
          aria-selected={activeTab === "canvas"}
        >
          <i className="fas fa-object-group" /> {gettext("Figure")}
        </button>
      </div>

      {!stepsDismissed && plotActive && (
        <div className="fr-steps" role="note">
          <ol className="fr-steps__list">
            <li>{gettext("1. Pick or import data")}</li>
            <li>{gettext("2. Choose a plot type")}</li>
            <li>{gettext("3. Adjust & export")}</li>
          </ol>
          <button
            type="button"
            className="fr-steps__close"
            onClick={dismissSteps}
            aria-label={gettext("Close")}
            title={gettext("Close")}
          >
            <i className="fas fa-times" aria-hidden="true" />
          </button>
        </div>
      )}

      {/* ── Tab Content ─────────────────────────────── */}
      <div
        ref={bodyRef}
        className="editor-body"
        data-stx-panes="figrecipe"
        data-stx-panes-layout="app"
        data-stx-active={phonePane}
      >
        {/* SigmaPlot-style worksheet: the data table gets its own
            full-width page instead of a squeezed strip beside the viewer. */}
        <div className="data-page" {...paneAttrs("data", gettext("Data"), 1)}>
          <div className="data-page__inner">
            <DataTablePane hideCollapse active={dataActive} />
          </div>
        </div>
        <section className="editor-plot-page" {...paneAttrs("plot", gettext("Plot"), 2)}>
          {/* Plot type selector nav — fixed width, not resizable. */}
          <PlotTypeNav />
          {/* Rendered figure viewer — always expanded. */}
          <main className="split-pane split-pane-center">
            <FigureViewer />
          </main>
        </section>
        {/* Composition canvas — always expanded. */}
        <main className="split-pane split-pane-center editor-figure-page" {...paneAttrs("figure", gettext("Figure"), 3)}>
          <CanvasPane active={canvasActive} />
        </main>

        {/* Resizer + Details grouped together and pushed to far right */}
        <div
          className="stx-layout-most-right"
          style={{ display: "flex", flexShrink: 0, marginLeft: "auto" }}
          {...paneAttrs("details", gettext("Details"), 4)}
        >
          <div className="panel-resizer" {...rightPanel.resizerProps} />
          <aside
            ref={rightPanel.panelRef as React.Ref<HTMLElement>}
            className={`split-pane split-pane-right${detailsCollapsed ? " collapsed" : ""}`}
            style={detailsCollapsed ? undefined : { width: rightPanel.width }}
          >
            <PropertiesPane
              onToggleCollapse={rightPanel.toggleCollapse}
              collapsed={detailsCollapsed}
              onRequestDataTab={() => selectTab("data")}
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
