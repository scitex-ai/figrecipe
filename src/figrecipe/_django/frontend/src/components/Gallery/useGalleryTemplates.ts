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
import { mapWithConcurrency } from "../../utils/mapWithConcurrency";
import { useEditorStore } from "../../store/useEditorStore";
import { gettext, gettext_noop, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

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

/** Max thumbnail requests in flight at once (site audit D2 — bounds the
 * per-session connection burst that exhausted the shared hub's Postgres). */
const THUMBNAIL_CONCURRENCY = 4;

export const CATEGORY_LABELS: Record<string, { label: string; icon: string }> = {
  line: { label: gettext_noop("Line"), icon: "fa-chart-line" },
  scatter: { label: gettext_noop("Scatter"), icon: "fa-braille" },
  categorical: { label: gettext_noop("Categorical"), icon: "fa-chart-bar" },
  distribution: { label: gettext_noop("Distribution"), icon: "fa-chart-column" },
  statistical: { label: gettext_noop("Statistical"), icon: "fa-square-root-variable" },
  grid: { label: gettext_noop("Grid"), icon: "fa-th" },
  area: { label: gettext_noop("Area"), icon: "fa-chart-area" },
  contour: { label: gettext_noop("Contour"), icon: "fa-layer-group" },
  special: { label: gettext_noop("Special"), icon: "fa-shapes" },
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
    // Names that still need a thumbnail. Mark them requested up front (the
    // ref, not a re-render), then fetch through a concurrency cap.
    const due = flattenTemplates(data).filter(
      (tmpl) => tmpl.has_thumbnail && !requested.current.has(tmpl.name),
    );
    for (const tmpl of due) requested.current.add(tmpl.name);
    if (due.length === 0) return;
    // CAP THE BURST (site audit D2): at most THUMBNAIL_CONCURRENCY thumbnail
    // requests in flight at once. Un-capped, a session fired ~18
    // api/gallery/thumbnail requests simultaneously; on a shared hub with many
    // sessions that exhausted the Postgres pool ("too many clients", 120 in
    // 15 min) and surfaced as "Could not load the example gallery". A small
    // constant keeps the gallery fully populated while bounding the connection
    // burst each session contributes.
    void mapWithConcurrency(due, THUMBNAIL_CONCURRENCY, async (tmpl) => {
      try {
        const d = await api.get<{ image: string }>(`api/gallery/thumbnail/${tmpl.name}`);
        setThumbnails((prev) => ({ ...prev, [tmpl.name]: d.image }));
      } catch {
        // A missing thumbnail degrades to the template's icon; it must
        // never take the surrounding grid down with it.
      }
    });
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
        showToast(interpolate(gettext("Failed to add template: %s"), [e]), "error");
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
