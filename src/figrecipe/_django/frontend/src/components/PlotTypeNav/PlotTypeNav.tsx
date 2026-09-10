/** Vertical plot-type selector nav — fixed width, never collapses.
 * Uses the shared SelectorNav from scitex-ui.
 * Sits between DataTable and FigureViewer panes, matching scitex-cloud app selector pattern.
 *
 * TODO 129 — "reach the target plot in one operation": a family that ships
 * exactly one template (scatter, statistical/errorbar, contour) adds that
 * template the moment its rail item is selected, instead of opening a gallery
 * that only holds a single tile. Families with several templates (or none, or
 * data still loading) fall back to opening the gallery, which shows ONLY the
 * chosen family (TODO 128 — no 'All'/re-choose), exactly as before.
 */

import { useState } from "react";
import { SelectorNav } from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/selector-nav";
import type { SelectorNavItem } from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/selector-nav";
import { useEditorStore } from "../../store/useEditorStore";
import { GalleryPanel } from "../Gallery/GalleryPanel";
import { useGalleryTemplates } from "../Gallery/useGalleryTemplates";
import { singleFamilyTemplate } from "../Gallery/singleFamilyTemplate";

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
  const [galleryFamily, setGalleryFamily] = useState<string | undefined>();
  const { placedFigures } = useEditorStore();
  const { data, addTemplate } = useGalleryTemplates();

  const selectFamily = (id: string) => {
    // One operation (TODO 129): a single-template family adds its plot directly.
    const sole = singleFamilyTemplate(data, id);
    if (sole) {
      void addTemplate(sole);
      return;
    }
    // Otherwise open the gallery for that family (multiple/none/not-yet-loaded).
    // The panel shows ONLY the chosen family (TODO 128) — no 'All', no re-choose.
    setGalleryFamily(id);
    setGalleryOpen(true);
  };

  return (
    <>
      <SelectorNav
        items={PLOT_TYPES}
        activeId={galleryFamily ?? null}
        onSelect={selectFamily}
        indicator="left"
        style={{ width: 56, minWidth: 56, maxWidth: 56 }}
        footer={
          <span className="plot-type-nav__count">{placedFigures.length}</span>
        }
      />

      {galleryOpen && galleryFamily && (
        <GalleryPanel
          family={galleryFamily}
          onClose={() => setGalleryOpen(false)}
        />
      )}
    </>
  );
}
