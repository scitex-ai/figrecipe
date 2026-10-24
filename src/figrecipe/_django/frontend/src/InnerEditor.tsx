/** InnerEditor — React editor content (without shell chrome).
 *
 * This is what gets mounted inside Workspace's appContent slot.
 * Stable pages: Figure <- Panels <- Tables, Details beside the chain.
 * The desktop navigator is three rows, top to bottom — Figures, Panels,
 * Tables — so the page order reads as the dependency chain (a figure
 * depends on its panels, a panel on its tables; tables come from a CSV
 * file or typed by hand). The left cell of each row is the page tab; the
 * right cells jump straight to an entity (select + show its page).
 * Details is not in the chain — it stays beside the pages.
 * Phone tabs (SDK panes) keep their own Data | Panel | Figure | Details.
 *   - Figure: composition Canvas (CanvasPane).
 *   - Panels: one Panel at a time (PlotTypeNav | FigureViewer + Objects).
 *   - Tables: full-width DataTablePane (import, paste, sample, edit).
 */

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
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
import { gettext, interpolate } from "@scitex/sdk/ui/ts/_base/gettext.ts";

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
    placedFigures,
    selectedFigureId,
    selectFigure,
    datatableTabs,
    activeTabId,
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
      // A deep link names a figure to WORK on: land on the Figure canvas,
      // not the Panel viewer. Without this the arrival renders the raster in
      // the viewer while the canvas stays empty — the figure exists nowhere
      // the user can drag, arrange, or export it. Measured live 2026-10-22:
      // `?recipe=demo_first_figure.yaml` painted the viewer and left
      // OBJECTS at "No figures yet".
      setActiveTab("canvas");
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
  const dataActive = phone ? phonePane === "data" : activeTab === "data";
  const canvasActive = phone ? phonePane === "figure" : activeTab === "canvas";
  // Model-row context: the selected figure names the Panels row, and its
  // panel letter names the Tables row. Labels here are file basenames and
  // panel letters — the per-panel identity the canvas actually tracks.
  const selectedFig =
    placedFigures.find((f) => f.id === selectedFigureId) ?? null;
  const selectedFigLabel = selectedFig
    ? (selectedFig.path.split("/").pop() ?? selectedFig.path)
    : null;
  const selectedPanelLabel = selectedFig
    ? (selectedFig.panelLetter
      ? interpolate(gettext("Panel %s"), [selectedFig.panelLetter])
      : selectedFigLabel)
    : null;
  const tableList = Object.values(datatableTabs);
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
          only visible title (no duplication).

          SSoT yield (figrecipe-ssot-header-row-20261017): when the Django
          template rendered the shared SDK header row above the mount
          (header.stx-app-header[data-ssot]), that row owns the title/version
          chrome — rendering this one too would stack two identical titles.
          Yield it and portal the live picker into the server slot instead, so
          project switching keeps working with exactly one header. Re-queried
          every render, so a late-injected partial self-heals on the next
          state change. Without a server row (raw SPA fallback) the owned
          header renders exactly as before. */}
      {(() => {
        let ssotSlot: Element | null = null;
        try {
          ssotSlot = document.querySelector(
            "header.stx-app-header[data-ssot] .stx-app-header__slot--project-selector",
          );
        } catch {
          ssotSlot = null;
        }
        // Single picker element, rendered in exactly one place: portaled into
        // the server SSoT slot when present, else inside the owned fallback
        // header. One picker on the page, never two (hub ruling 9/16).
        const picker = <ProjectScopeSelector />;
        if (ssotSlot) return createPortal(picker, ssotSlot);
        return (
          <header className="stx-app-header">
            <span className="stx-app-header__title">{gettext("FigRecipe")}</span>
            {resolvedVersion && (
              <span className="stx-app-header__version">v{resolvedVersion}</span>
            )}
            <div className="stx-app-header__slot--project-selector">
              {picker}
            </div>
          </header>
        );
      })()}

      {/* ── Model rows: Figures / Panels / Tables ────────────
          Three stacked rows, top to bottom — not one flat tab row. Each
          row's left cell is the page tab; the right cells jump straight
          to an entity (select it and show its page). The middle and bottom
          rows name their parent ("Panels for Figure X", "Tables for
          Panel Y") so the dependency chain reads in place: a figure
          depends on its panels, a panel on its tables. */}
      <div className="inner-editor__tabs" role="tablist">
        <div className="inner-editor__tabrow">
          <button
            className={`inner-editor__tab inner-editor__tab--scope${activeTab === "canvas" ? " inner-editor__tab--active" : ""}`}
            onClick={() => selectTab("canvas")}
            role="tab"
            aria-selected={activeTab === "canvas"}
            title={gettext("Figures — a figure depends on its panels")}
          >
            <i className="fas fa-object-group" /> {gettext("Figures")}
          </button>
          <span className="inner-editor__tabitems">
            {placedFigures.length === 0 ? (
              <span className="inner-editor__tabhint">{gettext("No figures yet")}</span>
            ) : (
              placedFigures.map((f) => {
                const label = f.path.split("/").pop() ?? f.path;
                const selected = f.id === selectedFigureId;
                return (
                  <button
                    key={f.id}
                    type="button"
                    className={`inner-editor__tabitem${selected ? " inner-editor__tabitem--active" : ""}`}
                    aria-current={selected || undefined}
                    title={f.path}
                    onClick={() => {
                      selectFigure(f.id);
                      selectTab("canvas");
                    }}
                  >
                    {label}
                  </button>
                );
              })
            )}
          </span>
        </div>
        <div className="inner-editor__tabrow">
          <button
            className={`inner-editor__tab inner-editor__tab--scope${activeTab === "plot" ? " inner-editor__tab--active" : ""}`}
            onClick={() => selectTab("plot")}
            role="tab"
            aria-selected={activeTab === "plot"}
            title={gettext("Panels — a panel depends on its data")}
          >
            <i className="fas fa-chart-line" /> {gettext("Panels")}
          </button>
          {selectedFigLabel ? (
            <span className="inner-editor__tabscope">
              {interpolate(gettext("Panels for %s"), [selectedFigLabel])}
            </span>
          ) : null}
          <span className="inner-editor__tabitems">
            {placedFigures.length === 0 ? (
              <span className="inner-editor__tabhint">{gettext("No figures yet")}</span>
            ) : (
              placedFigures.map((f) => {
                const label = f.panelLetter
                  ? interpolate(gettext("Panel %s"), [f.panelLetter])
                  : (f.path.split("/").pop() ?? f.path);
                const selected = f.id === selectedFigureId;
                return (
                  <button
                    key={f.id}
                    type="button"
                    className={`inner-editor__tabitem${selected ? " inner-editor__tabitem--active" : ""}`}
                    aria-current={selected || undefined}
                    title={f.path}
                    onClick={() => {
                      selectFigure(f.id);
                      selectTab("plot");
                    }}
                  >
                    {label}
                  </button>
                );
              })
            )}
          </span>
        </div>
        <div className="inner-editor__tabrow">
          <button
            className={`inner-editor__tab inner-editor__tab--scope${activeTab === "data" ? " inner-editor__tab--active" : ""}`}
            onClick={() => selectTab("data")}
            role="tab"
            aria-selected={activeTab === "data"}
            title={gettext("Data — yaml, csv, npy files, or typed by hand")}
          >
            <i className="fas fa-table" /> {gettext("Data")}
          </button>
          {selectedPanelLabel ? (
            <span className="inner-editor__tabscope">
              {interpolate(gettext("Data for %s"), [selectedPanelLabel])}
            </span>
          ) : null}
          <span className="inner-editor__tabitems">
            {tableList.length === 0 ? (
              <span className="inner-editor__tabhint">{gettext("No tables")}</span>
            ) : (
              tableList.map((t) => {
                const selected = t.id === activeTabId;
                return (
                  <button
                    key={t.id}
                    type="button"
                    className={`inner-editor__tabitem${selected ? " inner-editor__tabitem--active" : ""}`}
                    aria-current={selected || undefined}
                    onClick={() => {
                      useEditorStore.setState({ activeTabId: t.id });
                      selectTab("data");
                    }}
                  >
                    {t.label}
                  </button>
                );
              })
            )}
          </span>
        </div>
      </div>

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
        <section className="editor-panel-page" {...paneAttrs("plot", gettext("Panel"), 2)}>
          {/* Plot type selector nav — fixed width, not resizable. */}
          <PlotTypeNav />
          {/* Rendered figure viewer — always expanded. */}
          <main className="split-pane split-pane-center">
            <FigureViewer onRequestDataTab={() => selectTab("data")} />
          </main>
        </section>
        {/* Composition canvas — always expanded. */}
        <main className="split-pane split-pane-center editor-figure-page" {...paneAttrs("figure", gettext("Figure"), 3)}>
          <CanvasPane
            active={canvasActive}
            onRequestPanelTab={() => selectTab("plot")}
            onRequestTablesTab={() => selectTab("data")}
          />
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
