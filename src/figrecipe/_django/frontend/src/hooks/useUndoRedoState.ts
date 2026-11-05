/** Availability follows completed history operations, including Data tabs. */
import { useSyncExternalStore } from "react";
import { canRedo, canUndo, historyRevision, subscribeHistory } from "./useUndoRedo";
export function useUndoRedoState(): { canUndo: boolean; canRedo: boolean } {
  useSyncExternalStore(subscribeHistory, historyRevision, historyRevision);
  return { canUndo: canUndo(), canRedo: canRedo() };
}
