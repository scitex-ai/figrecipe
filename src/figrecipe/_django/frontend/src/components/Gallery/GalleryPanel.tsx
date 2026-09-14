/** Gallery panel — template selector for ONE chosen plot family.
 *
 * Opened from the plot-type rail (PlotTypeNav). The family was just chosen in
 * the rail, so the panel shows ONLY that family's templates — picking "Line"
 * then being handed an "All" grid plus a second row of family tabs would make
 * the user re-choose the family they already picked. Fetching, thumbnails and
 * add-to-canvas live in `useGalleryTemplates`, shared with GalleryStart (the
 * empty-canvas gallery) so the two cannot drift.
 */

import { useEffect } from "react";
import { CATEGORY_LABELS, useGalleryTemplates } from "./useGalleryTemplates";
import { gettext, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

interface Props {
  onClose: () => void;
  /** The plot family chosen in the rail; the panel shows only its templates. */
  family: string;
}

export function GalleryPanel({ onClose, family }: Props) {
  const { data, loading, failed, thumbnails, addTemplate } =
    useGalleryTemplates();

  // A family that ships no templates (e.g. "vector" declares none) says so
  // instead of rendering an empty grid that reads as a broken gallery.
  const familyTemplates = data?.categories[family] ?? [];
  const familyLabel = gettext(CATEGORY_LABELS[family]?.label ?? family);

  // Close on Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <div className="gallery-overlay" onMouseDown={onClose}>
      <div className="gallery-panel" onMouseDown={(e) => e.stopPropagation()}>
        {/* Header — names the family the rail selection already made */}
        <div className="gallery-header">
          <h3>
            <i className={`fas ${CATEGORY_LABELS[family]?.icon ?? "fa-shapes"}`} />{" "}
            {interpolate(gettext("%s templates"), [familyLabel])}
          </h3>
          <button className="gallery-close" onClick={onClose} type="button" aria-label={gettext("Close")}>
            <i className="fas fa-times" />
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="gallery-loading">
            <i className="fas fa-spinner fa-spin" /> {gettext("Loading templates…")}
          </div>
        ) : failed ? (
          <div className="gallery-empty">
            <i className="fas fa-triangle-exclamation" />
            {gettext("Could not load the template gallery")}
          </div>
        ) : familyTemplates.length === 0 ? (
          <div className="gallery-empty">
            <i className="fas fa-inbox" />
            {interpolate(gettext("No %s templates are available in this install"), [familyLabel])}
          </div>
        ) : (
          <div className="gallery-grid">
            {familyTemplates.map((tmpl) => (
              <div
                key={tmpl.name}
                className="gallery-item"
                onClick={() => {
                  void addTemplate(tmpl).then((ok) => {
                    if (ok) onClose();
                  });
                }}
                title={interpolate(gettext("Add %s to canvas"), [tmpl.label])}
              >
                <div className="gallery-item-thumb">
                  {thumbnails[tmpl.name] ? (
                    <img src={thumbnails[tmpl.name]} alt={tmpl.label} />
                  ) : (
                    <i
                      className={`fas ${tmpl.icon} gallery-icon-placeholder`}
                    />
                  )}
                </div>
                <div className="gallery-item-label">{tmpl.label}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
