/** Variant thumbnail chooser for one plot category
 * (card figrecipe-data-column-and-plot-variant-ux-20260916).
 *
 * Replaces the rail's read-only example list (TODO 130). A label tells you the
 * variant's NAME; the variants are pictures, so the panel shows the same
 * thumbnails the gallery uses and lets the pointed-at category be picked in one
 * gesture: hover/focus on a mouse (revealed by the rail), tap on a touch screen.
 *
 * Portalled to <body>: the rail lives inside the scrolling phone layout, where
 * an absolutely-positioned panel was clipped and peeked out behind other
 * sections (same reason the gallery modal is portalled).
 *
 * The decisions (which variants, which reveal gesture, where the panel may sit,
 * what each key does) live in ./variantChooser so they stay testable under Node;
 * this file only renders them and reports the user's intent back to the rail.
 */

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { gettext, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";
import {
  choiceKeyAction,
  chooserPlacement,
  type AnchorRect,
  type ChooserPlacement,
  type VariantChoice,
} from "./variantChooser";

interface Props {
  /** The rail item's box in viewport coordinates — the panel's anchor. */
  anchor: AnchorRect;
  /** The category's translated label, for the panel heading. */
  familyLabel: string;
  choices: VariantChoice[];
  /** Template name -> data URL, from useGalleryTemplates. */
  thumbnails: Record<string, string>;
  /** A tap-revealed panel stays until dismissed; a hover-revealed one closes
   * when the pointer leaves rail + panel. */
  pinned: boolean;
  onChoose: (choice: VariantChoice) => void;
  /** "See all" hands the whole category back to the gallery modal. */
  onSeeAll: () => void;
  /** Present only when this category can be plotted from the loaded table:
   * the chooser is then the touch user's only way to reach the Data pane. */
  onPlotFromData?: () => void;
  onClose: () => void;
  /** The pointer moved into the panel: a hover-revealed panel must survive the
   * rail's own mouseleave, otherwise it closes in the gap between the two. */
  onPointerEnter?: () => void;
  onPointerLeave?: () => void;
}

/** Size used for the very first (pre-measurement) placement; replaced by the
 * panel's real box in the same commit, before the browser paints. */
const FALLBACK = { width: 248, height: 220 };

export function VariantChooser({
  anchor,
  familyLabel,
  choices,
  thumbnails,
  pinned,
  onChoose,
  onSeeAll,
  onPlotFromData,
  onClose,
  onPointerEnter,
  onPointerLeave,
}: Props) {
  const panelRef = useRef<HTMLDivElement | null>(null);
  const [placement, setPlacement] = useState<ChooserPlacement | null>(null);
  const [active, setActive] = useState(0);

  // Position from the panel's real size, once it exists: placing it with the
  // fallback size first would make it jump on the second paint.
  const { top, left, right, bottom, height } = anchor;
  useLayoutEffect(() => {
    const rect = panelRef.current?.getBoundingClientRect();
    const size = {
      width: Math.round(rect?.width || FALLBACK.width),
      height: Math.round(rect?.height || FALLBACK.height),
    };
    setPlacement(
      chooserPlacement(
        { top, left, right, bottom, width: right - left, height },
        size,
        { width: window.innerWidth, height: window.innerHeight },
      ),
    );
  }, [top, left, right, bottom, height, choices.length]);

  // A tapped-open panel is pinned: it must accept Escape even when focus is
  // still on the rail button, and it must not outlive a click outside it.
  useEffect(() => {
    if (!pinned) return;
    const onKey = (e: KeyboardEvent) => {
      const result = choiceKeyAction(e.key, active, choices.length);
      if (result.action === "dismiss") {
        e.preventDefault();
        onClose();
      }
    };
    const onDown = (e: PointerEvent) => {
      if (!panelRef.current?.contains(e.target as Node)) onClose();
    };
    window.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onDown);
    return () => {
      window.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onDown);
    };
  }, [pinned, active, choices.length, onClose]);

  // Move focus into a pinned panel so the variant list is reachable by keyboard
  // (and by a screen reader) the moment it opens.
  useEffect(() => {
    if (pinned) panelRef.current?.focus();
  }, [pinned]);

  if (choices.length === 0) return null;

  const step = (e: React.KeyboardEvent) => {
    const result = choiceKeyAction(e.key, active, choices.length);
    if (result.action === "ignore") return;
    e.preventDefault();
    if (result.action === "dismiss") {
      onClose();
      return;
    }
    if (result.action === "choose") {
      const choice = choices[result.index];
      if (choice) onChoose(choice);
      return;
    }
    setActive(result.index);
  };

  return createPortal(
    <div
      ref={panelRef}
      className="plot-type-nav__chooser"
      role="dialog"
      aria-label={interpolate(gettext("%s variants"), [familyLabel])}
      tabIndex={-1}
      style={{
        top: placement ? placement.top : undefined,
        left: placement ? placement.left : undefined,
        // Until the real box is measured, keep it off-screen rather than at 0,0.
        visibility: placement ? "visible" : "hidden",
        maxHeight: placement?.maxHeight,
        ["--chooser-side" as string]: placement?.side ?? "right",
      }}
      onKeyDown={step}
      onPointerEnter={onPointerEnter}
      onPointerLeave={onPointerLeave}
    >
      <div className="plot-type-nav__chooser-head">
        <span className="plot-type-nav__chooser-title">
          {interpolate(gettext("%s variants"), [familyLabel])}
        </span>
        <button
          type="button"
          className="plot-type-nav__chooser-close"
          onClick={onClose}
          aria-label={gettext("Close")}
        >
          <i className="fas fa-times" aria-hidden="true" />
        </button>
      </div>

      <ul className="plot-type-nav__chooser-list">
        {/* The data route first: with a table loaded it is the gesture the tap
            used to perform, so it must stay the most prominent action. */}
        {onPlotFromData && (
          <li>
            <button
              type="button"
              className="plot-type-nav__chooser-item plot-type-nav__chooser-item--data"
              tabIndex={-1}
              onClick={onPlotFromData}
            >
              <span className="plot-type-nav__chooser-thumb">
                <i className="fas fa-table" aria-hidden="true" />
              </span>
              <span className="plot-type-nav__chooser-label">
                {gettext("Plot from data columns…")}
              </span>
            </button>
          </li>
        )}
        {choices.map((choice, i) => (
          <li key={choice.name}>
            <button
              type="button"
              className={`plot-type-nav__chooser-item${i === active ? " is-active" : ""}`}
              tabIndex={i === active ? 0 : -1}
              onFocus={() => setActive(i)}
              onClick={() => onChoose(choice)}
              title={interpolate(gettext("Add %s to canvas"), [choice.label])}
            >
              <span className="plot-type-nav__chooser-thumb">
                {thumbnails[choice.name] ? (
                  <img src={thumbnails[choice.name]} alt="" loading="lazy" />
                ) : (
                  <i className={`fas ${choice.icon}`} aria-hidden="true" />
                )}
              </span>
              <span className="plot-type-nav__chooser-label">{choice.label}</span>
            </button>
          </li>
        ))}
      </ul>

      <button
        type="button"
        className="plot-type-nav__chooser-more"
        onClick={onSeeAll}
      >
        {gettext("See all templates…")}
      </button>
    </div>,
    document.body,
  );
}
