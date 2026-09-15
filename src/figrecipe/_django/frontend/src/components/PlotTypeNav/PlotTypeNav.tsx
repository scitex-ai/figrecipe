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
 *
 * TODO 130 — informational HOVER panel: on hover/focus of a rail item, a
 * small panel to its right previews that family's related examples (e.g. hover
 * "Line" -> "Line, Fill Between, Stack"). It is READ-ONLY and purely
 * informational: hovering neither selects nor opens the gallery, and the panel
 * itself is not clickable. It complements the click behavior (#128/#129) rather
 * than replacing it.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { SelectorNav } from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/selector-nav";
import type { SelectorNavItem } from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/selector-nav";
import { useEditorStore } from "../../store/useEditorStore";
import { GalleryPanel } from "../Gallery/GalleryPanel";
import { useGalleryTemplates } from "../Gallery/useGalleryTemplates";
import { singleFamilyTemplate } from "../Gallery/singleFamilyTemplate";
import { familyExampleLabels, familyHasExamples } from "../Gallery/familyExamples";
import { kindForFamily } from "../DataTablePane/columnPlotSelection";
import { showEditorPane } from "../mobilePanes";
import { gettext, gettext_noop, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

export const PLOT_TYPES: SelectorNavItem[] = [
  { id: "line", icon: "fas fa-chart-line", label: gettext_noop("Line") },
  { id: "scatter", icon: "fas fa-braille", label: gettext_noop("Scatter") },
  { id: "categorical", icon: "fas fa-chart-bar", label: gettext_noop("Bar") },
  { id: "distribution", icon: "fas fa-chart-column", label: gettext_noop("Dist") },
  { id: "statistical", icon: "fas fa-square-root-variable", label: gettext_noop("Stats") },
  { id: "grid", icon: "fas fa-th", label: gettext_noop("Grid") },
  { id: "area", icon: "fas fa-chart-area", label: gettext_noop("Area") },
  { id: "contour", icon: "fas fa-layer-group", label: gettext_noop("Contour") },
  { id: "vector", icon: "fas fa-arrows-alt", label: gettext_noop("Vector") },
  { id: "special", icon: "fas fa-shapes", label: gettext_noop("Special") },
];

export function PlotTypeNav({ paneAttrs = {} }: { paneAttrs?: Record<string, string | number> }) {
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [galleryFamily, setGalleryFamily] = useState<string | undefined>();
  const [hoveredFamily, setHoveredFamily] = useState<string | null>(null);
  const { placedFigures, plotFamily, setPlotFamily, datatableTabs, activeTabId } =
    useEditorStore();
  const { data, addTemplate } = useGalleryTemplates();
  const activeTable = activeTabId ? datatableTabs[activeTabId] : null;

  const selectFamily = (id: string) => {
    setPlotFamily(id);
    // With a table loaded, the rail picks the type the Data pane plots with.
    if (activeTable && activeTable.columns.length > 0 && kindForFamily(id)) {
      showEditorPane("data");
      document
        .querySelector(".plot-from-columns")
        ?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      return;
    }
    // One operation (TODO 129): a single-template family adds its plot directly.
    const sole = singleFamilyTemplate(data, id);
    if (sole) {
      void addTemplate(sole).then(() => showEditorPane("figure"));
      return;
    }
    // Otherwise open the gallery for that family (multiple/none/not-yet-loaded).
    // The panel shows ONLY the chosen family (TODO 128) — no 'All', no re-choose.
    setGalleryFamily(id);
    setGalleryOpen(true);
  };

  // TODO 130 — delegate hover/focus on the SelectorNav container to find which
  // family is pointed at (the scitex-ui items are <button>s in PLOT_TYPES order,
  // and carry no data-id, so we map by index). The panel is informational only.
  const navRef = useRef<HTMLDivElement | null>(null);
  const onItemHover = useCallback((familyId: string | null) => {
    setHoveredFamily(familyId);
  }, []);
  useEffect(() => {
    const root = navRef.current;
    if (!root) return;
    const itemAt = (e: Event): string | null => {
      const el = e.target as HTMLElement | null;
      const item = el?.closest?.(".stx-app-selector-nav__item") as HTMLElement | null;
      if (!item) return null;
      const idx = [...root.querySelectorAll(".stx-app-selector-nav__item")].indexOf(item);
      const t = PLOT_TYPES[idx];
      return t ? t.id : null;
    };
    const over = (e: Event) => onItemHover(itemAt(e));
    const leave = () => onItemHover(null);
    const focusin = (e: Event) => onItemHover(itemAt(e));
    const focusout = () => onItemHover(null);
    root.addEventListener("mouseover", over);
    root.addEventListener("mouseleave", leave);
    root.addEventListener("focusin", focusin);
    root.addEventListener("focusout", focusout);
    return () => {
      root.removeEventListener("mouseover", over);
      root.removeEventListener("mouseleave", leave);
      root.removeEventListener("focusin", focusin);
      root.removeEventListener("focusout", focusout);
    };
  }, [onItemHover]);

  const hoveredPlotType = PLOT_TYPES.find((p) => p.id === hoveredFamily);
  const hoveredFamilyLabel = hoveredPlotType ? gettext(hoveredPlotType.label) : hoveredFamily;

  const hoverLabels =
    hoveredFamily && familyHasExamples(data, hoveredFamily)
      ? familyExampleLabels(data, hoveredFamily)
      : null;

  return (
    <div className="plot-type-nav" {...paneAttrs}>
      <h2 className="fr-section-title">{gettext("Plot type")}</h2>
      <div ref={navRef} className="plot-type-nav__rail">
        <SelectorNav
          items={PLOT_TYPES.map((plotType) => ({ ...plotType, label: gettext(plotType.label) }))}
          activeId={plotFamily ?? galleryFamily ?? null}
          onSelect={selectFamily}
          indicator="left"
          style={{ width: 56, minWidth: 56, maxWidth: 56 }}
          footer={
            <span className="plot-type-nav__count">{placedFigures.length}</span>
          }
        />
      </div>

      {/* TODO 130 — read-only hover preview of the pointed family's examples.
          pointer-events:none so it never intercepts the rail's own hover/click. */}
      {hoverLabels && hoveredFamily && (
        <div className="plot-type-nav__hover" aria-hidden="true">
          <div className="plot-type-nav__hover-label">
            {interpolate(gettext("%s examples"), [hoveredFamilyLabel])}
          </div>
          <ul className="plot-type-nav__hover-list">
            {hoverLabels.map((lbl) => (
              <li key={lbl}>{lbl}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Portalled: a fixed overlay inside the scrolling phone layout was
          clipped and peeked out behind other sections. */}
      {galleryOpen &&
        galleryFamily &&
        createPortal(
          <GalleryPanel
            family={galleryFamily}
            onClose={() => setGalleryOpen(false)}
            onAdded={() => showEditorPane("figure")}
          />,
          document.body,
        )}
    </div>
  );
}
