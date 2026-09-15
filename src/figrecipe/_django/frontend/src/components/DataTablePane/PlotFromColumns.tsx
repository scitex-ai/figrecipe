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

export function PlotFromColumns({ tab }: { tab: TabData }) {
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
          <select
            className="plot-from-columns__select"
            value={selection.x ?? ""}
            onChange={(e) =>
              setSelection((s) => ({ ...s, x: e.target.value || null }))
            }
          >
            <option value="">{gettext("Row number")}</option>
            {tab.columns.map((c) => (
              <option key={c.name} value={c.name}>
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
