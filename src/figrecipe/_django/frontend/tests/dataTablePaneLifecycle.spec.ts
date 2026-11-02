/** Sample worksheet rerenders must retain one grid and correct cell coordinates. */
import { act, createElement } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { parseCSV } from "@scitex/sdk/ui/react/app/data-table/utils/parseCSV";
import { DataTablePane } from "../src/components/DataTablePane/DataTablePane";
import { SAMPLE_TABLE_CSV } from "../src/components/DataTablePane/sampleData";
import { useEditorStore } from "../src/store/useEditorStore";
import type { TabData } from "../src/types/editor";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
let root: Root;
let mount: HTMLDivElement;
const original = useEditorStore.getState();
const sample = parseCSV(SAMPLE_TABLE_CSV);
const tab: TabData = {
  id: "sample-table", label: "Sample data", source: "import",
  columns: sample.columns.map((name) => ({name, dtype: name === "group" ? "string" : "float64"})),
  rows: sample.rows.map((row) => sample.columns.map((name) => row[name] ?? "")),
};

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("Unexpected network request"))));
  useEditorStore.setState({ ...original, datatableTabs: {[tab.id]: tab}, activeTabId: tab.id,
    highlightedDataRows: [], loadDatatable: async () => {}, refreshAfterMutation: async () => {},
    showToast: () => {},
  });
  mount = document.createElement("div");
  document.body.append(mount);
  root = createRoot(mount);
});
afterEach(() => {
  act(() => root.unmount());
  mount.remove();
  useEditorStore.setState(original, true);
  vi.unstubAllGlobals();
});

it("keeps the sample grid and every row/column coordinate stable across pane updates", async () => {
  await act(async () => { root.render(createElement(DataTablePane, {hideCollapse: true})); });
  const grid = mount.querySelector(".stx-app-data-table");
  for (let iteration = 0; iteration < 8; iteration++) {
    await act(async () => { useEditorStore.setState({highlightedDataRows: [iteration % tab.rows.length]}); });
    expect(mount.querySelectorAll(".stx-app-data-table")).toHaveLength(1);
    expect(mount.querySelector(".stx-app-data-table")).toBe(grid);
    expect(grid?.querySelectorAll("thead")).toHaveLength(1);
    expect(grid?.querySelectorAll("tbody tr")).toHaveLength(tab.rows.length);
    tab.rows.forEach((row, ri) => row.forEach((value, ci) => {
      expect(grid?.querySelectorAll(`td[data-row="${ri}"][data-col="${ci}"]`)).toHaveLength(1);
      expect(grid?.querySelector(`td[data-row="${ri}"][data-col="${ci}"]`)?.textContent).toBe(String(value));
    }));
  }
  expect(fetch).not.toHaveBeenCalled();
});

it("replaces the grid once when switching sample tables without leaving old coordinates", async () => {
  await act(async () => { root.render(createElement(DataTablePane, {hideCollapse: true})); });
  const other = {...tab, id: "other-table", label: "Other data", rows: tab.rows.slice(0, 2)};
  for (const selected of [other, tab, other, tab]) {
    await act(async () => {
      useEditorStore.setState({datatableTabs: {[tab.id]: tab, [other.id]: other}, activeTabId: selected.id});
    });
    expect(mount.querySelectorAll(".stx-app-data-table")).toHaveLength(1);
    expect(mount.querySelectorAll(".stx-app-data-table thead")).toHaveLength(1);
    expect(mount.querySelectorAll(".stx-app-data-table tbody tr")).toHaveLength(selected.rows.length);
  }
  expect(fetch).not.toHaveBeenCalled();
});
