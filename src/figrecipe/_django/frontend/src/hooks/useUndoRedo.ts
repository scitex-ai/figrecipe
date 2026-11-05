/** Undo/Redo state history for canvas operations.
 *
 * Tracks snapshots of figure positions, placements, and overrides.
 * Max 50 history states. Push on every user action that modifies canvas.
 */

import { setRecipe } from "../api/client";
import { useEditorStore } from "../store/useEditorStore";
import type { PlacedFigure, StyleOverrides, TabData } from "../types/editor";

interface Snapshot {
  kind?: "canvas" | "data-navigation";
  placedFigures: PlacedFigure[];
  overrides: StyleOverrides;
  selectedFigureId: string | null;
  selectedFigureIds: string[];
  datatableTabs: Record<string, TabData>;
  activeTabId: string | null;
  datatableRevision: string | null;
}

const MAX_HISTORY = 50;

let history: Snapshot[] = [];
let pointer = -1;
let revision = 0;
const listeners = new Set<() => void>();
export function subscribeHistory(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
export const historyRevision = () => revision;
function publish() { revision++; listeners.forEach(listener => listener()); }


function takeSnapshot(): Snapshot {
  const { placedFigures, overrides, selectedFigureId, selectedFigureIds, datatableTabs, activeTabId, datatableRevision } = useEditorStore.getState();
  return {
    placedFigures: placedFigures.map((f) => ({ ...f })),
    overrides: { ...overrides },
    selectedFigureId, selectedFigureIds: [...selectedFigureIds],
    // Table edits replace values immutably; do not clone every data row for
    // every canvas drag. History stores membership and those immutable values.
    datatableTabs: {...datatableTabs}, activeTabId, datatableRevision,
  };
}

/** Push current state onto history stack. Call after every user action. */
export function prepareUndoState(): void {
  if (pointer < 0) { initUndoHistory(); return; }
  const kind = history[pointer].kind;
  history[pointer] = {...takeSnapshot(), kind};
}

export function pushUndoState(kind: Snapshot["kind"] = "canvas"): void {
  const snap = {...takeSnapshot(), kind};

  // Discard any redo states ahead of pointer
  history = history.slice(0, pointer + 1);
  history.push(snap);

  // Cap at max
  if (history.length > MAX_HISTORY) {
    history = history.slice(history.length - MAX_HISTORY);
  }
  pointer = history.length - 1;
  publish();
}

/** Undo — restore previous state. */
export function undo(): boolean {
  if (pointer <= 0) return false;
  const restoreData = history[pointer].kind === "data-navigation";
  pointer--;
  applySnapshot(history[pointer], restoreData);
  publish();
  return true;
}

/** Redo — restore next state. */
export function redo(): boolean {
  if (pointer >= history.length - 1) return false;
  pointer++;
  applySnapshot(history[pointer], history[pointer].kind === "data-navigation");
  publish();
  return true;
}

/** Check if undo/redo is available. */
export function canUndo(): boolean {
  return pointer > 0;
}

export function canRedo(): boolean {
  return pointer < history.length - 1;
}

/** Initialize history with current state. Call once on app load. */
export function initUndoHistory(): void {
  history = [takeSnapshot()];
  pointer = 0;
  publish();
}

function applySnapshot(snap: Snapshot, restoreData: boolean): void {
  const current = useEditorStore.getState();
  const sameDataRevision = current.datatableRevision === snap.datatableRevision;
  // Canvas history does not remove data that a later asynchronous read loaded.
  // Data navigation restores tab membership, preserving live values/locks.
  const tabs = restoreData && sameDataRevision
    ? Object.fromEntries(Object.entries(snap.datatableTabs).map(([id, tab]) =>
        [id, current.datatableTabs[id] ?? tab]))
    : current.datatableTabs;
  const panel = snap.placedFigures.find(figure => figure.id === snap.selectedFigureId);
  const related = Object.values(tabs).filter(tab => tab.panelPath === panel?.path);
  const activeId = restoreData ? snap.activeTabId
    : related.find(tab => tab.id === current.activeTabId)?.id ?? related[0]?.id ?? (panel ? null : current.activeTabId);
  const active = activeId ? tabs[activeId] : null;
  if (panel) setRecipe(panel.path);
  useEditorStore.setState({
    selectedFigureId: snap.selectedFigureId, selectedFigureIds: [...snap.selectedFigureIds],
    selectedElement: null, selectedBbox: null,
    ...(panel ? {currentFile: panel.path} : {}),
    datatableTabs: tabs, activeTabId: activeId,
    ...(active ? {datatableRevision: active.revision ?? current.datatableRevision, elementDataMap: active.elementDataMap ?? {}} : {}),
    placedFigures: snap.placedFigures.map(figure => ({...figure})),
    overrides: {...snap.overrides},
  });
}
