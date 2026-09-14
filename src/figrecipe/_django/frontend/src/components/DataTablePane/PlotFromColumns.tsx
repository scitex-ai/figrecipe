/** Data pane form: pick a plot type and columns, then plot them onto the figure. */

import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import { useEditorStore } from "../../store/useEditorStore";
import type { TabData } from "../../types/editor";
import { PLOT_TYPES } from "../PlotTypeNav/PlotTypeNav";
import {
  DATA_PLOT_KINDS,
  buildPlotRequest,
  defaultColumnSelection,
  plotKind,
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
  const { showToast, refreshAfterMutation, loadDatatable } = useEditorStore();
  const [kindId, setKindId] = useState(DATA_PLOT_KINDS[0].id);
  const [selection, setSelection] = useState<ColumnSelection>(() =>
    defaultColumnSelection(tab.columns, tab.rows),
  );
  const [busy, setBusy] = useState(false);

  const columnKey = JSON.stringify(tab.columns.map((c) => c.name));
  useEffect(() => {
    setSelection((s) => reconcileSelection(s, tab.columns, tab.rows));
  }, [columnKey]); // the column set, not every row edit

  const kind = plotKind(kindId);
  const request = useMemo(
    () => buildPlotRequest(kindId, selection),
    [kindId, selection],
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
      <fieldset className="plot-from-columns__group">
        <legend className="plot-from-columns__legend">{gettext("Plot type")}</legend>
        <div className="plot-from-columns__kinds" role="radiogroup">
          {DATA_PLOT_KINDS.map((k) => {
            const icon = PLOT_TYPES.find((p) => p.id === k.family)?.icon;
            return (
              <button
                key={k.id}
                type="button"
                role="radio"
                aria-checked={k.id === kindId}
                className={`plot-from-columns__chip${k.id === kindId ? " active" : ""}`}
                onClick={() => setKindId(k.id)}
              >
                {icon && <i className={icon} aria-hidden="true" />}
                <span>{kindLabel(k.id)}</span>
              </button>
            );
          })}
        </div>
      </fieldset>

      {kind.usesX && (
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
            .filter((c) => !kind.usesX || c.name !== selection.x)
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
