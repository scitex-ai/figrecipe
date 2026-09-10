/** Pure helpers for a plot family's example list (TODO 130 — hover panel).
 *
 * The rail's hover panel is INFORMATIONAL: it previews the templates a family
 * holds, distinct from the click behavior (TODO 128/129 — click adds a
 * single-template family directly or opens that family's gallery). These pure
 * functions derive the hover content from the already-fetched gallery data so
 * the decision is unit-testable under Node without React, the DOM, or the
 * scitex-ui SelectorNav.
 */

import type { GalleryData, GalleryTemplate } from "./useGalleryTemplates";

/** The templates a family ships (empty when the family has none or data is
 * not loaded yet). A family like "vector" declares no templates — the hover
 * panel should simply not appear for it. */
export function familyTemplates(
  data: GalleryData | null,
  family: string,
): GalleryTemplate[] {
  if (!data) return [];
  return data.categories[family] ?? [];
}

/** The example labels a family holds, for display in the hover panel. */
export function familyExampleLabels(
  data: GalleryData | null,
  family: string,
): string[] {
  return familyTemplates(data, family).map((t) => t.label);
}

/** Whether the hover panel should show for a family: it has templates AND the
 * data is loaded (so we are not previewing an empty/undetermined state). */
export function familyHasExamples(
  data: GalleryData | null,
  family: string,
): boolean {
  return !!data && familyTemplates(data, family).length > 0;
}
