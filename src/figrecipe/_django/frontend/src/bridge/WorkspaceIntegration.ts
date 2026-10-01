/**
 * FigRecipe workspace integration — connects bridge events to TS managers.
 *
 * Listens for CustomEvents emitted by the React bridge and calls
 * the appropriate workspace manager methods (VisEditor, file tree, etc.).
 */

import { onEvent } from "./EventBus";
import { switchRecipeFile } from "./MountPoint";
import { api } from "../api/client";
import { gettext, interpolate } from "@scitex/sdk/ui/ts/_base/gettext.ts";

/** Cleanup functions for event subscriptions. */
const cleanups: Array<() => void> = [];

/**
 * Wire bridge events to the VisEditor instance.
 * Call this after VisEditor is initialized.
 */
export function wireWorkspaceBridge(visEditor: any): void {
  // Clean up any previous wiring
  unwireWorkspaceBridge();

  // React → TS: File selected in figrecipe
  cleanups.push(
    onEvent("fileSelect", ({ path }) => {
      console.log("[Bridge] figrecipe file selected:", path);
      visEditor.treeSyncCoordinator?.syncTreeToFigure(path);
    }),
  );

  // React → TS: Element selected on canvas
  cleanups.push(
    onEvent("elementSelect", ({ elementId, bbox }) => {
      console.log("[Bridge] figrecipe element selected:", elementId);
      visEditor.propertiesManager?.updateSelection(elementId, bbox);
    }),
  );

  // React → TS: Property changed
  cleanups.push(
    onEvent("propertyChange", ({ key, value }) => {
      console.log("[Bridge] figrecipe property changed:", key, value);
      visEditor.updateStatusBar?.(interpolate(gettext("Property %s updated"), [key]));
    }),
  );

  // React → TS: Data changed
  cleanups.push(
    onEvent("dataChange", ({ columns, rowCount }) => {
      console.log(
        "[Bridge] figrecipe data changed:",
        columns.length,
        "cols,",
        rowCount,
        "rows",
      );
      visEditor.updateStatusBar?.(
        interpolate(gettext("Data: %s columns, %s rows"), [columns.length, rowCount]),
      );
    }),
  );

  // React → TS: Stat bracket added
  cleanups.push(
    onEvent("statBracketAdd", (bracket) => {
      console.log("[Bridge] figrecipe stat bracket added:", bracket.bracket_id);
      visEditor.updateStatusBar?.(interpolate(gettext("Stat bracket added: %s"), [bracket.stars]));
    }),
  );

  // TS → React: File tree click interception for recipe files
  document.addEventListener("click", handleFileTreeClick);
  cleanups.push(() => {
    document.removeEventListener("click", handleFileTreeClick);
  });
}

const RECIPE_EXTS = [".yaml", ".yml"];

function handleFileTreeClick(e: Event): void {
  const link = (e.target as Element)?.closest("[data-file-path]");
  if (!link) return;

  const path = link.getAttribute("data-file-path") || "";
  const ext = path.substring(path.lastIndexOf(".")).toLowerCase();

  if (RECIPE_EXTS.includes(ext)) {
    e.preventDefault();
    e.stopPropagation();
    switchRecipeFile(path);
  }
}

/**
 * Remove all bridge event subscriptions.
 */
export function unwireWorkspaceBridge(): void {
  for (const cleanup of cleanups) {
    cleanup();
  }
  cleanups.length = 0;
}

/**
 * Run a stat test via figrecipe's API and render the bracket.
 */
export async function runStatAndRenderBracket(
  testName: string,
  groups: Array<{ label: string; values: number[] }>,
  axIndex: number = 0,
  groupPositions?: { x1: number; x2: number },
): Promise<{
  result: any;
  annotation: any;
  bracket_id: string;
  preview: string;
}> {
  const { result, annotation } = await api.post<{ result: any; annotation: any }>(
    "stats/run", { test_name: testName, groups },
  );

  const { bracket_id, preview } = await api.post<{ bracket_id: string; preview: string }>(
    "stats/add_bracket", {
        annotation,
        ax_index: axIndex,
        group_positions: groupPositions,
    },
  );

  console.log(
    `[Bridge] Stat → bracket: ${testName} → ${annotation.stars} (${bracket_id})`,
  );

  return { result, annotation, bracket_id, preview };
}
