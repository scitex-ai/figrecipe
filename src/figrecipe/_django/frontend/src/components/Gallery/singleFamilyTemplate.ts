/** Pure decision helper for the plot-type rail (TODO 129).
 *
 * "Reach the target plot in one operation." When a plot family ships EXACTLY
 * one template (scatter, statistical/errorbar, contour), opening the gallery
 * just to show a single tile is a wasted operation: one click should add the
 * template directly. This pure function decides that — returning the lone
 * template so the caller can add it, or `null` so the caller falls back to
 * opening the gallery (multiple templates, zero templates, or data not loaded
 * yet).
 *
 * Pure and dependency-free (only reads the already-fetched gallery shape), so
 * it is unit-testable under Node without React, the DOM, or a network.
 */

import type { GalleryData, GalleryTemplate } from "./useGalleryTemplates";

export function singleFamilyTemplate(
  data: GalleryData | null,
  family: string,
): GalleryTemplate | null {
  if (!data) return null;
  const items = data.categories[family];
  if (items && items.length === 1) return items[0];
  return null;
}

/** True when selecting `family` should add its single template directly
 * (one operation) instead of opening the gallery. */
export function addFamilyDirectly(
  data: GalleryData | null,
  family: string,
): boolean {
  return singleFamilyTemplate(data, family) !== null;
}
