/** Reactive undo/redo availability for toolbar disabled state.
 *
 * The history itself lives in module scope (useUndoRedo.ts); this hook
 * re-reads canUndo()/canRedo() after every completed render that could have
 * pushed or consumed a snapshot. Cheap enough (two integer compares) to run
 * on each placedFigures change — the only thing that moves the pointer.
 */
import { useEffect, useState } from "react";
import { canRedo, canUndo } from "./useUndoRedo";
import { useEditorStore } from "../store/useEditorStore";

export function useUndoRedoState(): { canUndo: boolean; canRedo: boolean } {
  const placedFigures = useEditorStore((s) => s.placedFigures);
  const [state, setState] = useState({ canUndo: false, canRedo: false });
  useEffect(() => {
    setState({ canUndo: canUndo(), canRedo: canRedo() });
  }, [placedFigures]);
  return state;
}
