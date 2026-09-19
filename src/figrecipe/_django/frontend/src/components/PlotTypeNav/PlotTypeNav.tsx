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
 * TODO 130 (upgraded by figrecipe-data-column-and-plot-variant-ux-20260916) —
 * POINTING at a rail item reveals that category's VARIANTS as a thumbnail
 * chooser (VariantChooser). The old panel listed the variant labels
 * read-only; a label names a variant but the variants are pictures, so the
 * panel now shows the same thumbnails the gallery uses and a variant can be
 * added straight from it, without the round trip through the gallery modal.
 * The reveal gesture follows the input device: hover/focus on a fine pointer,
 * TAP on a touch screen (where a hover cannot be held). Which gesture, which
 * variants and where the panel may sit are pure decisions in
 * Gallery/variantChooser — this file only wires them to the rail.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { SelectorNav } from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/selector-nav";
import type { SelectorNavItem } from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/selector-nav";
import { useEditorStore } from "../../store/useEditorStore";
import { GalleryPanel } from "../Gallery/GalleryPanel";
import { CATEGORY_LABELS, useGalleryTemplates } from "../Gallery/useGalleryTemplates";
import { singleFamilyTemplate } from "../Gallery/singleFamilyTemplate";
import { VariantChooser } from "../Gallery/VariantChooser";
import {
  chooserAvailable,
  chooserOffersDataRoute,
  railKeyIntent,
  revealMode,
  revealOnFocus,
  variantChoices,
  type AnchorRect,
  type PointerCaps,
  type VariantChoice,
} from "../Gallery/variantChooser";
import { kindForFamily } from "../DataTablePane/columnPlotSelection";
import { showEditorPane } from "../mobilePanes";
import { gettext, gettext_noop } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

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

/** The rail item's box, for anchoring the chooser. */
function rectOf(el: Element): AnchorRect {
  const r = el.getBoundingClientRect();
  return { top: r.top, left: r.left, right: r.right, bottom: r.bottom, width: r.width, height: r.height };
}

/** How this device reveals the chooser (hover vs tap). Read from matchMedia;
 * without it, assume a mouse rather than stranding a desktop user behind a
 * gesture they cannot perform. */
function usePointerCaps(): PointerCaps {
  const read = (): PointerCaps => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return { hover: true, coarse: false };
    }
    return {
      hover: window.matchMedia("(hover: hover)").matches,
      coarse: window.matchMedia("(pointer: coarse)").matches,
    };
  };
  const [caps, setCaps] = useState<PointerCaps>(read);
  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return;
    const queries = [
      window.matchMedia("(hover: hover)"),
      window.matchMedia("(pointer: coarse)"),
    ];
    const onChange = () => setCaps(read());
    queries.forEach((m) => m.addEventListener("change", onChange));
    return () => queries.forEach((m) => m.removeEventListener("change", onChange));
  }, []);
  return caps;
}

/** Time the panel survives the pointer leaving the rail, so crossing the gap
 * into the panel does not close it. */
const CLOSE_DELAY_MS = 140;

interface Reveal {
  family: string;
  anchor: AnchorRect;
  /** Tap-revealed: stays until dismissed. Hover-revealed: closes on leave. */
  pinned: boolean;
  /** Opened from the keyboard: the panel takes focus onto its active variant,
   *  and dismissing it hands focus back to this rail item. */
  keyboard: boolean;
}

