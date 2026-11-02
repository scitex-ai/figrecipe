/** Actual SDK React table keeps column names/children separate from role copy. */
import { act, createElement } from "react";
import { createRoot } from "react-dom/client";
import { expect, it } from "vitest";
import { DataTable } from "@scitex/sdk/ui/react/app/data-table/DataTable.tsx";
import {
  applyColumnHighlight,
  renderedColumnNodes,
} from "../src/components/DataTablePane/dataTableDom";

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

it("decorates real React headers with localized role attributes without changing children", async () => {
  const mount = document.createElement("div");
  document.body.append(mount);
  const root = createRoot(mount);
  const data = {columns: ["x", "y"], rows: [{x: 2, y: 4}, {x: 1, y: 3}]};
  try {
    await act(async () => root.render(createElement(DataTable, {data})));
    const x = mount.querySelector<HTMLElement>('th[data-col="0"]')!;
    const y = mount.querySelector<HTMLElement>('th[data-col="1"]')!;
    const originalChildren = [x.innerHTML, y.innerHTML];
    const highlights = [
      {index: 0, name: "x", role: "x" as const, preview: false},
      {index: 1, name: "y", role: "y" as const, preview: false},
    ];
    for (let i = 0; i < 3; i++) {
      applyColumnHighlight(renderedColumnNodes(mount), highlights, {x: "横軸", y: "縦軸"});
      expect([x.textContent, y.textContent]).toEqual(["x", "y"]);
      expect([x.innerHTML, y.innerHTML]).toEqual(originalChildren);
      expect([x.dataset.colAxisLabel, y.dataset.colAxisLabel]).toEqual(["横軸", "縦軸"]);
      expect([x.getAttribute("aria-label"), y.getAttribute("aria-label")]).toEqual(["x, 横軸", "y, 縦軸"]);
      expect(mount.querySelector('td[data-col="0"]')?.classList.contains("data-pane__col--x")).toBe(true);
      expect(mount.querySelector('td[data-col-axis-label]')).toBeNull();
    }
    await act(async () => x.dispatchEvent(new MouseEvent("click", {bubbles: true})));
    expect(mount.querySelector('td[data-row="0"][data-col="0"]')?.textContent).toBe("1");
    applyColumnHighlight(renderedColumnNodes(mount), []);
    expect(mount.querySelector("[data-col-axis-label]")).toBeNull();
    expect([x.getAttribute("aria-label"), y.getAttribute("aria-label")]).toEqual([null, null]);
    expect(data.columns).toEqual(["x", "y"]);
  } finally {
    act(() => root.unmount());
    mount.remove();
  }
});
