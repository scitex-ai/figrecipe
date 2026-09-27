/** Node test for the Objects tree model.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/objectTree.test.ts
 */

import assert from "node:assert/strict";
import {
  figureTreeItems,
  shortName,
} from "../src/components/ObjectTree/objectTree.ts";
import type { PlacedFigure } from "../src/types/editor.ts";

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

function figure(id: string, path: string, panelLetter?: string): PlacedFigure {
  return {
    id,
    path,
    x: 0,
    y: 0,
    previewImage: "",
    bboxes: {},
    imgSize: { width: 1, height: 1 },
    ...(panelLetter ? { panelLetter } : {}),
  };
}

ok("the tree shows file names in canvas order", () => {
  const items = figureTreeItems(
    [figure("a", "recipes/plot_plot.yaml"), figure("b", "recipes/plot_bar.yaml")],
    null,
  );
  assert.deepEqual(
    items.map((item) => item.label),
    ["plot_plot.yaml", "plot_bar.yaml"],
  );
});

ok("only the selected figure reads as selected", () => {
  const items = figureTreeItems(
    [figure("a", "plot_plot.yaml"), figure("b", "plot_bar.yaml")],
    "b",
  );
  assert.deepEqual(
    items.map((item) => item.selected),
    [false, true],
  );
});

ok("an empty canvas yields an empty tree, not a placeholder row", () => {
  assert.deepEqual(figureTreeItems([], null), []);
});

ok("the panel letter rides along when the figure carries one", () => {
  const items = figureTreeItems([figure("a", "plot_plot.yaml", "B")], "a");
  assert.equal(items[0].sublabel, "B");
});

ok("shortName keeps bare names untouched", () => {
  assert.equal(shortName("plot_plot.yaml"), "plot_plot.yaml");
});

console.log(`\n${passed} passed`);
