/** Node test for matrix-cell hit resolution on hitmap image/mesh elements.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/matrixCell.test.ts
 *
 * One hitmap key covers a whole imshow/matshow/pcolormesh grid, so picking a
 * cell is geometry (click point -> bbox fraction -> row/col), not colour.
 * The module must survive a missing bbox/shape, a degenerate box, clicks
 * outside the element, and non-matrix element types — a wrong cell would
 * inspect (and let the user edit through) data they did not click.
 */

import assert from "node:assert/strict";

import {
  cellAtPoint,
  isMatrixElement,
} from "../src/components/Canvas/matrixCell.ts";

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

console.log("matrixCell:");

const bbox = { x: 100, y: 50, width: 400, height: 300 };
const imgSize = { width: 800, height: 600 };
const box = { width: 800, height: 600 };
const shape = { rows: 3, cols: 4 };

ok("only image and quadmesh colorMap types are matrix elements", () => {
  // Arrange
  const colorMap = {
    ax0_image0: { type: "image" },
    ax0_quadmesh0: { type: "quadmesh" },
    ax0_bar1: { type: "bar" },
  };
  // Act + Assert
  assert.equal(isMatrixElement(colorMap, "ax0_image0"), true);
  assert.equal(isMatrixElement(colorMap, "ax0_quadmesh0"), true);
  assert.equal(isMatrixElement(colorMap, "ax0_bar1"), false);
});

ok("a click in the top-left of the bbox is row 0, col 0", () => {
  // Arrange
  const point = { x: 101, y: 51 };
  // Act
  const cell = cellAtPoint(bbox, imgSize, box, point, shape);
  // Assert
  assert.deepEqual(cell, { row: 0, col: 0 });
});

ok("a click maps to the right cell of a 3x4 grid", () => {
  // Arrange: centre of cell (row 2, col 3): relX in [0.75, 1), relY in [2/3, 1)
  const point = { x: 100 + 0.8 * 400, y: 50 + 0.7 * 300 };
  // Act
  const cell = cellAtPoint(bbox, imgSize, box, point, shape);
  // Assert
  assert.deepEqual(cell, { row: 2, col: 3 });
});

ok("the displayed scale cancels out (zoomed overlay)", () => {
  // Arrange: same cell, overlay drawn at half size
  const halfBox = { width: 400, height: 300 };
  const point = { x: (100 + 0.8 * 400) / 2, y: (50 + 0.7 * 300) / 2 };
  // Act
  const cell = cellAtPoint(bbox, imgSize, halfBox, point, shape);
  // Assert
  assert.deepEqual(cell, { row: 2, col: 3 });
});

ok("a click outside the element bbox is no cell", () => {
  // Arrange
  const point = { x: 10, y: 10 };
  // Act
  const cell = cellAtPoint(bbox, imgSize, box, point, shape);
  // Assert
  assert.equal(cell, null);
});

ok("a missing shape or bbox is no cell, not a crash", () => {
  // Arrange
  const point = { x: 200, y: 200 };
  // Act + Assert
  assert.equal(cellAtPoint(bbox, imgSize, box, point, null), null);
  assert.equal(cellAtPoint(null, imgSize, box, point, shape), null);
  assert.equal(
    cellAtPoint(bbox, imgSize, box, point, { rows: 0, cols: 4 }),
    null,
  );
});

ok("unknown keys and missing colorMaps are not matrix elements", () => {
  // Act + Assert
  assert.equal(isMatrixElement({}, "ax0_image0"), false);
  assert.equal(isMatrixElement(null, "ax0_image0"), false);
  assert.equal(isMatrixElement({ ax0_image0: { type: "image" } }, null), false);
});

console.log(`\n${passed} passed`);
