/** Table-column -> canvas-element emphasis (highlight only, never selection).
 *
 * Inverts the backend-served ``element_data_map`` (element key ->
 * ``{columns, rowIndices}``): given the badged table columns, name the
 * canvas elements drawn from them so the canvas can emphasize them with the
 * hover visual. Selection and the Details pane are untouched -- this answers
 * "where is this column plotted?" without stealing anything.
 *
 * Kept free of React and the @scitex/sdk/ui alias so it runs under
 * `node --experimental-strip-types` -- the JSX only renders what this
 * module decides.
 */

import type { ElementDataLink } from "../../types/editor.ts";

/** Element keys whose mapped columns intersect the given table columns. */
export function elementsForColumns(
  elementDataMap: Record<string, ElementDataLink>,
  columns: string[],
): string[] {
  if (columns.length === 0) return [];
  const wanted = new Set(columns);
  return Object.entries(elementDataMap)
    .filter(([, link]) => link.columns.some((c) => wanted.has(c)))
    .map(([key]) => key);
}
