/** App-local project selector — figrecipe's consumption of the shared
 * scitex-ui ProjectSelector primitive (TODO 145 / 147).
 *
 * The SDK component owns the PATTERN (the dropdown, the change event, the
 * vocabulary). figrecipe owns the DATA: which projects this app knows about
 * (its current working dir + its app-local recent-projects memory) and what to
 * do when the user picks one. The data is namespaced figrecipe-* state, NOT the
 * hub's global "Current Project", so figrecipe controls "which project to
 * target" independently of a forced global UI state.
 *
 * On selection it re-targets the API client (setWorkingDir), records the
 * project in the app-local recent memory, and reloads the editor for it.
 */

import { useEffect, useRef } from "react";
import {
  ProjectSelector,
  PROJECT_SELECTOR_CHANGE,
} from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/app/project-selector";
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

  // (Re)build the selector whenever the current project or the recent list
  // changes. The SDK component is imperative, so we recreate it in place.
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

    let selector: ProjectSelector | null = null;
    try {
      selector = new ProjectSelector({
        container: host,
        projects: options,
        current: currentId,
        placeholder: "Select project",
      });
    } catch {
      // The SDK component throws if its container is missing; nothing to show.
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
    host.addEventListener(PROJECT_SELECTOR_CHANGE, onChange);

    return () => {
      host.removeEventListener(PROJECT_SELECTOR_CHANGE, onChange);
      try {
        selector?.destroy();
      } catch {
        /* ignore */
      }
      el.innerHTML = "";
    };
  }, [workingDir, loadFiles, loadPreview, loadHitmap, loadDatatable]);

  return <div className="project-scope-selector" ref={containerRef} />;
}
