/** App-local project selector — figrecipe's consumption of the shared
 * scitex-ui app-scope contract (operator ledger #48, #140-149).
 *
 * figrecipe declares `"scope": "project"` in its manifest; the scitex-app host
 * stamps `<meta name="stx-app-scope" content="project">` into the embedded
 * workspace page. This component consumes the SDK gate
 * (`mountProjectSelectorByScope` from `@scitex/ui/.../ts/shell`) instead of
 * forking the selector: it renders the app-local project picker ONLY when the
 * page is project-scoped, and renders nothing on user-scoped or standalone
 * pages (no marker -> the SDK returns null). The no-header-switcher ruling
 * holds structurally — the selector never reaches the global header.
 *
 * The SDK owns the PATTERN (the dropdown, the change event, the vocabulary,
 * the scope gate). figrecipe owns the DATA: which projects this app knows
 * about (its current working dir + its app-local recent-projects memory) and
 * what to do when the user picks one. That data is namespaced figrecipe-*
 * state, NOT the hub's global "Current Project", so figrecipe controls
 * "which project to target" independently of a forced global UI state.
 */

import { useEffect, useRef } from "react";
import {
  mountProjectSelectorByScope,
  PROJECT_SELECTOR_CHANGE,
} from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell";
import { setWorkingDir } from "../api/client";
import { useEditorStore } from "../store/useEditorStore";
import { buildProjectOptions } from "../store/projectOptions";
import {
  addRecentProject,
  getRecentProjects,
} from "../store/recentProjects";
import { rememberLastProject } from "../store/lastProjectMemory";

export function ProjectScopeSelector() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const { workingDir, loadFiles, loadPreview, loadDatatable, loadHitmap } =
    useEditorStore();

  // (Re)mount the scope-gated selector whenever the current project or the
  // recent list changes. The SDK is imperative and self-contained: it reads
  // the page's stx-app-scope marker and either mounts the shared
  // ProjectSelector into our container (project-scoped) or returns null
  // (user-scoped / standalone — nothing rendered, no global switcher).
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const { options, currentId } = buildProjectOptions(
      workingDir,
      getRecentProjects(),
    );
    el.innerHTML = "";
    const host = document.createElement("div");
    el.appendChild(host);

    const selector = mountProjectSelectorByScope({
      container: host,
      projects: options,
      current: currentId,
      placeholder: "Select project",
    });
    if (!selector) {
      // Not project-scoped (standalone / user-scoped host): the contract says
      // render nothing. No listener, no selector to destroy.
      host.remove();
      return;
    }

    const onChange = (e: Event) => {
      const { id } = (e as CustomEvent<{ id: string }>).detail || {};
      if (!id || id === workingDir) return;
      // Re-target the app's API client to the chosen project, remember it
      // app-locally, then reload its contents.
      setWorkingDir(id);
      addRecentProject(id);
      rememberLastProject(id);
      void loadFiles();
      void loadPreview();
      void loadHitmap();
      void loadDatatable();
    };
    // The SDK dispatches PROJECT_SELECTOR_CHANGE on its own container (the
    // host we supplied), so the listener lives on the host, not the selector.
    host.addEventListener(PROJECT_SELECTOR_CHANGE, onChange);

    return () => {
      host.removeEventListener(PROJECT_SELECTOR_CHANGE, onChange);
      try {
        selector.destroy();
      } catch {
        /* ignore */
      }
      el.innerHTML = "";
    };
  }, [workingDir, loadFiles, loadPreview, loadHitmap, loadDatatable]);

  return <div className="project-scope-selector" ref={containerRef} />;
}
