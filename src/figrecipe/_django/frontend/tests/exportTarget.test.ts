import assert from "node:assert/strict";
import { exportTarget, exportFilename } from "../src/components/ExportDialog/exportTarget.ts";
import type { PlacedFigure } from "../src/types/editor.ts";
const panels = [
  { id: "a", path: "one.yaml", canvasKey: "first" },
  { id: "b", path: "two.yaml", canvasKey: "second" },
  { id: "c", path: "three.yaml", canvasKey: "first" },
] as PlacedFigure[];
assert.deepEqual(exportTarget(panels, "a").panels.map(p => p.id), ["a", "c"]);
assert.deepEqual(exportTarget(panels, "b"), {panels: [panels[1]], figureNumber: 2});
assert.deepEqual(exportTarget(panels, null).panels.map(p => p.id), ["a", "c"]);
assert.deepEqual(exportTarget([], null), {panels: [], figureNumber: 1});
assert.equal(exportFilename("ywatanabe/my project", 2, new Date("2026-11-02T04:05:06Z")), "my-project-Figure2-20261102T040506Z");
assert.equal(exportFilename(null, 1, new Date("2026-11-02T04:05:06Z")), "project-Figure1-20261102T040506Z");
console.log("Export target/filename: 6 checks passed");
