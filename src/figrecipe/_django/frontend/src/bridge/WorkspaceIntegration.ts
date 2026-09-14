/**
 * FigRecipe workspace integration — connects bridge events to TS managers.
 *
 * Listens for CustomEvents emitted by the React bridge and calls
 * the appropriate workspace manager methods (VisEditor, file tree, etc.).
 */

import { onEvent } from "./EventBus";
import { switchRecipeFile } from "./MountPoint";
import { csrfToken } from "../api/client";

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
      visEditor.updateStatusBar?.(`Property ${key} updated`);
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
        `Data: ${columns.length} columns, ${rowCount} rows`,
      );
    }),
  );

  // React → TS: Stat bracket added
  cleanups.push(
    onEvent("statBracketAdd", (bracket) => {
      console.log("[Bridge] figrecipe stat bracket added:", bracket.bracket_id);
      visEditor.updateStatusBar?.(`Stat bracket added: ${bracket.stars}`);
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
  const statResp = await fetch("/apps/figrecipe/figrecipe/stats/run", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
    body: JSON.stringify({ test_name: testName, groups }),
  });
  const { result, annotation } = await statResp.json();

  const bracketResp = await fetch(
    "/apps/figrecipe/figrecipe/stats/add_bracket",
    {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
      body: JSON.stringify({
        annotation,
        ax_index: axIndex,
        group_positions: groupPositions,
      }),
    },
  );
  const { bracket_id, preview } = await bracketResp.json();

  console.log(
    `[Bridge] Stat → bracket: ${testName} → ${annotation.stars} (${bracket_id})`,
  );

  return { result, annotation, bracket_id, preview };
}
