/** Data pane form: pick columns and plot them with the type chosen in the plot-type rail. */

import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import { useEditorStore } from "../../store/useEditorStore";
import type { TabData } from "../../types/editor";
import { PLOT_TYPES } from "../PlotTypeNav/PlotTypeNav";
import { showEditorPane } from "../mobilePanes";
import {
  buildPlotRequest,
  defaultColumnSelection,
  kindForFamily,
  reconcileSelection,
  type ColumnSelection,
} from "./columnPlotSelection";
import { cloneSelection } from "./dataTableEdit";
import { selectionAfterColumnClick } from "./dataColumnHighlight";
import { gettext, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

function kindLabel(id: string): string {
  switch (id) {
    case "line":
      return gettext("Line");
    case "scatter":
      return gettext("Scatter");
    case "bar":
      return gettext("Bar");
    case "histogram":
      return gettext("Histogram");
    case "boxplot":
      return gettext("Box");
    default:
      return id;
  }
}

/** A click on a table column, sent down by the Data pane. `nonce` re-arms a
 * repeat click on the column that is already selected. */
export interface ColumnClickCommand {
  name: string;
  nonce: number;
}

/** An explicit selection handed down by the Data pane (undo/redo).
 *
 * The table and its X/Y binding change in one history transition, so the form
 * must take the whole binding — not just "click column X" — and it must take it
 * AFTER the reconciler has looked at the restored column set (see the effect
 * order below). `nonce` re-arms an identical command. */
export interface SelectionCommand {
  selection: ColumnSelection;
  nonce: number;
}

interface PlotFromColumnsProps {
  tab: TabData;
  /** Set when the user clicks a table column header or cell. */
  columnCommand?: ColumnClickCommand | null;
  /** Set when the table and its binding were restored from history (undo/redo):
   *  applied after the reconciler, in the same commit as the table. */
  selectionCommand?: SelectionCommand | null;
  /** Mirrors the badge state up so the pane can highlight the table column each
   * badge names. Pass a stable setter (not an inline arrow): the pane's model
   * and this form must not ping-pong. */
  onSelectionChange?: (selection: ColumnSelection) => void;
}

export function PlotFromColumns({
  tab,
  columnCommand,
  selectionCommand,
  onSelectionChange,
}: PlotFromColumnsProps) {
  const { showToast, refreshAfterMutation, loadDatatable, plotFamily } =
    useEditorStore();
  const [selection, setSelection] = useState<ColumnSelection>(() =>
    defaultColumnSelection(tab.columns, tab.rows),
  );
  const [busy, setBusy] = useState(false);

  const columnKey = JSON.stringify(tab.columns.map((c) => c.name));
  useEffect(() => {
    setSelection((s) => reconcileSelection(s, tab.columns, tab.rows));
  }, [columnKey]); // the column set, not every row edit

  // A click in the table is a badge gesture: an X-column sets X, a Y-column
  // toggles Y — the same rule the chips and the select follow.
  useEffect(() => {
    if (!columnCommand) return;
    setSelection((s) => selectionAfterColumnClick(s, columnCommand.name));
  }, [columnCommand]);

  // An explicit binding from the pane (undo/redo). The table and its X/Y travel
  // through history as ONE transition, so this must be applied in the same
  // commit as the restored table — and AFTER the reconciler above, which looks at
  // the new column set and would otherwise drop a name the restore re-introduced.
  useEffect(() => {
    if (!selectionCommand) return;
    setSelection(cloneSelection(selectionCommand.selection));
  }, [selectionCommand]);

  useEffect(() => {
    onSelectionChange?.(selection);
  }, [selection, onSelectionChange]);

  const kind = kindForFamily(plotFamily);
  const request = useMemo(
    () => (kind ? buildPlotRequest(kind.id, selection) : null),
    [kind, selection],
  );

  const toggleY = (name: string) =>
    setSelection((s) => ({
      ...s,
      ys: s.ys.includes(name) ? s.ys.filter((y) => y !== name) : [...s.ys, name],
    }));

  const plot = async () => {
    if (!request) return;
    setBusy(true);
    try {
      await api.post("datatable/plot", request);
      await refreshAfterMutation();
      loadDatatable();
      showEditorPane("figure");
      showToast(interpolate(gettext("Plotted %s"), [request.columns.join(", ")]), "success");
    } catch (e) {
      showToast(interpolate(gettext("Plot failed: %s"), [e]), "error");
    } finally {
      setBusy(false);
    }
  };

  if (tab.columns.length === 0) return null;

  return (
    <form
      className="plot-from-columns"
      onSubmit={(e) => {
        e.preventDefault();
        void plot();
      }}
    >
      <p className="plot-from-columns__kind">
        {kind ? (
          <>
            <i
              className={PLOT_TYPES.find((p) => p.id === kind.family)?.icon}
              aria-hidden="true"
            />
            {interpolate(gettext("Plot type: %s"), [kindLabel(kind.id)])}
          </>
        ) : (
          gettext("This plot type cannot be drawn from table columns yet; pick Line, Scatter, Bar, Dist or Stats.")
        )}
      </p>

      {kind?.usesX && (
        <label className="plot-from-columns__group">
          <span className="plot-from-columns__legend">{gettext("X column")}</span>
          {/* data-column/data-role is how the Data pane finds the badge under
              the pointer and highlights the table column it names. */}
          <select
            className="plot-from-columns__select"
            data-role="x"
            data-column={selection.x ?? ""}
            value={selection.x ?? ""}
            onChange={(e) =>
              setSelection((s) => ({ ...s, x: e.target.value || null }))
            }
          >
            <option value="">{gettext("Row number")}</option>
            {tab.columns.map((c) => (
              <option key={c.name} value={c.name} data-role="x" data-column={c.name}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
      )}

      <fieldset className="plot-from-columns__group">
        <legend className="plot-from-columns__legend">{gettext("Y columns")}</legend>
        <div className="plot-from-columns__ys">
          {tab.columns
            .filter((c) => !kind?.usesX || c.name !== selection.x)
            .map((c) => (
              <button
                key={c.name}
                type="button"
                aria-pressed={selection.ys.includes(c.name)}
                /* The chip's visible text is the column name; the accessible
                   name adds the role it assigns, so the button still says what
                   it does when it is reached out of the legend's context
                   (WCAG 2.5.3: the name contains the visible text). */
                aria-label={interpolate(gettext("Y column: %s"), [c.name])}
                data-role="y"
                data-column={c.name}
                className={`plot-from-columns__chip${selection.ys.includes(c.name) ? " active" : ""}`}
                onClick={() => toggleY(c.name)}
              >
                {c.name}
              </button>
            ))}
        </div>
      </fieldset>

      <button
        type="submit"
        className="plot-from-columns__submit"
        disabled={!request || busy}
      >
        <i className="fas fa-chart-line" aria-hidden="true" />
        {busy ? gettext("Plotting…") : gettext("Plot")}
      </button>
    </form>
  );
}
