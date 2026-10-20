/** Inspected details of the selected canvas element.
 *
 * Click-to-select names the element (Properties header already does that);
 * this section says what it IS: the value, the row/column (or cell), and
 * the series it belongs to. Matrix elements (imshow/matshow/pcolormesh)
 * additionally offer row/column steppers to walk the cells, since one
 * hitmap key covers the whole grid. Empty states name the gesture that
 * fills them.
 */

import { useEditorStore } from "../../store/useEditorStore";
import type { ElementDetails as Details } from "../../types/editor";
import { PropRow } from "./PropRow";
import { PropSection } from "./PropSection";
import { gettext, interpolate } from "@scitex/sdk/ui/ts/_base/gettext.ts";

function formatValue(value: Details["value"]): string | number {
  if (Array.isArray(value)) {
    return `(${value.map((v) => formatNumber(v)).join(", ")})`;
  }
  return formatNumber(value);
}

function formatNumber(value: number | null | undefined): string | number {
  if (value === null || value === undefined) return "—";
  if (typeof value !== "number" || !Number.isFinite(value)) return String(value);
  return Math.abs(value) >= 10000 || (Math.abs(value) < 0.001 && value !== 0)
    ? value.toExponential(3)
    : Math.round(value * 10000) / 10000;
}

export function ElementDetails() {
  const { selectedElement, elementDetails, elementCell, setElementCell } =
    useEditorStore();

  if (!selectedElement) return null;
  const details = elementDetails;

  // The fetch is in flight (or failed): say so instead of showing the
  // previous element's numbers under the new one's name.
  if (!details || details.element !== selectedElement) {
    return (
      <PropSection title={gettext("Details")}>
        <div className="properties-empty-hint">
          {gettext("Loading element details…")}
        </div>
      </PropSection>
    );
  }

  const isMatrix = details.shape != null;
  const shape = details.shape;
  const cellRow = elementCell?.row ?? details.row ?? null;
  const cellCol = elementCell?.col ?? details.col ?? null;

  const stepCell = (dRow: number, dCol: number) => {
    if (!shape) return;
    const row = Math.min(shape[0] - 1, Math.max(0, (cellRow ?? 0) + dRow));
    const col = Math.min(shape[1] - 1, Math.max(0, (cellCol ?? 0) + dCol));
    setElementCell(row, col);
  };

  return (
    <PropSection title={gettext("Details")}>
      {details.series != null && (
        <PropRow label={gettext("Series")} value={String(details.series)} />
      )}
      {details.value !== undefined && details.value !== null && (
        <PropRow label={gettext("Value")} value={formatValue(details.value)} />
      )}
      {details.row !== undefined && details.row !== null && (
        <PropRow
          label={gettext("Row")}
          value={
            details.row_label != null && details.row_label !== details.row
              ? `${details.row_label} (${details.row})`
              : String(details.row)
          }
        />
      )}
      {details.column !== undefined && details.column !== null && (
        <PropRow label={gettext("Column")} value={String(details.column)} />
      )}
      {details.index !== undefined &&
        details.index !== null &&
        details.index !== details.row && (
          <PropRow label={gettext("Index")} value={details.index} />
        )}
      {details.count !== undefined && details.count !== null && (
        <PropRow
          label={gettext("Points")}
          value={interpolate(gettext("%s points"), [details.count])}
        />
      )}
      {details.shape && (
        <PropRow
          label={gettext("Shape")}
          value={`${details.shape[0]} × ${details.shape[1]}`}
        />
      )}
      {details.minimum !== undefined && details.minimum !== null && (
        <PropRow
          label={gettext("Range")}
          value={`${formatNumber(details.minimum)} … ${formatNumber(details.maximum)}`}
        />
      )}
      {details.mean !== undefined && details.mean !== null && (
        <PropRow label={gettext("Mean")} value={formatNumber(details.mean)} />
      )}
      {details.levels && (
        <PropRow
          label={gettext("Levels")}
          value={details.levels.map((v) => formatNumber(v)).join(", ")}
        />
      )}
      {isMatrix && shape && (
        <div className="element-cell-stepper">
          <span className="property-label">{gettext("Cell")}</span>
          <div className="element-cell-stepper__controls">
            <button
              type="button"
              className="pane-header-btn"
              aria-label={gettext("Previous row")}
              title={gettext("Previous row")}
              onClick={() => stepCell(-1, 0)}
            >
              <i className="fas fa-chevron-up" aria-hidden="true" />
            </button>
            <button
              type="button"
              className="pane-header-btn"
              aria-label={gettext("Next row")}
              title={gettext("Next row")}
              onClick={() => stepCell(1, 0)}
            >
              <i className="fas fa-chevron-down" aria-hidden="true" />
            </button>
            <button
              type="button"
              className="pane-header-btn"
              aria-label={gettext("Previous column")}
              title={gettext("Previous column")}
              onClick={() => stepCell(0, -1)}
            >
              <i className="fas fa-chevron-left" aria-hidden="true" />
            </button>
            <button
              type="button"
              className="pane-header-btn"
              aria-label={gettext("Next column")}
              title={gettext("Next column")}
              onClick={() => stepCell(0, 1)}
            >
              <i className="fas fa-chevron-right" aria-hidden="true" />
            </button>
            <span className="element-cell-stepper__pos">
              {cellRow ?? "—"} / {cellCol ?? "—"}
            </span>
          </div>
          <div className="properties-empty-hint">
            {gettext("Tip: click another cell of the selected grid to inspect it.")}
          </div>
        </div>
      )}
    </PropSection>
  );
}
