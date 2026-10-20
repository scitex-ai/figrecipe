/** Objects tree — the always-visible figure list above Details.
 *
 * Details used to open on "No selection — select an item from the tree" with
 * no tree anywhere on screen. This tree lists every placed figure, so the
 * pane always has something to point at; a click selects the figure the
 * viewer shows. With nothing open, the tree says so and offers the two ways
 * in (an example figure, the Data page) instead of going blank.
 */

import { useEditorStore } from "../../store/useEditorStore";
import { useGalleryTemplates } from "../Gallery/useGalleryTemplates";
import { figureTreeItems } from "./objectTree";
import { gettext } from "@scitex/sdk/ui/ts/_base/gettext.ts";

interface ObjectTreeProps {
  /** Jump to the full-width Data page (SigmaPlot-style worksheet). */
  onRequestDataTab: () => void;
}

export function ObjectTree({ onRequestDataTab }: ObjectTreeProps) {
  const { placedFigures, selectedFigureId, selectFigure } = useEditorStore();
  const { openDemoFigure } = useGalleryTemplates();
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
          <div className="object-tree__empty-actions">
            <button
              type="button"
              className="data-pane__btn"
              onClick={() => void openDemoFigure()}
              title={gettext("Add an example recipe and its data to this project")}
            >
              <i className="fas fa-wand-magic-sparkles" aria-hidden="true" />
              {gettext("Open an example figure")}
            </button>
            <button
              type="button"
              className="data-pane__btn"
              onClick={onRequestDataTab}
              title={gettext("Enter data on its own full-width page")}
            >
              <i className="fas fa-table" aria-hidden="true" />
              {gettext("Go to Data")}
            </button>
          </div>
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
