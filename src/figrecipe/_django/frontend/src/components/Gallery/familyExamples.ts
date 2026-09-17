/** Pure helpers for a plot family's template list.
 *
 * The rail showed a family's templates as a READ-ONLY list of labels (TODO
 * 130). That list is gone: pointing at a rail item now reveals the variants as
 * a thumbnail chooser (card figrecipe-data-column-and-plot-variant-ux-20260916,
 * see ./variantChooser.ts), because a label names a variant while the variants
 * themselves are pictures.
 *
 * What the two surfaces still share is which templates a family holds, so it is
 * derived here once, from the already-fetched gallery data, without React, the
 * DOM or the scitex-ui SelectorNav — the chooser's decisions are unit-tested
 * under Node on top of these.
 */

import type { GalleryData, GalleryTemplate } from "./useGalleryTemplates";

/** The templates a family ships (empty when the family has none or data is
 * not loaded yet). A family like "vector" declares no templates — the chooser
 * must not open for it. */
export function familyTemplates(
  data: GalleryData | null,
  family: string,
): GalleryTemplate[] {
  if (!data) return [];
  return data.categories[family] ?? [];
}

/** Whether a family has templates to show: data loaded AND non-empty. The
 * chooser is suppressed otherwise, so pointing at a family never opens an
 * empty panel that reads as a broken one. */
export function familyHasExamples(
  data: GalleryData | null,
  family: string,
): boolean {
  return !!data && familyTemplates(data, family).length > 0;
}
