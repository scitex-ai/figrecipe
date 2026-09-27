/** Sync actions — element↔data linking, calls/labels, stat brackets. */

import { api } from "../api/client";
import type {
  AxesLabels,
  BBox,
  CallRecord,
  ElementDetails,
  StatBracket,
} from "../types/editor";
import { gettext, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

type Get = () => {
  selectedFigureId: string | null;
  selectedElement: string | null;
  elementCell: { row: number; col: number } | null;
  elementDataMap: Record<string, { columns: string[]; rowIndices: number[] }>;
  loadPreview: () => Promise<void>;
  loadHitmap: () => Promise<void>;
  loadPanelPositions: () => Promise<void>;
  showToast: (msg: string, type?: "info" | "success" | "error") => void;
};
type Set = (partial: Record<string, unknown> | ((s: any) => any)) => void;

export function createSyncActions(set: Set, get: Get) {
  return {
    // ── Load calls for an axes index ──────────────────────
    loadCalls: async (axIndex: number) => {
      try {
        const data = await api.get<{ calls: CallRecord[] }>(
          `calls?ax_index=${axIndex}`,
        );
        set((s: any) => ({
          calls: { ...s.calls, [String(axIndex)]: data.calls ?? [] },
        }));
      } catch {
        set((s: any) => ({
          calls: { ...s.calls, [String(axIndex)]: [] },
        }));
      }
    },

    // ── Load labels for an axes index ─────────────────────
    loadLabels: async (axIndex: number) => {
      try {
        const data = await api.get<AxesLabels>(
          `get_labels?ax_index=${axIndex}`,
        );
        set((s: any) => ({
          labels: { ...s.labels, [String(axIndex)]: data },
        }));
      } catch {
        /* no labels available */
      }
    },

    // ── Highlight data rows for a selected element ────────
    highlightDataForElement: (elementId: string | null) => {
      if (!elementId) {
        set({ highlightedDataRows: [] });
        return;
      }
      const { elementDataMap } = get();
      const link = elementDataMap[elementId];
      set({ highlightedDataRows: link?.rowIndices ?? [] });
    },

    // ── Inspected details for a selected element ──────────
    loadElementDetails: async () => {
      const { selectedElement, elementCell } = get();
      if (!selectedElement) {
        set({ elementDetails: null });
        return;
      }
      // A newer selection supersedes this fetch: only the latest pick may
      // write, or a fast click-train shows stale values under a new element.
      const wanted = selectedElement;
      const cell = elementCell;
      try {
        let endpoint = `element_details?element=${encodeURIComponent(wanted)}`;
        if (cell) endpoint += `&row=${cell.row}&col=${cell.col}`;
        const data = await api.get<ElementDetails>(endpoint);
        if (get().selectedElement !== wanted) return;
        set((s: any) => {
          const shapes = { ...s.elementShapes };
          const shape = (data as ElementDetails | null)?.shape;
          if (shape && shape.length === 2) {
            shapes[wanted] = { rows: shape[0], cols: shape[1] };
          }
          return { elementDetails: data, elementShapes: shapes };
        });
      } catch {
        if (get().selectedElement !== wanted) return;
        set({ elementDetails: null });
      }
    },

    // ── Refresh preview + bboxes + hitmap after mutation ──
    refreshAfterMutation: async () => {
      const { loadPreview, loadHitmap, loadPanelPositions } = get();
      await Promise.all([loadPreview(), loadHitmap(), loadPanelPositions()]);
    },

    // ── Stats bracket actions ─────────────────────────────
    loadStatBrackets: async (axIndex?: number) => {
      try {
        const q = axIndex !== undefined ? `?ax_index=${axIndex}` : "";
        const data = await api.get<{
          brackets: Record<string, StatBracket[]>;
        }>(`stats/list_brackets${q}`);
        set({ statBrackets: data.brackets });
      } catch {
        /* no brackets */
      }
    },

    addStatBracket: async (
      bracket: Omit<StatBracket, "bracket_id"> & { bracket_id?: string },
    ): Promise<string | null> => {
      try {
        const data = await api.post<{
          success: boolean;
          bracket_id: string;
          image: string;
          bboxes: Record<string, BBox>;
          img_size: { width: number; height: number };
        }>("stats/add_bracket", bracket);
        const { selectedFigureId } = get();
        if (selectedFigureId && data.image) {
          set((s: any) => ({
            placedFigures: s.placedFigures.map((f: any) =>
              f.id === selectedFigureId
                ? {
                    ...f,
                    previewImage: data.image,
                    bboxes: data.bboxes,
                    imgSize: data.img_size,
                  }
                : f,
            ),
          }));
        }
        // Reload brackets list
        const loadStatBrackets = (get() as any).loadStatBrackets;
        if (loadStatBrackets) loadStatBrackets();
        return data.bracket_id;
      } catch (e) {
        get().showToast(interpolate(gettext("Add bracket failed: %s"), [e]), "error");
        return null;
      }
    },

    removeStatBracket: async (
      axIndex: number,
      bracketId: string,
    ): Promise<boolean> => {
      try {
        const data = await api.post<{
          success: boolean;
          image: string;
          bboxes: Record<string, BBox>;
          img_size: { width: number; height: number };
        }>("stats/remove_bracket", {
          ax_index: axIndex,
          bracket_id: bracketId,
        });
        const { selectedFigureId } = get();
        if (selectedFigureId && data.image) {
          set((s: any) => ({
            placedFigures: s.placedFigures.map((f: any) =>
              f.id === selectedFigureId
                ? {
                    ...f,
                    previewImage: data.image,
                    bboxes: data.bboxes,
                    imgSize: data.img_size,
                  }
                : f,
            ),
          }));
        }
        const loadStatBrackets = (get() as any).loadStatBrackets;
        if (loadStatBrackets) loadStatBrackets();
        return true;
      } catch (e) {
        get().showToast(interpolate(gettext("Remove bracket failed: %s"), [e]), "error");
        return false;
      }
    },

    // ── Move a legend to a custom position (drag-to-place) ──
    // x, y are the legend's anchor in axes-fraction coords (0..1, y bottom-up);
    // the backend sets bbox_to_anchor=(x,y) with loc='upper left'.
    moveLegend: async (
      axIndex: number,
      x: number,
      y: number,
    ): Promise<boolean> => {
      try {
        const data = await api.post<{
          success: boolean;
          image: string;
          bboxes: Record<string, BBox>;
          img_size: { width: number; height: number };
        }>("update_legend_position", {
          ax_index: axIndex,
          loc: "custom",
          x,
          y,
        });
        const { selectedFigureId } = get();
        if (selectedFigureId && data.image) {
          set((s: any) => ({
            placedFigures: s.placedFigures.map((f: any) =>
              f.id === selectedFigureId
                ? {
                    ...f,
                    previewImage: data.image,
                    bboxes: data.bboxes,
                    imgSize: data.img_size,
                  }
                : f,
            ),
          }));
        }
        return true;
      } catch (e) {
        get().showToast(interpolate(gettext("Move legend failed: %s"), [e]), "error");
        return false;
      }
    },
  };
}
