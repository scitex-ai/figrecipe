/**
 * FigRecipe mount point — React root + fetch override.
 *
 * Uses the generic bridge runtime from scitex-ui.
 */

import React from "react";
import {
  installFetchOverride,
  mountReactApp,
  unmountReactApp,
} from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/bridge";
import type {
  BridgeConfig,
  BridgeMountOptions,
} from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/bridge";
import { FigrecipeEditor } from "../FigrecipeEditor";
import { emitEvent } from "./EventBus";
import { resolveAppVersion } from "./appVersion";


/**
 * Figrecipe API endpoint prefixes that should be routed through Django.
 * Only these paths get rewritten — all other fetches pass through unchanged.
 */
const BRIDGE_CONFIG: BridgeConfig = {
  slug: "figrecipe",
  mountId: "app-mount",
  apiPaths: [
    "/preview",
    "/hitmap",
    "/update",
    "/save",
    "/restore",
    "/switch_theme",
    "/list_themes",
    "/download/",
    "/datatable/",
    "/get_axes_positions",
    "/update_axes_position",
    "/update_legend_position",
    "/update_label",
    "/update_call",
    "/get_labels",
    "/calls",
    "/stats/",
    "/api/files",
    "/api/switch",
    "/api/compose",
    "/api/delete",
    "/api/rename",
    "/api/file-tree",
    "/api/git/",
  ],
  fileExtensions: [".yaml", ".yml"],
};

/**
 * Mount the figrecipe editor into the given container.
 */
export function mountFigrecipeEditor(options: BridgeMountOptions): void {
  installFetchOverride(BRIDGE_CONFIG);

  const apiBaseUrl = `/apps/${BRIDGE_CONFIG.slug}/${BRIDGE_CONFIG.slug}`;

  mountReactApp(
    options.container,
    React.createElement(FigrecipeEditor, {
      apiBaseUrl,
      workingDir: options.workingDir,
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
  import("../index").then(({ useEditorStore }) => {
    const params = new URLSearchParams(window.location.search);
    params.set("recipe", path);
    params.set("mode", "embedded");
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState(null, "", newUrl);

    const store = useEditorStore.getState();
    store.loadPreview();
    store.loadHitmap();
    store.loadDatatable();
  });
}

/**
 * Unmount the figrecipe editor and clean up.
 */
export function unmountFigrecipeEditor(): void {
  unmountReactApp();
}
