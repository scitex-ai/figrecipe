/** Category → variant chooser decisions (card
 * figrecipe-data-column-and-plot-variant-ux-20260916).
 *
 * The rail answered a hover with a READ-ONLY list of example labels (TODO 130).
 * A label tells you the variant's name but not which variant you want — the
 * variants are pictures. This module holds the decisions behind upgrading that
 * panel into a real chooser: which variants a category offers, HOW the chooser
 * is revealed for the input device actually in hand (hover/focus on a fine
 * pointer, tap on a touch screen), where it may sit so it stays on screen, and
 * what each key does inside it.
 *
 * React-free, DOM-free and @scitex/ui-free on purpose: it is exercised by
 * `node --experimental-strip-types` (tests/variantChooser.test.ts), and a
 * module importing the app alias could not run there.
 */

import { familyHasExamples, familyTemplates } from "./familyExamples.ts";
import type { GalleryData, GalleryTemplate } from "./useGalleryTemplates.ts";

/** One variant offered by the chooser. Structurally a GalleryTemplate, so a
 * choice can be handed straight to `addTemplate`. */
export type VariantChoice = GalleryTemplate;

/** The variants a category offers ([] when it has none or data is not loaded). */
export function variantChoices(
  data: GalleryData | null,
  family: string,
): VariantChoice[] {
  return familyTemplates(data, family);
}

/** Whether the chooser has anything to offer. A family with no templates
 * (e.g. "vector") must not open an empty panel — the rail keeps its own
 * behaviour for it. */
export function chooserAvailable(
  data: GalleryData | null,
  family: string | null,
): boolean {
  if (!family) return false;
  return familyHasExamples(data, family);
}

/** What the device can do, as read from matchMedia. */
export interface PointerCaps {
  /** `(hover: hover)` — the device can hover at all. */
  hover: boolean;
  /** `(pointer: coarse)` — the primary pointer is a finger/stylus. */
  coarse: boolean;
}

export type RevealMode = "hover" | "tap";

/** How the chooser is revealed: hover/focus on a mouse, tap on a touch screen.
 *
 * Both facts are required for hover: a coarse pointer that also claims hover
 * (touch laptops, some Android browsers) still gets the tap gesture, because a
 * touch user cannot hold a hover to reach the panel and a tap is the gesture
 * they actually have. */
export function revealMode(caps: PointerCaps): RevealMode {
  return caps.hover && !caps.coarse ? "hover" : "tap";
}

/** The rail item's box, in viewport coordinates (DOMRect is structurally this). */
export interface AnchorRect {
  top: number;
  left: number;
  right: number;
  bottom: number;
  width: number;
  height: number;
}

export interface PanelSize {
  width: number;
  height: number;
}

export interface ViewportSize {
  width: number;
  height: number;
}

export interface ChooserPlacement {
  side: "right" | "left";
  top: number;
  left: number;
  /** Cap for the panel's own scroll area, so it never runs off the viewport. */
  maxHeight: number;
}

const GAP = 8;
const MARGIN = 8;
/** Never shrink the panel below this; a tiny viewport scrolls instead. */
const MIN_PANEL_HEIGHT = 120;

/** Place the chooser beside the rail item, kept inside the viewport.
 *
 * Prefers the right of the rail (the rail is a left-edge strip), flips to the
 * left when the right side would overflow, and clamps on both axes so a phone
 * in portrait still sees the whole panel. Vertically it is centred on the
 * pointed item, clamped to the viewport. */
export function chooserPlacement(
  anchor: AnchorRect,
  panel: PanelSize,
  viewport: ViewportSize,
  gap: number = GAP,
  margin: number = MARGIN,
): ChooserPlacement {
  const fitsRight = anchor.right + gap + panel.width <= viewport.width - margin;
  const fitsLeft = anchor.left - gap - panel.width >= margin;
  const side: "right" | "left" = fitsRight || !fitsLeft ? "right" : "left";

  const naturalLeft =
    side === "right" ? anchor.right + gap : anchor.left - gap - panel.width;
  const maxLeft = Math.max(margin, viewport.width - panel.width - margin);
  const left = Math.min(Math.max(naturalLeft, margin), maxLeft);

  const maxHeight = Math.max(
    MIN_PANEL_HEIGHT,
    viewport.height - 2 * margin,
  );
  const centred = anchor.top + anchor.height / 2 - panel.height / 2;
  const maxTop = Math.max(margin, viewport.height - panel.height - margin);
  const top = Math.min(Math.max(centred, margin), maxTop);

  return { side, top, left, maxHeight };
}

