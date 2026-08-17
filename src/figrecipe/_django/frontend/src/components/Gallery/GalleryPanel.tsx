/** Gallery panel — template selector modal.
 * Shows categories + thumbnail grid. Click to add template to canvas.
 *
 * Fetching, thumbnails and add-to-canvas live in `useGalleryTemplates`, shared
 * with GalleryStart (the empty-canvas gallery) so the two cannot drift.
 */

import { useEffect, useState } from "react";
import {
  CATEGORY_LABELS,
  flattenTemplates,
  useGalleryTemplates,
} from "./useGalleryTemplates";

interface Props {
  onClose: () => void;
  initialCategory?: string;
}

export function GalleryPanel({ onClose, initialCategory }: Props) {
  const { data, loading, failed, thumbnails, addTemplate } =
    useGalleryTemplates();
  const [activeCategory, setActiveCategory] = useState(
    initialCategory || "all",
  );

  // Fall back to "all" when the requested category ships no templates
  // (e.g. "vector", which declares none) — an empty tab the user did not
  // choose reads as a broken gallery.
  useEffect(() => {
    if (data && initialCategory && !data.categories[initialCategory]) {
      setActiveCategory("all");
    }
  }, [data, initialCategory]);

  // Close on Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  const templates =
    activeCategory === "all"
      ? flattenTemplates(data)
      : (data?.categories[activeCategory] ?? []);
  const categoryKeys = data ? Object.keys(data.categories) : [];

  return (
    <div className="gallery-overlay" onMouseDown={onClose}>
      <div className="gallery-panel" onMouseDown={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="gallery-header">
          <h3>
            <i className="fas fa-shapes" /> Template Gallery
          </h3>
          <button className="gallery-close" onClick={onClose} type="button">
            <i className="fas fa-times" />
          </button>
        </div>

        {/* Category tabs */}
        <div className="gallery-categories-bar">
          <button
            className={`gallery-cat-btn${activeCategory === "all" ? " active" : ""}`}
            onClick={() => setActiveCategory("all")}
            type="button"
          >
            All
          </button>
          {categoryKeys.map((key) => {
            const cat = CATEGORY_LABELS[key];
            return (
              <button
                key={key}
                className={`gallery-cat-btn${activeCategory === key ? " active" : ""}`}
                onClick={() => setActiveCategory(key)}
                type="button"
              >
                {cat && <i className={`fas ${cat.icon}`} />}
                {cat?.label || key}
              </button>
            );
          })}
        </div>

        {/* Content */}
        {loading ? (
          <div className="gallery-loading">
            <i className="fas fa-spinner fa-spin" /> Loading templates...
          </div>
        ) : failed ? (
          <div className="gallery-empty">
            <i className="fas fa-triangle-exclamation" />
            Could not load the template gallery
          </div>
        ) : templates.length === 0 ? (
          <div className="gallery-empty">
            <i className="fas fa-inbox" />
            No templates available for this category
          </div>
        ) : (
          <div className="gallery-grid">
            {templates.map((tmpl) => (
              <div
                key={tmpl.name}
                className="gallery-item"
                onClick={() => {
                  void addTemplate(tmpl).then((ok) => {
                    if (ok) onClose();
                  });
                }}
                title={`Add ${tmpl.label} to canvas`}
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
