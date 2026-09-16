/** FigrecipeEditor — mountable wrapper with event callback props.
 *
 * This is the public API for embedding figrecipe's React editor into
 * external applications (e.g. scitex-cloud) without an iframe.
 *
 * Usage:
 *   import { FigrecipeEditor } from "figrecipe-editor";
 *   <FigrecipeEditor
 *     apiBaseUrl="/vis/api/figrecipe"
 *     workingDir="/path/to/project"
 *     onFileSelect={(path) => console.log("file:", path)}
 *   />
 */

import { useEffect, useMemo } from "react";
import { InnerEditor } from "./InnerEditor";
import { setApiBase, setRecipe, setWorkingDir } from "./api/client";
import { useEditorStore } from "./store/useEditorStore";
import type { BBox, StatBracket } from "./types/editor";

export interface FigrecipeEditorProps {
  /** Base URL for the figrecipe API (e.g. "/vis/api/figrecipe"). */
  apiBaseUrl?: string;
  /** Project working directory (injected server-side). */
  workingDir?: string;
  /**
   * figrecipe's own version for the header badge. A host mounts via
   * #app-mount (no #root[data-version]), so pass the derived version
   * explicitly here; it takes precedence over the build-time
   * __FIGRECIPE_VERSION__ fallback. Omit to use the fallback.
   */
  appVersion?: string;
  /** Initial recipe path to load. */
  recipe?: string;
  /** Dark mode. */
  darkMode?: boolean;
  /** Called when a file is selected in the file tree. */
  onFileSelect?: (path: string) => void;
  /** Called when an element is clicked on the canvas. */
  onElementSelect?: (elementId: string, bbox: BBox | null) => void;
  /** Called when a property is changed. */
  onPropertyChange?: (key: string, value: unknown) => void;
  /** Called when data is imported/changed. */
  onDataChange?: (columns: string[], rowCount: number) => void;
  /** Called when a stat bracket is added. */
  onStatBracketAdd?: (bracket: StatBracket) => void;
}

export function FigrecipeEditor({
  apiBaseUrl,
  workingDir,
  appVersion,
  recipe,
  darkMode,
  onFileSelect,
  onElementSelect,
}: FigrecipeEditorProps) {
  // Configure API client before first render
  useMemo(() => {
    if (apiBaseUrl) setApiBase(apiBaseUrl);
    if (workingDir) setWorkingDir(workingDir);
    if (recipe) setRecipe(recipe);
  }, [apiBaseUrl, workingDir, recipe]);

  // Subscribe to store changes and forward as callbacks
  useEffect(() => {
    if (!onFileSelect && !onElementSelect) return;

    const unsub = useEditorStore.subscribe((state, prevState) => {
      if (onFileSelect && state.currentFile !== prevState.currentFile) {
        if (state.currentFile) onFileSelect(state.currentFile);
      }
      if (
        onElementSelect &&
        state.selectedElement !== prevState.selectedElement
      ) {
        if (state.selectedElement) {
          onElementSelect(state.selectedElement, state.selectedBbox);
        }
      }
    });

    return unsub;
  }, [onFileSelect, onElementSelect]);

  // Apply dark mode prop
  useEffect(() => {
    if (darkMode !== undefined) {
      useEditorStore.getState().setDarkMode(darkMode);
    }
  }, [darkMode]);

  return <InnerEditor embedded appVersion={appVersion} />;
}

// Re-export types for consumers
export type { BBox, StatBracket, CallRecord } from "./types/editor";
export { useEditorStore } from "./store/useEditorStore";
