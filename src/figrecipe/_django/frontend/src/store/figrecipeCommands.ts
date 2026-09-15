/** FigRecipe's named commands on the shared scitex-ui keymap registry.
 *
 * The operator's beta boundary: a GUI button, a keyboard chord, and an agent
 * dispatch all converge on ONE registered command action — none calls app code
 * directly. This replaces figrecipe's old manual `window` keydown handler
 * (the "another shortcut system" the hub migration exists to remove) with the
 * scitex-ui CommandRegistry + Keymap page-mode.
 *
 * scitex-ui 0.22.0: `ts/shell/keymap` (CommandRegistry, Keymap). The keymap
 * gates by an `inInput` flag per binding (inside an input only inInput=true
 * bindings fire), and treats Ctrl (`C-`) and Meta (`M2-`) as DISTINCT chords,
 * so a cross-platform "Ctrl/Cmd" command is bound under BOTH. The key token a
 * binding must match is what `eventToChord` produces from KeyboardEvent.key,
 * which normalizes only the `NAMED_KEYS` aliases — so Delete binds as "del",
 * Escape as "esc", but Backspace and the Arrow keys keep their raw key strings
 * ("Backspace", "ArrowUp", ...) to match the event verbatim.
 */

import {
  CommandRegistry,
  Keymap,
} from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/shell/keymap";
import { MM_PX } from "../hooks/useSnap";
import { redo, undo } from "../hooks/useUndoRedo";
import { useEditorStore } from "./useEditorStore";

/** The figrecipe page/app mode. Mode-scoped commands are live only in it. */
export const FIGRECIPE_MODE = "figrecipe";

/** Stable command IDs — the contract buttons + keyboard + agents key off. */
export const CMD = {
  save: "figrecipe.save",
  undo: "figrecipe.undo",
  redo: "figrecipe.redo",
  copy: "figrecipe.copy",
  paste: "figrecipe.paste",
  deselect: "figrecipe.deselect",
  selectAll: "figrecipe.select-all",
  removeSelected: "figrecipe.remove-selected",
  nudgeUp: "figrecipe.nudge.up",
  nudgeDown: "figrecipe.nudge.down",
  nudgeLeft: "figrecipe.nudge.left",
  nudgeRight: "figrecipe.nudge.right",
  nudgeUpShift: "figrecipe.nudge.up-shift",
  nudgeDownShift: "figrecipe.nudge.down-shift",
  nudgeLeftShift: "figrecipe.nudge.left-shift",
  nudgeRightShift: "figrecipe.nudge.right-shift",
  group: "figrecipe.group",
  ungroup: "figrecipe.ungroup",
  toggleSnap: "figrecipe.toggle-snap",
  toggleRulers: "figrecipe.toggle-rulers",
  zoomToFit: "figrecipe.zoom-to-fit",
  toggleHitmap: "figrecipe.toggle-hitmap",
  restore: "figrecipe.restore",
  export: "figrecipe.export",
} as const;
export type CommandId = (typeof CMD)[keyof typeof CMD];

const NUDGE_MM = 1; // 1mm per arrow press
const NUDGE_SHIFT_MM = 5; // 5mm with Shift held

type State = ReturnType<typeof useEditorStore.getState>;

function nudge(dxPx: number, dyPx: number): void {
  const st = useEditorStore.getState();
  const fig = st.placedFigures.find((f) => f.id === st.selectedFigureId);
  if (!fig) return;
  st.moveFigure(fig.id, fig.x + dxPx, fig.y + dyPx);
}

function actions(): Record<CommandId, () => void> {
  const S = (): State => useEditorStore.getState();
  return {
    [CMD.save]: () => S().save(),
    [CMD.undo]: () => undo(),
    [CMD.redo]: () => redo(),
    [CMD.copy]: () => {
      // Preserve the old guard: if the user has a text selection, let the
      // browser copy the text; otherwise copy the selected figure.
      const sel = window.getSelection?.();
      if (sel && sel.toString().length > 0) return;
      S().copyFigure();
    },
    [CMD.paste]: () => S().pasteFigure(),
    [CMD.deselect]: () => {
      S().selectFigure(null);
      S().selectElement(null);
    },
    [CMD.selectAll]: () => {
      const ids = S().placedFigures.map((f) => f.id);
      useEditorStore.setState({
        selectedFigureIds: ids,
        selectedFigureId: ids.length > 0 ? ids[0] : null,
      });
    },
    [CMD.removeSelected]: () => {
      const st = S();
      const ids =
        st.selectedFigureIds.length > 0
          ? [...st.selectedFigureIds]
          : st.selectedFigureId
            ? [st.selectedFigureId]
            : [];
      if (ids.length === 0) return;
      for (const id of ids) useEditorStore.getState().removeFigure(id);
    },
    [CMD.nudgeUp]: () => nudge(0, -NUDGE_MM * MM_PX),
    [CMD.nudgeDown]: () => nudge(0, NUDGE_MM * MM_PX),
    [CMD.nudgeLeft]: () => nudge(-NUDGE_MM * MM_PX, 0),
    [CMD.nudgeRight]: () => nudge(NUDGE_MM * MM_PX, 0),
    [CMD.nudgeUpShift]: () => nudge(0, -NUDGE_SHIFT_MM * MM_PX),
    [CMD.nudgeDownShift]: () => nudge(0, NUDGE_SHIFT_MM * MM_PX),
    [CMD.nudgeLeftShift]: () => nudge(-NUDGE_SHIFT_MM * MM_PX, 0),
    [CMD.nudgeRightShift]: () => nudge(NUDGE_SHIFT_MM * MM_PX, 0),
    [CMD.group]: () => {
      const st = S();
      const ids =
        st.selectedFigureIds.length >= 2
          ? st.selectedFigureIds
          : st.placedFigures.map((f) => f.id);
      if (ids.length >= 2) st.groupFigures(ids);
    },
    [CMD.ungroup]: () => {
      const st = S();
      const sel = st.placedFigures.find((f) => f.id === st.selectedFigureId);
      if (sel?.groupId) st.ungroupFigures(sel.groupId);
    },
    [CMD.toggleSnap]: () => S().toggleSnap(),
    [CMD.toggleRulers]: () => S().toggleRulers(),
    [CMD.zoomToFit]: () => S().zoomControls?.zoomToFit(),
    [CMD.toggleHitmap]: () => S().toggleHitmap(),
    [CMD.restore]: () => S().restore(),
    [CMD.export]: () => {
      // No-op action: Export is opened from a dialog (ExportDialog) whose own
      // confirm performs the compose/download. Registered so the Export button
      // can converge on the same named command; the dialog wiring is unchanged.
    },
  };
}

