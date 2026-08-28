/** Shared access to the Template Gallery data.
 *
 * Two surfaces render the same templates and must not drift:
 *   - GalleryPanel  — the modal opened from the plot-type nav
 *   - GalleryStart  — what the Plot canvas shows before anything is open
 *
 * Both need the same three things (categories, thumbnails, add-to-canvas), so
 * they share this hook rather than each keeping its own copy of the fetch
 * logic. `failed` is carried explicitly: a gallery that could not be fetched
 * and a gallery that is genuinely empty look identical otherwise, and the
 * empty canvas has to say which one happened instead of rendering nothing.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import { useEditorStore } from "../../store/useEditorStore";

export interface GalleryTemplate {
  name: string;
  label: string;
  icon: string;
  path: string;
  has_thumbnail: boolean;
}

export interface GalleryData {
  categories: Record<string, GalleryTemplate[]>;
}

export const CATEGORY_LABELS: Record<string, { label: string; icon: string }> =
  {
    line: { label: "Line", icon: "fa-chart-line" },
    scatter: { label: "Scatter", icon: "fa-braille" },
    categorical: { label: "Categorical", icon: "fa-chart-bar" },
    distribution: { label: "Distribution", icon: "fa-chart-column" },
    statistical: { label: "Statistical", icon: "fa-square-root-variable" },
    grid: { label: "Grid", icon: "fa-th" },
    area: { label: "Area", icon: "fa-chart-area" },
    contour: { label: "Contour", icon: "fa-layer-group" },
    special: { label: "Special", icon: "fa-shapes" },
  };

/** Every template once, in declaration order (a template may sit in two
 * categories — "Fill Between" is both line and area). */
export function flattenTemplates(data: GalleryData | null): GalleryTemplate[] {
  if (!data) return [];
  const seen = new Set<string>();
  const all: GalleryTemplate[] = [];
  for (const items of Object.values(data.categories)) {
    for (const item of items) {
      if (seen.has(item.name)) continue;
      seen.add(item.name);
      all.push(item);
    }
  }
  return all;
}

export function useGalleryTemplates() {
  const [data, setData] = useState<GalleryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const [thumbnails, setThumbnails] = useState<Record<string, string>>({});
  const { addFigure, showToast } = useEditorStore();

  // Names already requested. Keying the fetch effect off `thumbnails` alone
  // re-fires it on every arrival, and an in-flight request has no entry yet —
  // so 18 templates issued a quadratic burst of duplicate requests. A ref is
  // the right memory here: it must not itself trigger a render.
  const requested = useRef<Set<string>>(new Set());

  useEffect(() => {
    let cancelled = false;
    api
      .get<GalleryData>("api/gallery")
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        console.error("[Gallery] Failed to load:", e);
        if (!cancelled) setFailed(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!data) return;
    for (const tmpl of flattenTemplates(data)) {
      if (!tmpl.has_thumbnail || requested.current.has(tmpl.name)) continue;
      requested.current.add(tmpl.name);
      api
        .get<{ image: string }>(`api/gallery/thumbnail/${tmpl.name}`)
        .then((d) => {
          setThumbnails((prev) => ({ ...prev, [tmpl.name]: d.image }));
        })
        .catch(() => {
          // A missing thumbnail degrades to the template's icon; it must
          // never take the surrounding grid down with it.
        });
    }
  }, [data]);

  /** Copy a template into the working dir and open it on the canvas. This is
   * the same path a file-tree click takes (`addFigure`), so a template opens
   * as an ordinary editable recipe, not as a special read-only preview. */
  const addTemplate = useCallback(
    async (tmpl: GalleryTemplate) => {
      try {
        const result = await api.post<{ recipe_path: string }>(
          "api/gallery/add",
          { template: tmpl.name },
        );
        await addFigure(result.recipe_path);
        return true;
      } catch (e) {
        showToast(`Failed to add template: ${e}`, "error");
        return false;
      }
    },
    [addFigure, showToast],
  );

  /** Open the figure a brand-new workspace should start on.
   *
   * The server decides whether there is one: it seeds a small demo recipe
   * (and its data) into an EMPTY workspace, hands back an existing seed
   * unchanged, and returns `null` for a workspace that already holds the
   * user's own recipes — a real project must not be littered with a demo.
   *
   * Resolves to `true` only when a figure is now on the canvas, so the
   * caller can fall back to the template grid on `false`.
   */
  const openDemoFigure = useCallback(async () => {
    try {
      const result = await api.post<{ recipe_path: string | null }>(
        "api/gallery/demo",
        {},
      );
      if (!result.recipe_path) return false;
      await addFigure(result.recipe_path);
      return true;
    } catch (e) {
      // Never a toast: the visitor did not ask for this, so a failure must
      // degrade to the gallery silently rather than open with an error.
      console.error("[Gallery] Could not open the demo figure:", e);
      return false;
    }
  }, [addFigure]);

  return { data, loading, failed, thumbnails, addTemplate, openDemoFigure };
}
