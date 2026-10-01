/** Pure helper for the empty-canvas fallback (TODO 131).
 *
 * The "Start from an example" grid only renders when no figure is on the
 * canvas — and the plot-type rail is ALWAYS present beside it. Showing every
 * template tile there puts two parallel "which plot?" choosers on one screen
 * (measured 18 tiles + 10 rail families simultaneously on the live hub). This
 * helper encodes the reduction: how many example tiles are visible at once, as
 * a function of the disclosure state. Collapsed shows ZERO (the rail is the
 * single entry point); expanded shows ALL (the examples stay one click away).
 *
 * Pure and dependency-free, so it is unit-testable under Node without React,
 * the DOM, or the gallery fetch (same pattern as singleFamilyTemplate.ts and
 * lastProjectMemory.ts).
 */

import type { GalleryTemplate } from "./useGalleryTemplates";

/** The example tiles to render on the empty canvas, given the disclosure state.
 *
 * `expanded=false` (the default) returns an empty list — nothing is shown at
 * once, so the entry screen carries only the rail. `expanded=true` returns the
 * full list, preserving one-click access to every example.
 */
export function visibleStartTemplates(
  templates: GalleryTemplate[],
  expanded: boolean,
): GalleryTemplate[] {
  return expanded ? templates : [];
}

/** Number of example tiles visible at once (the cognitive-load metric). */
export function visibleStartTemplateCount(
  templates: GalleryTemplate[],
  expanded: boolean,
): number {
  return visibleStartTemplates(templates, expanded).length;
}
