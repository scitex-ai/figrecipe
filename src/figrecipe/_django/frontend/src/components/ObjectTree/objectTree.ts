/** The Objects tree model: which figures exist and which one is current.
 *
 * The Details pane used to open on "No selection — select an item from the
 * tree" with no tree anywhere on screen. The tree below lists every placed
 * figure, so Details always has something to point at and a click selects
 * the figure the viewer shows.
 *
 * Pure and dependency-free (no React, no DOM, no @scitex/ui), so it runs
 * under `node --experimental-strip-types` like the other decision modules
 * here.
 */

import type { PlacedFigure } from "../../types/editor";

export interface ObjectTreeItem {
  id: string;
  /** The recipe file name, e.g. `plot_plot.yaml`. */
  label: string;
  /** Panel letter when the figure carries one. */
  sublabel: string | null;
  selected: boolean;
}

/** The file name of a recipe path — the tree shows names, not directories. */
export function shortName(path: string): string {
  const base = path.split("/").pop() ?? path;
  return base.length > 0 ? base : path;
}

/** One row per placed figure, in canvas order; empty when nothing is open. */
export function figureTreeItems(
  figures: PlacedFigure[],
  selectedId: string | null,
): ObjectTreeItem[] {
  return figures.map((figure) => ({
    id: figure.id,
    label: shortName(figure.path),
    sublabel: figure.panelLetter ?? null,
    selected: figure.id === selectedId,
  }));
}
