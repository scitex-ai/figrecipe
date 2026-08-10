/** Vertical plot-type selector nav — fixed width, never collapses.
 * Uses the shared SelectorNav from scitex-ui.
 * Sits between DataTable and FigureViewer panes, matching scitex-cloud app selector pattern.
 */

import { useState } from "react";
import { SelectorNav } from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/selector-nav";
import type { SelectorNavItem } from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/selector-nav";
import { useEditorStore } from "../../store/useEditorStore";
import { GalleryPanel } from "../Gallery/GalleryPanel";

const PLOT_TYPES: SelectorNavItem[] = [
  { id: "line", icon: "fas fa-chart-line", label: "Line" },
  { id: "scatter", icon: "fas fa-braille", label: "Scatter" },
  { id: "categorical", icon: "fas fa-chart-bar", label: "Bar" },
  { id: "distribution", icon: "fas fa-chart-column", label: "Dist" },
  { id: "statistical", icon: "fas fa-square-root-variable", label: "Stats" },
  { id: "grid", icon: "fas fa-th", label: "Grid" },
  { id: "area", icon: "fas fa-chart-area", label: "Area" },
  { id: "contour", icon: "fas fa-layer-group", label: "Contour" },
  { id: "vector", icon: "fas fa-arrows-alt", label: "Vector" },
  { id: "special", icon: "fas fa-shapes", label: "Special" },
];

export function PlotTypeNav() {
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [galleryCategory, setGalleryCategory] = useState<string | undefined>();
  const { placedFigures } = useEditorStore();

  const openGallery = (id: string) => {
    setGalleryCategory(id);
    setGalleryOpen(true);
  };

  return (
    <>
      <SelectorNav
        items={PLOT_TYPES}
        activeId={galleryCategory ?? null}
        onSelect={openGallery}
        indicator="left"
        style={{ width: 56, minWidth: 56, maxWidth: 56 }}
        footer={
          <span className="plot-type-nav__count">{placedFigures.length}</span>
        }
      />

      {galleryOpen && (
        <GalleryPanel
          onClose={() => setGalleryOpen(false)}
          initialCategory={galleryCategory}
        />
      )}
    </>
  );
}
