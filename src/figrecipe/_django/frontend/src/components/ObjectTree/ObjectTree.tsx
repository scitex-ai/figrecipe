/** Objects tree — the always-visible figure list above Details.
 *
 * Details used to open on "No selection — select an item from the tree" with
 * no tree anywhere on screen. This tree lists every placed figure, so the
 * pane always has something to point at; a click selects the figure the
 * viewer shows. With nothing open, the tree says so. Operator UI batch: no
 * "Go to Data" door here — the Data tab is its own full-width destination
 * and Details must not route there (the empty Panel hint remains).
 */

import { useEditorStore } from "../../store/useEditorStore";
import { figureTreeItems } from "./objectTree";
import { gettext } from "@scitex/sdk/ui/ts/_base/gettext.ts";

export function ObjectTree() {
  const { placedFigures, selectedFigureId, selectFigure } = useEditorStore();
  const items = figureTreeItems(placedFigures, selectedFigureId);

  return (
    <section className="object-tree" aria-label={gettext("Objects")}>
      <h3 className="object-tree__title">
        <i className="fas fa-sitemap" aria-hidden="true" />
        {gettext("Objects")}
        {items.length > 0 && (
          <span className="object-tree__count">{items.length}</span>
        )}
      </h3>
      {items.length === 0 ? (
        <div className="object-tree__empty">
          <p className="object-tree__empty-text">
            {gettext("No figures yet.")}
          </p>
          {/* Operator UI batch: no "Go to Data" door in the Details pane.
              The Data tab is its own full-width destination. */}
        </div>
      ) : (
        <ul className="object-tree__list">
          {items.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className={`object-tree__item${item.selected ? " object-tree__item--selected" : ""}`}
                onClick={() => selectFigure(item.id)}
                aria-current={item.selected}
                title={item.label}
              >
                <i className="fas fa-image" aria-hidden="true" />
                <span className="object-tree__label">{item.label}</span>
                {item.sublabel && (
                  <span className="object-tree__badge">{item.sublabel}</span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
