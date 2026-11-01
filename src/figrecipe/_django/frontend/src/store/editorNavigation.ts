/** Navigation removal changes this composition, never source files. */
import { setRecipe } from "../api/client";
import { useEditorStore } from "./useEditorStore";
import { pushUndoState } from "../hooks/useUndoRedo";
import { gettext } from "@scitex/sdk/ui/ts/_base/gettext.ts";
export function closeDataTab(id: string): boolean {
  const state = useEditorStore.getState();
  const tab = state.datatableTabs[id];
  if (!tab) return false;
  if (tab.source === "record") {
    state.showToast(gettext("Figure-recorded data is read-only. Take ownership before removing it."), "error");
    return false;
  }
  const tabs = { ...state.datatableTabs };
  delete tabs[id];
  useEditorStore.setState({ datatableTabs: tabs,
    activeTabId: state.activeTabId === id ? Object.keys(tabs)[0] ?? null : state.activeTabId });
  pushUndoState();
  return true;
}

/** A cached chunk carries its own API recipe and revision; never writes prefs. */
export function selectDataTab(id: string): void {
  const state = useEditorStore.getState();
  const tab = state.datatableTabs[id];
  if (!tab) return;
  if (tab.panelPath) setRecipe(tab.panelPath);
  const panel = state.placedFigures.find(figure => figure.path === tab.panelPath);
  useEditorStore.setState({activeTabId: id,
    ...(tab.panelPath ? {currentFile: tab.panelPath} : {}),
    ...(panel ? {selectedFigureId: panel.id, selectedFigureIds: [panel.id]} : {}),
    datatableRevision: tab.revision ?? null,
    elementDataMap: tab.elementDataMap ?? {},
    selectedElement: null, selectedBbox: null, highlightedDataRows: [],
  });
}
