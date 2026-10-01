/**
 * FigRecipe mount point — React root and instance-local API routing.
 *
 * Uses the generic bridge runtime from scitex-ui.
 */

import React from "react";
import {
  mountReactApp,
  unmountReactApp,
} from "@scitex/sdk/ui/react/app/bridge";
import type {
  BridgeMountOptions,
} from "@scitex/sdk/ui/react/app/bridge";
import { FigrecipeEditor } from "../FigrecipeEditor";
import { emitEvent } from "./EventBus";
import { resolveAppVersion } from "./appVersion";
import { resolveApiMount } from "./mountRouting";
import { retireApiSession, setApiBase, setProject, setRecipe, setWorkingDir } from "../api/client";
import { useEditorStore, resetEditorWorkspace } from "../store/useEditorStore";
import { initUndoHistory } from "../hooks/useUndoRedo";

let mountedContainer: HTMLElement | null = null;

export interface FigrecipeMountOptions extends BridgeMountOptions {
  /** Trusted host declaration. Otherwise read data-stx-mount on the container. */
  apiBaseUrl?: string;
  projectId?: string;
  projectName?: string;
}

/**
 * Mount the figrecipe editor into the given container.
 */
export function mountFigrecipeEditor(options: FigrecipeMountOptions): void {
  const apiBaseUrl = resolveApiMount(options.container, options.apiBaseUrl);
  unmountFigrecipeEditor();
  retireApiSession();
  resetEditorWorkspace();
  mountedContainer = options.container;

  mountReactApp(
    options.container,
    React.createElement(FigrecipeEditor, {
      apiBaseUrl,
      workingDir: options.workingDir,
      projectId: options.projectId,
      projectName: options.projectName,
      // Version for the header badge: read the stable `data-app-version` mount
      // attribute the host stamps generically (present on the Hub #app-mount
      // path), then fall back to figrecipe's own build-time constant. On the
      // Hub bundle the build-time constant is undefined, so without the
      // attribute read the badge fell back to "" (no .stx-app-header__version).
      // Omitted entirely when neither source has a value -> InnerEditor runs
      // its own resolution chain (prop -> #root[data-version] -> build const).
      appVersion: resolveAppVersion(
        options.container.getAttribute("data-app-version"),
      ),
      recipe: options.initialFile,
      darkMode: options.darkMode,
      onFileSelect: (path: string) => {
        emitEvent("fileSelect", { path });
      },
      onElementSelect: (elementId: string, bbox: any) => {
        emitEvent("elementSelect", { elementId, bbox });
      },
      onPropertyChange: (key: string, value: unknown) => {
        emitEvent("propertyChange", { key, value });
      },
      onDataChange: (columns: string[], rowCount: number) => {
        emitEvent("dataChange", { columns, rowCount });
      },
      onStatBracketAdd: (bracket: any) => {
        emitEvent("statBracketAdd", bracket);
      },
    }),
  );
}

/**
 * Switch the loaded recipe file (called from TS side).
 */
export function switchRecipeFile(path: string): void {
  setRecipe(path);
  const params = new URLSearchParams(window.location.search);
  params.set("recipe", path);
  params.set("mode", "embedded");
  const newUrl = `${window.location.pathname}?${params.toString()}`;
  window.history.replaceState(null, "", newUrl);

  void useEditorStore.getState().switchFile(path);
}

/**
 * Unmount the figrecipe editor and clean up.
 */
export function unmountFigrecipeEditor(): void {
  if (!mountedContainer) return;
  unmountReactApp(mountedContainer);
  mountedContainer = null;
  retireApiSession();
  setApiBase("");
  setWorkingDir("");
  setRecipe("");
  setProject("");
  resetEditorWorkspace();
  initUndoHistory();
}