export function PlotTypeNav({ paneAttrs = {} }: { paneAttrs?: Record<string, string | number> }) {
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [galleryFamily, setGalleryFamily] = useState<string | undefined>();
  const [reveal, setReveal] = useState<Reveal | null>(null);
  const { placedFigures, plotFamily, setPlotFamily, datatableTabs, activeTabId } =
    useEditorStore();
  const { data, thumbnails, addTemplate } = useGalleryTemplates();
  const activeTable = activeTabId ? datatableTabs[activeTabId] : null;
  const mode = revealMode(usePointerCaps());

  const navRef = useRef<HTMLDivElement | null>(null);
  const closeTimer = useRef<number | null>(null);
  /** The category whose panel the keyboard just dismissed: the rail reveals on
   *  focus, and Escape hands the focus back to that very item, so without this
   *  the panel would re-open on the way out (see revealOnFocus). */
  const suppressedFamily = useRef<string | null>(null);

  const cancelClose = useCallback(() => {
    if (closeTimer.current !== null) {
      window.clearTimeout(closeTimer.current);
      closeTimer.current = null;
    }
  }, []);

  const closeReveal = useCallback(() => {
    cancelClose();
    setReveal(null);
  }, [cancelClose]);

  const scheduleClose = useCallback(() => {
    cancelClose();
    // A pinned (tap) panel is dismissed by a click/Escape, never by a timer.
    if (reveal?.pinned) return;
    closeTimer.current = window.setTimeout(() => setReveal(null), CLOSE_DELAY_MS);
  }, [cancelClose, reveal?.pinned]);

  useEffect(() => cancelClose, [cancelClose]);

  /** The rail item for a family, for anchoring the chooser (and for handing
   *  focus back to it when a keyboard-opened panel closes). */
  const itemForFamily = useCallback((family: string): HTMLElement | null => {
    const idx = PLOT_TYPES.findIndex((p) => p.id === family);
    const items = navRef.current?.querySelectorAll<HTMLElement>(
      ".stx-app-selector-nav__item",
    );
    return items?.[idx] ?? null;
  }, []);

  const anchorForFamily = useCallback(
    (family: string): AnchorRect => {
      const item = itemForFamily(family);
      return item
        ? rectOf(item)
        : { top: 56, left: 0, right: 56, bottom: 96, width: 56, height: 40 };
    },
    [itemForFamily],
  );

  /** Dismiss the panel, and give the rail item its focus back when the panel was
   *  opened from the keyboard (otherwise the user is dropped at the top of the
   *  document, with nothing to continue from). The item is suppressed from
   *  re-revealing the panel by that very focus — else Escape would look like it
   *  did nothing. */
  const dismissReveal = useCallback(() => {
    const { family, keyboard } = reveal ?? { family: null, keyboard: false };
    closeReveal();
    if (!keyboard || !family) return;
    suppressedFamily.current = family;
    itemForFamily(family)?.focus();
  }, [closeReveal, itemForFamily, reveal?.family, reveal?.keyboard]);

  const familyLabel = useCallback((family: string): string => {
    const labelled = CATEGORY_LABELS[family]?.label ?? PLOT_TYPES.find((p) => p.id === family)?.label;
    return labelled ? gettext(labelled) : family;
  }, []);

  const plotFromData = useCallback(() => {
    // The family is already in the store; the Data pane's column form reads it.
    showEditorPane("data");
    document
      .querySelector(".plot-from-columns")
      ?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, []);

  const canPlotFromData = (family: string): boolean =>
    Boolean(
      activeTable && activeTable.columns.length > 0 && kindForFamily(family),
    );

  const selectFamily = (id: string) => {
    setPlotFamily(id);
    // Touch: a category holding SEVERAL variants opens its thumbnail chooser
    // first. Because the tap is now spent on the chooser, the chooser itself
    // carries the "plot from data columns" route when the category can be
    // plotted from the loaded table — otherwise the tap gesture would be a dead
    // end for a phone user with a table.
    if (mode === "tap" && variantChoices(data, id).length >= 2) {
      setReveal({ family: id, anchor: anchorForFamily(id), pinned: true, keyboard: false });
      return;
    }
    // With a table loaded, the rail picks the type the Data pane plots with.
    if (canPlotFromData(id)) {
      closeReveal();
      plotFromData();
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

  const chooseVariant = (choice: VariantChoice) => {
    const family = reveal?.family;
    // Keep using the gallery's own objects, so adding a variant is the same code
    // path as adding any other template (copy + open as an editable recipe).
    const template =
      (family ? variantChoices(data, family).find((t) => t.name === choice.name) : undefined) ??
      choice;
    void addTemplate(template).then((ok) => {
      if (!ok) return;
      closeReveal();
      showEditorPane("figure");
    });
  };

  const seeAllTemplates = () => {
    const family = reveal?.family;
    closeReveal();
    if (!family) return;
    setGalleryFamily(family);
    setGalleryOpen(true);
  };

  // TODO 130 — hover/focus tracking on the SelectorNav container: the scitex-ui
  // items are <button>s in PLOT_TYPES order and carry no data-id, so we map by
  // index. The chooser is revealed, not selection: pointing at a family never
  // adds a plot by itself.
  useEffect(() => {
    const root = navRef.current;
    if (!root) return;
    const infoAt = (e: Event): Reveal | null => {
      const el = e.target as HTMLElement | null;
      const item = el?.closest?.(".stx-app-selector-nav__item") as HTMLElement | null;
      if (!item) return null;
      const idx = [...root.querySelectorAll(".stx-app-selector-nav__item")].indexOf(item);
      const t = PLOT_TYPES[idx];
      return t
        ? { family: t.id, anchor: rectOf(item), pinned: false, keyboard: false }
        : null;
    };
    const hover = (e: Event) => {
      if (mode !== "hover") return; // touch: the tap on the rail reveals it
      const info = infoAt(e);
      if (!info) return;
      if (!chooserAvailable(data, info.family)) return;
      // The pointer is in use again: a keyboard dismissal no longer applies.
      suppressedFamily.current = null;
      cancelClose();
      setReveal((cur) =>
        cur?.family === info.family && cur.pinned ? cur : { ...info, anchor: info.anchor },
      );
    };
    const leave = () => scheduleClose();
    // Keyboard reveal: the arrow keys open the panel and move focus into it (the
    // panel is portalled to <body>, so TAB could never land there). Enter/Space
    // keep their rail meaning — one gesture, one action.
    const keydown = (e: KeyboardEvent) => {
      const info = infoAt(e);
      if (!info) return;
      // Whether the LIST already holds the focus, not whether the panel is
      // open: the rail reveals the panel on focus, and that reveal must still
      // take an arrow into the list.
      const panel = document.querySelector(".plot-type-nav__chooser");
      const focusInPanel = Boolean(
        panel && document.activeElement && panel.contains(document.activeElement),
      );
      if (
        railKeyIntent(
          e.key,
          chooserAvailable(data, info.family),
          focusInPanel,
        ) !== "open"
      )
        return;
      e.preventDefault();
      cancelClose();
      setReveal({ ...info, pinned: true, keyboard: true });
    };
    const focusin = (e: Event) => {
      const info = infoAt(e);
      if (!info || !chooserAvailable(data, info.family)) return;
      if (!revealOnFocus(info.family, suppressedFamily.current)) return;
      cancelClose();
      setReveal(info);
    };
    const focusout = (e: Event) => {
      // Tabbing INTO the chooser leaves the rail: keep the panel open, or a
      // keyboard user could never reach the variants.
      const next = (e as FocusEvent).relatedTarget as Node | null;
      const panel = document.querySelector(".plot-type-nav__chooser");
      if (next && panel?.contains(next)) return;
      // The focus left the rail entirely: the next visit is a fresh gesture.
      suppressedFamily.current = null;
      scheduleClose();
    };
    root.addEventListener("mouseover", hover);
    root.addEventListener("mouseleave", leave);
    root.addEventListener("focusin", focusin);
    root.addEventListener("focusout", focusout);
    root.addEventListener("keydown", keydown);
    return () => {
      root.removeEventListener("mouseover", hover);
      root.removeEventListener("mouseleave", leave);
      root.removeEventListener("focusin", focusin);
      root.removeEventListener("focusout", focusout);
      root.removeEventListener("keydown", keydown);
    };
  }, [mode, data, cancelClose, scheduleClose]);

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

      {/* The category's variants as thumbnails, revealed by pointing at (or
          tapping) a rail item. Portalled: inside the scrolling phone layout an
          in-flow panel was clipped and peeked out behind other sections. */}
      {reveal && (
        <VariantChooser
          anchor={reveal.anchor}
          familyLabel={familyLabel(reveal.family)}
          choices={variantChoices(data, reveal.family)}
          thumbnails={thumbnails}
          pinned={reveal.pinned}
          focusOnOpen={reveal.keyboard}
          onChoose={chooseVariant}
          onSeeAll={seeAllTemplates}
          onPlotFromData={
            chooserOffersDataRoute(
              kindForFamily(reveal.family)?.id ?? null,
              Boolean(activeTable && activeTable.columns.length > 0),
            )
              ? () => {
                  closeReveal();
                  plotFromData();
                }
              : undefined
          }
          onClose={dismissReveal}
          onPointerEnter={cancelClose}
          onPointerLeave={scheduleClose}
        />
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