/** What a key pressed on a RAIL ITEM does about the chooser.
 *
 * A keyboard user can focus a rail item (which reveals the panel), but the
 * panel is portalled to <body> and its variants use a roving tabindex, so TAB
 * never lands inside it: the list was announced and unreachable. The menu-button
 * pattern fixes that — the arrow keys OPEN the panel and move focus into it,
 * where the list's own arrows/Enter/Escape then apply (choiceKeyAction).
 *
 * Three things deliberately do NOT open it:
 *   - Enter/Space keep their existing meaning on the rail (the one-operation
 *     plot and the data route). One gesture, one action.
 *   - a category with no variants, where an empty panel would be a dead end and
 *     would also swallow the rail's own arrow navigation.
 *   - a panel whose LIST already holds the focus: there the arrows belong to the
 *     list. Note this is focus, not mere openness — an already-revealed panel
 *     (the rail reveals on hover/focus) with the focus still on the rail item
 *     must still take the arrow, or the reveal would be decorative for the
 *     keyboard user it exists for. */
export function railKeyIntent(
  key: string,
  hasChoices: boolean,
  focusInPanel: boolean,
): "open" | "ignore" {
  if (!hasChoices || focusInPanel) return "ignore";
  return key === "ArrowDown" || key === "ArrowRight" ? "open" : "ignore";
}

/** The variant to put focus on when the chooser opens from the keyboard.
 *  Clamped like choiceKeyAction, so a stale index cannot focus nothing. */
export function chooserFocusIndex(active: number, count: number): number {
  if (count <= 0) return 0;
  const last = count - 1;
  const current = Number.isFinite(active) ? Math.trunc(active) : 0;
  return Math.min(Math.max(current, 0), last);
}

/** May focusing a rail item reveal its chooser?
 *
 * `suppressedFamily` is the category whose panel the keyboard just dismissed.
 * Escape hands the focus back to that very rail item, and the rail reveals on
 * focus — without this the panel would re-open on the way out and Escape would
 * look like a no-op. The suppression lasts until the next deliberate gesture
 * (an arrow, a click, a hover, or leaving the rail). */
export function revealOnFocus(
  family: string,
  suppressedFamily: string | null,
): boolean {
  return family !== suppressedFamily;
}

export type ChoiceKeyActionKind = "move" | "choose" | "dismiss" | "ignore";

export interface ChoiceKeyAction {
  /** Index the chooser should highlight after this key. */
  index: number;
  action: ChoiceKeyActionKind;
}

/** What a key does inside the chooser's variant list.
 *
 * Pure so the keyboard contract (which is the only way a keyboard/screen-reader
 * user can act on the panel) is testable without rendering it. `count === 0`
 * can never choose, and `index` is clamped, so a stale index from a rebuilt list
 * cannot throw or select a wrong variant. */
export function choiceKeyAction(
  key: string,
  index: number,
  count: number,
): ChoiceKeyAction {
  if (count <= 0) return { index: 0, action: "ignore" };
  const last = count - 1;
  const current = Math.min(Math.max(index, 0), last);

  switch (key) {
    case "ArrowDown":
    case "ArrowRight":
      return { index: current === last ? 0 : current + 1, action: "move" };
    case "ArrowUp":
    case "ArrowLeft":
      return { index: current === 0 ? last : current - 1, action: "move" };
    case "Home":
      return { index: 0, action: "move" };
    case "End":
      return { index: last, action: "move" };
    case "Enter":
    case " ":
      return { index: current, action: "choose" };
    case "Escape":
      return { index: current, action: "dismiss" };
    default:
      // Tab (and anything else) keeps the browser's own focus handling.
      return { index: current, action: "ignore" };
  }
}

/** Whether the chooser must ALSO offer the "plot from the table's columns"
 * route for this category.
 *
 * On a touch screen the chooser is reached by TAP, which is the same gesture
 * that used to route a data-plottable category straight to the Data pane. The
 * chooser therefore takes that gesture over for categories that hold several
 * variants — and has to carry the data route itself, or a phone user with a
 * table loaded would lose the ability to plot their data. */
export function chooserOffersDataRoute(
  plotKind: string | null,
  hasTableData: boolean,
): boolean {
  return Boolean(plotKind) && hasTableData;
}
