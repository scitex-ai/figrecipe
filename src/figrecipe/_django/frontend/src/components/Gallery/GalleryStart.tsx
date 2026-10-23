/** GalleryStart — the Panel canvas before anything is open.
 *
 * Operator batch apps-figrecipe-ui-feedback-20261023 item 2: the example
 * block is gone — no "Start from an example" head, no demo door, no
 * template tiles, no "Show N examples" disclosure. Rationale: the plot-type
 * rail plus the gallery modal remain the template route, so the empty
 * canvas kept two parallel "which plot?" choosers on one screen; and the
 * demo door wrote example artifacts into the project, which the Private
 * Beta spec only allows on an explicit user request. This surface now
 * points at the two real ways in: the Data tab (table-first) and the file
 * tree. The explicit-seed rule itself (./exampleSeed, PR 923) is untouched.
 */

import { gettext } from "@scitex/sdk/ui/ts/_base/gettext.ts";

interface GalleryStartProps {
  /** Jump to the full-width Data page (SigmaPlot-style worksheet). */
  onRequestDataTab?: () => void;
}

export function GalleryStart({ onRequestDataTab }: GalleryStartProps) {
  return (
    <div className="gallery-start">
      <div className="gallery-start-head">
        <h2 className="gallery-start-title">{gettext("No figures yet")}</h2>
        <p className="gallery-start-subtitle">
          {gettext("Select a recipe file from the tree to view its figure.")}
        </p>
      </div>

      {/* One way in, not two: the Data tab owns table-first entry
          (load-from-project, import, paste, sample); the tree owns recipes.
          No example door here anymore, so no second same-labelled button can
          drift back onto this screen. */}
      <div className="gallery-start-actions">
        <button
          type="button"
          className="gallery-start-primary"
          onClick={onRequestDataTab}
          title={gettext("Enter data on its own full-width page")}
        >
          <i className="fas fa-table" aria-hidden="true" />
          {gettext("Go to Data")}
        </button>
      </div>
    </div>
  );
}
