/** Dotted column guides at 0.5 / 1.5 journal columns.
 *
 * Rendered INSIDE `.vis-canvas-container`, so the guides pan and zoom with
 * the page. Positions come from the single COLUMN_WIDTH_MM source shared
 * with the ruler column labels (which mark exactly these two columns).
 */

import { CANVAS_H, MM_PX } from "../../hooks/useSnap";
import { COLUMN_WIDTH_MM } from "./Rulers";

const GUIDED_COLUMNS = [0.5, 1.5];

export function ColumnGuides() {
  return (
    <>
      {GUIDED_COLUMNS.map((col) => (
        <div
          key={col}
          className="column-guide"
          data-col={col}
          aria-hidden="true"
          style={{ left: col * COLUMN_WIDTH_MM * MM_PX, height: CANVAS_H }}
        />
      ))}
    </>
  );
}
