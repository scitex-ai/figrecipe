/** GalleryStart — the Plot canvas before anything is open.
 *
 * This replaces a dead end. The empty canvas used to read "Select a recipe
 * file to view the figure", which names a thing the visitor does not have:
 * a brand-new project has no recipes, so the instruction cannot be followed
 * and the tool never shows what it makes. Showing the shipped templates
 * instead makes the empty state the fastest way IN — every tile is a real
 * figure, and one click opens its recipe as an ordinary editable file.
 *
 * The tiles come from the same gallery the plot-type nav opens, so a template
 * added there appears here with no second registration.
 */

import { useGalleryTemplates, flattenTemplates } from "./useGalleryTemplates";

export function GalleryStart() {
  const { data, loading, failed, thumbnails, addTemplate } =
    useGalleryTemplates();

  if (loading) {
    return (
      <div className="gallery-start gallery-start--message">
        <i className="fas fa-spinner fa-spin" />
        <p>Loading example figures…</p>
      </div>
    );
  }

  // Never render a blank pane. A failure and an empty gallery are different
  // situations and each gets its own words, because "nothing here" with no
  // explanation is exactly the dead end this component exists to remove.
  if (failed) {
    return (
      <div className="gallery-start gallery-start--message">
        <i className="fas fa-triangle-exclamation" />
        <p>Could not load the example gallery.</p>
        <p className="gallery-start-hint">
          Select a recipe file from the tree to view its figure.
        </p>
      </div>
    );
  }

  const templates = flattenTemplates(data);

  if (templates.length === 0) {
    return (
      <div className="gallery-start gallery-start--message">
        <i className="fas fa-image" />
        <p>No example figures are available in this install.</p>
        <p className="gallery-start-hint">
          Select a recipe file from the tree to view its figure.
        </p>
      </div>
    );
  }

  return (
    <div className="gallery-start">
      <div className="gallery-start-head">
        <h2 className="gallery-start-title">Start from an example</h2>
        <p className="gallery-start-subtitle">
          Click a figure to open its recipe — then edit the data, the style and
          the layout, and export it publication-ready.
        </p>
      </div>

      <div className="gallery-start-grid">
        {templates.map((tmpl) => (
          <button
            key={tmpl.name}
            type="button"
            className="gallery-start-item"
            onClick={() => addTemplate(tmpl)}
            title={`Open the ${tmpl.label} example`}
          >
            <span className="gallery-start-thumb">
              {thumbnails[tmpl.name] ? (
                <img src={thumbnails[tmpl.name]} alt={tmpl.label} />
              ) : (
                <i className={`fas ${tmpl.icon} gallery-icon-placeholder`} />
              )}
            </span>
            <span className="gallery-start-label">{tmpl.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