let registry: CommandRegistry | null = null;
let keymap: Keymap | null = null;
let detach: (() => void) | null = null;

/** Build (once) the figrecipe CommandRegistry + Keymap with all bindings. */
function ensure(): Keymap {
  if (keymap) return keymap;

  const reg = new CommandRegistry();
  for (const [id, action] of Object.entries(actions())) {
    reg.set({ id, action, modes: new Set([FIGRECIPE_MODE]), group: "FigRecipe" });
  }

  const km = new Keymap({ registry: reg });
  // `inInput` mirrors the old manual handler exactly: save/undo/redo/Escape
  // fired even while typing; copy/paste/select-all/delete/arrows/group did not.
  const bindMod = (seq: string, id: CommandId, inInput = false): void => {
    km.bind(FIGRECIPE_MODE, `C-${seq}`, id, inInput);
    km.bind(FIGRECIPE_MODE, `M2-${seq}`, id, inInput);
  };

  // mod = Ctrl on Linux/Win, Cmd on macOS -> bind both C- and M2- (the keymap
  // distinguishes them; the old handler matched `ctrlKey || metaKey`).
  bindMod("s", CMD.save, true); // Ctrl/Cmd+S — save (fired in inputs before too)
  bindMod("z", CMD.undo, true); // Ctrl/Cmd+Z — undo
  bindMod("S-z", CMD.redo, true); // Ctrl/Cmd+Shift+Z — redo
  bindMod("c", CMD.copy); // Ctrl/Cmd+C — copy figure (not in inputs)
  bindMod("v", CMD.paste); // Ctrl/Cmd+V — paste
  bindMod("a", CMD.selectAll); // Ctrl/Cmd+A — select all
  bindMod("g", CMD.group); // Ctrl/Cmd+G — group
  // ungroup + toggleSnap: the old manual handler had NO isEditing guard on
  // these (they fired even while typing), so preserve that -> inInput=true.
  bindMod("S-g", CMD.ungroup, true); // Ctrl/Cmd+Shift+G — ungroup
  bindMod("S-s", CMD.toggleSnap, true); // Ctrl/Cmd+Shift+S — toggle snap

  // Single-chord (no mod) bindings — bind the exact key token eventToChord yields.
  km.bind(FIGRECIPE_MODE, "esc", CMD.deselect, true); // Escape fired in inputs
  km.bind(FIGRECIPE_MODE, "del", CMD.removeSelected);
  km.bind(FIGRECIPE_MODE, "Backspace", CMD.removeSelected);

  // Arrow nudge (1mm) and Shift+Arrow (5mm). Key tokens are the RAW event keys
  // because "ArrowUp"/"Backspace" are not in the keymap's NAMED_KEYS aliases.
  km.bind(FIGRECIPE_MODE, "ArrowUp", CMD.nudgeUp);
  km.bind(FIGRECIPE_MODE, "ArrowDown", CMD.nudgeDown);
  km.bind(FIGRECIPE_MODE, "ArrowLeft", CMD.nudgeLeft);
  km.bind(FIGRECIPE_MODE, "ArrowRight", CMD.nudgeRight);
  km.bind(FIGRECIPE_MODE, "S-ArrowUp", CMD.nudgeUpShift);
  km.bind(FIGRECIPE_MODE, "S-ArrowDown", CMD.nudgeDownShift);
  km.bind(FIGRECIPE_MODE, "S-ArrowLeft", CMD.nudgeLeftShift);
  km.bind(FIGRECIPE_MODE, "S-ArrowRight", CMD.nudgeRightShift);

  km.activateMode(FIGRECIPE_MODE);
  keymap = km;
  registry = reg;
  return km;
}

/** Run a named command (the button/agent path — converges with the keyboard). */
export function runFigCommand(id: CommandId): void {
  ensure();
  registry?.run(id, { via: "button" });
}

/** Mount the shared keymap for the figrecipe page-mode. Returns a detacher. */
export function attachFigKeymap(target: EventTarget = document): () => void {
  const km = ensure();
  if (detach) return detach;
  detach = km.attach(target);
  return detach;
}
