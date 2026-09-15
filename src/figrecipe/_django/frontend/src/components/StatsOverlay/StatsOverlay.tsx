/** Stats bracket controls — displayed in Properties pane when axes selected. */

import { useCallback, useEffect } from "react";
import { useEditorStore } from "../../store/useEditorStore";
import type { StatBracket } from "../../types/editor";
import { gettext } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

export function StatsOverlay({ axIndex }: { axIndex: number }) {
  const {
    statBrackets,
    loadStatBrackets,
    addStatBracket,
    removeStatBracket,
    showToast,
  } = useEditorStore();

  useEffect(() => {
    loadStatBrackets(axIndex);
  }, [axIndex, loadStatBrackets]);

  const brackets = statBrackets[String(axIndex)] ?? [];

  const handleAddBracket = useCallback(async () => {
    const newBracket: Omit<StatBracket, "bracket_id"> = {
      ax_index: axIndex,
      x1: 0,
      x2: 1,
      y: null,
      p_value: 0.05,
      stars: "*",
      label: "",
      style: "bracket",
      effect_size: null,
      effect_size_name: null,
    };
    const id = await addStatBracket(newBracket);
    if (id) showToast(gettext("Bracket added"), "success");
  }, [axIndex, addStatBracket, showToast]);

  const handleRemove = useCallback(
    async (bracketId: string) => {
      await removeStatBracket(axIndex, bracketId);
    },
    [axIndex, removeStatBracket],
  );

  return (
    <div className="stats-overlay">
      <div className="stats-overlay__header">
        <span className="stats-overlay__title">
          <i className="fas fa-chart-bar" /> {gettext("Statistics")}
        </span>
        <button
          className="stats-overlay__add-btn"
          onClick={handleAddBracket}
          title={gettext("Add significance bracket")}
          type="button"
        >
          <i className="fas fa-plus" />
        </button>
      </div>

      {brackets.length === 0 ? (
        <p className="stats-overlay__empty">{gettext("No brackets on this panel")}</p>
      ) : (
        <ul className="stats-overlay__list">
          {brackets.map((b) => (
            <li key={b.bracket_id} className="stats-overlay__item">
              <span className="stats-overlay__label">
                x1={b.x1} → x2={b.x2}
                {b.stars && <strong> {b.stars}</strong>}
                {b.p_value !== undefined && (
                  <span className="stats-overlay__pval">
                    {" "}
                    p={b.p_value.toFixed(4)}
                  </span>
                )}
              </span>
              <button
                className="stats-overlay__remove-btn"
                onClick={() => handleRemove(b.bracket_id)}
                title={gettext("Remove bracket")}
                type="button"
              >
                <i className="fas fa-trash-alt" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
