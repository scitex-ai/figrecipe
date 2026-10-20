/** Matrix-cell hit resolution for hitmap image/mesh elements.
 *
 * An imshow/matshow/pcolormesh element is ONE hitmap key for the whole cell
 * grid, so picking a cell needs geometry, not colour: the click point (CSS
 * px inside the overlay box) is mapped into figure-image px via the
 * displayed scale, then into the element bbox's fraction, then into a
 * row/column via the matrix shape the element_details endpoint reported.
 * Fractions cancel the canvas zoom — the overlay box and the bboxes scale
 * together. Matrix row 0 is the TOP (imshow origin upper, y grows down),
 * which is also the overlay's y direction, so no flip is needed.
 *
 * React-free so it runs under `node --experimental-strip-types` — see
 * tests/matrixCell.test.ts.
 */

export interface Box {
  width: number;
  height: number;
}

export interface BBoxRect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Point {
  x: number;
  y: number;
}

export interface MatrixShape {
  rows: number;
  cols: number;
}

export interface CellRef {
  row: number;
  col: number;
}

/** Hitmap colorMap types that depict a matrix cell grid. */
const MATRIX_TYPES = new Set(["image", "quadmesh"]);

/** Whether a hitmap element key depicts matrix cells (needs row/col). */
export function isMatrixElement(
  colorMap: Record<string, unknown> | null | undefined,
  key: string | null | undefined,
): boolean {
  if (!key || !colorMap) return false;
  const type = (colorMap[key] as { type?: unknown } | undefined)?.type;
  return typeof type === "string" && MATRIX_TYPES.has(type);
}

/** Cell under a CSS-px point, or null when outside the element / unknown. */
export function cellAtPoint(
  bbox: BBoxRect | null | undefined,
  imgSize: Box | null | undefined,
  box: Box | null | undefined,
  point: Point | null | undefined,
  shape: MatrixShape | null | undefined,
): CellRef | null {
  if (!bbox || !imgSize || !box || !point || !shape) return null;
  if (!(bbox.width > 0) || !(bbox.height > 0)) return null;
  if (!(imgSize.width > 0) || !(imgSize.height > 0)) return null;
  if (!(box.width > 0) || !(box.height > 0)) return null;
  if (!Number.isFinite(point.x) || !Number.isFinite(point.y)) return null;
  if (
    !Number.isInteger(shape.rows) ||
    !Number.isInteger(shape.cols) ||
    shape.rows <= 0 ||
    shape.cols <= 0
  )
    return null;
  // CSS px -> figure-image px (the overlay stretches over the image).
  const imgX = (point.x * imgSize.width) / box.width;
  const imgY = (point.y * imgSize.height) / box.height;
  const relX = (imgX - bbox.x) / bbox.width;
  const relY = (imgY - bbox.y) / bbox.height;
  if (relX < 0 || relY < 0 || relX >= 1 || relY >= 1) return null;
  return {
    row: Math.floor(relY * shape.rows),
    col: Math.floor(relX * shape.cols),
  };
}
