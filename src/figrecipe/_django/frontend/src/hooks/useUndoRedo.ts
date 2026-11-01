/** Undo/Redo state history for canvas operations.
 *
 * Tracks snapshots of figure positions, placements, and overrides.
 * Max 50 history states. Push on every user action that modifies canvas.
 */

import { useEditorStore } from "../store/useEditorStore";
import type { PlacedFigure, StyleOverrides, TabData } from "../types/editor";

interface Snapshot {
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
    datatableTabs: structuredClone(datatableTabs), activeTabId, datatableRevision,
  };
}

/** Push current state onto history stack. Call after every user action. */
export function pushUndoState(): void {
  const snap = takeSnapshot();

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
  pointer--;
  applySnapshot(history[pointer]);
  publish();
  return true;
}

/** Redo — restore next state. */
export function redo(): boolean {
  if (pointer >= history.length - 1) return false;
  pointer++;
  applySnapshot(history[pointer]);
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

function applySnapshot(snap: Snapshot): void {
  const current = useEditorStore.getState();
  // Never replace a newer server table with a stale local history snapshot.
  const sameDataRevision = current.datatableRevision === snap.datatableRevision;
  useEditorStore.setState({
    selectedFigureId: snap.selectedFigureId,
    selectedFigureIds: [...snap.selectedFigureIds],
    selectedElement: null, selectedBbox: null,
    ...(sameDataRevision ? {
      datatableTabs: Object.fromEntries(Object.entries(snap.datatableTabs).map(([id, tab]) =>
        [id, current.datatableTabs[id] ?? structuredClone(tab)])),
      activeTabId: snap.activeTabId,
    } : {}),
    placedFigures: snap.placedFigures.map((f) => ({ ...f })),
    overrides: { ...snap.overrides },
  });
}
