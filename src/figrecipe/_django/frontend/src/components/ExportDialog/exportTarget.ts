/** Export belongs to one Figure, identified by its panels' canvas key. */
import { canvasOf } from "../../types/editor.ts";
import type { PlacedFigure } from "../../types/editor.ts";

export function exportTarget(figures: PlacedFigure[], selectedId: string | null) {
  const selected = figures.find((figure) => figure.id === selectedId) ?? figures[0];
  if (!selected) return { panels: [], figureNumber: 1 };
  const key = canvasOf(selected);
  const keys = [...new Set(figures.map(canvasOf))];
  return {
    panels: figures.filter((figure) => canvasOf(figure) === key),
    figureNumber: keys.indexOf(key) + 1,
  };
}

export function exportFilename(project: string | null, figureNumber: number, now = new Date()) {
  const slug = (project?.split("/").filter(Boolean).pop() || "project")
    .replace(/[^\p{L}\p{N}._-]+/gu, "-");
  const utc = now.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
  return `${slug}-Figure${figureNumber}-${utc}`;
}
