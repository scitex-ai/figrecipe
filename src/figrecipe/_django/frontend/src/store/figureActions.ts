/** Figure composition actions — add/remove/select/move/align placed figures. */

import { api } from "../api/client";
import { DPI, getPanelBboxes } from "../hooks/useSnap";
import { pushUndoState } from "../hooks/useUndoRedo";
import type {
  BBox,
  PlacedFigure,
  PreviewResponse,
  TabData,
} from "../types/editor";

type Get = () => {
  placedFigures: PlacedFigure[];
  selectedFigureId: string | null;
  selectedFigureIds: string[];
  selectedElement: string | null;
  selectedBbox: BBox | null;
  workingDir: string | null;
  currentFile: string | null;
  darkMode: boolean;
  datatableTabs: Record<string, TabData>;
  activeTabId: string | null;
  showToast: (msg: string, type?: "info" | "success" | "error") => void;
  loadFiles: () => Promise<void>;
  loadDatatable: () => Promise<void>;
  loadPanelPositions: () => Promise<void>;
};
type Set = (
  partial:
    | Partial<ReturnType<Get>>
    | ((s: ReturnType<Get>) => Partial<ReturnType<Get>>),
) => void;

export function createFigureActions(set: Set, get: Get) {
  return {
    addFigure: async (path: string) => {
      const { placedFigures } = get();
      if (placedFigures.some((f) => f.path === path)) {
        const existing = placedFigures.find((f) => f.path === path);
        if (existing) set({ selectedFigureId: existing.id });
        get().showToast(`Already on canvas: ${path}`, "info");
        return;
      }

      set({ loading: true } as never);
      try {
        const data = await api.post<
          PreviewResponse & {
            color_map?: Record<string, unknown>;
            working_dir?: string;
          }
        >(`api/switch?dpi=${DPI}`, { path, dark_mode: get().darkMode });

        if (data.working_dir) set({ workingDir: data.working_dir });

        let nextY = 0;
        for (const fig of placedFigures) {
          const bottom = fig.y + fig.imgSize.height;
          if (bottom > nextY) nextY = bottom;
        }
        if (placedFigures.length > 0) nextY += 20;

        const newFig: PlacedFigure = {
          id: crypto.randomUUID(),
          path,
          x: 0,
          y: nextY,
          previewImage: data.image,
          bboxes: data.bboxes,
          imgSize: data.img_size,
          panelLetter: String.fromCharCode(65 + placedFigures.length),
        };

        set((s) => ({
          placedFigures: [...s.placedFigures, newFig],
          selectedFigureId: newFig.id,
          currentFile: path,
        }));

        const params = new URLSearchParams(window.location.search);
        const wd = data.working_dir || get().workingDir;
        const fullPath = wd ? `${wd}/${path}` : path;
        params.set("recipe", fullPath);
        window.history.replaceState(null, "", `?${params.toString()}`);

        get().showToast(`Added: ${path}`, "success");
        pushUndoState();
        get().loadFiles();
        get().loadDatatable();
        get().loadPanelPositions();
      } catch (e) {
        console.error("[Editor] Failed to add figure:", e);
        get().showToast(`Error: ${e}`, "error");
      } finally {
        set({ loading: false } as never);
      }
    },

    removeFigure: (id: string) => {
      set((s) => {
        const figure = s.placedFigures.find((f) => f.id === id);
        const remaining = s.placedFigures.filter((f) => f.id !== id);

        // Clean up data table tab for the removed figure
        const updatedTabs = { ...s.datatableTabs };
        if (figure?.path) {
          delete updatedTabs[figure.path];
        }
        // If active tab was for this figure, switch to first remaining tab
        let activeTabId = s.activeTabId;
        if (figure?.path && activeTabId === figure.path) {
          const tabKeys = Object.keys(updatedTabs);
          activeTabId = tabKeys.length > 0 ? tabKeys[0] : null;
        }

        return {
          placedFigures: remaining.map((f, i) => ({
            ...f,
            panelLetter: String.fromCharCode(65 + i),
          })),
          selectedFigureId:
            s.selectedFigureId === id ? null : s.selectedFigureId,
          selectedFigureIds: s.selectedFigureIds.filter((fid) => fid !== id),
          selectedElement: s.selectedFigureId === id ? null : s.selectedElement,
          selectedBbox: s.selectedFigureId === id ? null : s.selectedBbox,
          datatableTabs: updatedTabs,
          activeTabId,
        };
      });
      pushUndoState();
    },

    /** Reassign A, B, C... by spatial position (top-left first). */
    reorderPanelLetters: () => {
      set((s) => {
        const sorted = [...s.placedFigures].sort((a, b) =>
          a.y !== b.y ? a.y - b.y : a.x - b.x,
        );
        const idToLetter = new Map<string, string>();
        sorted.forEach((f, i) =>
          idToLetter.set(f.id, String.fromCharCode(65 + i)),
        );
        return {
          placedFigures: s.placedFigures.map((f) => ({
            ...f,
            panelLetter: idToLetter.get(f.id) ?? f.panelLetter,
          })),
        };
      });
      pushUndoState();
    },

    selectFigure: (id: string | null) => {
      set({
        selectedFigureId: id,
        selectedFigureIds: id ? [id] : [],
        selectedElement: null,
        selectedBbox: null,
      } as never);
    },

    moveFigure: (id: string, x: number, y: number) => {
      set((s) => {
        const moved = s.placedFigures.find((f) => f.id === id);
        if (!moved) return {};
        const dx = x - moved.x;
        const dy = y - moved.y;

        // Move grouped siblings together
        return {
          placedFigures: s.placedFigures.map((f) => {
            if (f.id === id) return { ...f, x, y };
            if (moved.groupId && f.groupId === moved.groupId) {
              return { ...f, x: f.x + dx, y: f.y + dy };
            }
            return f;
          }),
        };
      });
      pushUndoState();
    },

    /** Group selected figures (or all if none selected). */
    groupFigures: (ids: string[]) => {
      if (ids.length < 2) return;
      const groupId = crypto.randomUUID();
      set((s) => ({
        placedFigures: s.placedFigures.map((f) =>
          ids.includes(f.id) ? { ...f, groupId } : f,
        ),
      }));
      pushUndoState();
    },

    /** Ungroup figures by group ID. */
    ungroupFigures: (groupId: string) => {
      set((s) => ({
        placedFigures: s.placedFigures.map((f) =>
          f.groupId === groupId ? { ...f, groupId: undefined } : f,
        ),
      }));
      pushUndoState();
    },

    /** Align all figures by figure edge or axes edge. */
    alignFigures: (
      mode:
        | "left"
        | "right"
        | "top"
        | "bottom"
        | "center-h"
        | "center-v"
        | "axes-left"
        | "axes-right"
        | "axes-top"
        | "axes-bottom",
    ) => {
      const { placedFigures } = get();
      if (placedFigures.length < 2) return;

      // Helper: get reference value from first figure
      const first = placedFigures[0];
      const firstPanels = getPanelBboxes(first);
      const firstPanel = firstPanels[0];

      let refValue: number;
      switch (mode) {
        case "left":
          refValue = first.x;
          break;
        case "right":
          refValue = first.x + first.imgSize.width;
          break;
        case "top":
          refValue = first.y;
          break;
        case "bottom":
          refValue = first.y + first.imgSize.height;
          break;
        case "center-h":
          refValue = first.x + first.imgSize.width / 2;
          break;
        case "center-v":
          refValue = first.y + first.imgSize.height / 2;
          break;
        case "axes-left":
          refValue = firstPanel ? first.x + firstPanel.x : first.x;
          break;
        case "axes-right":
          refValue = firstPanel
            ? first.x + firstPanel.x + firstPanel.width
            : first.x + first.imgSize.width;
          break;
        case "axes-top":
          refValue = firstPanel ? first.y + firstPanel.y : first.y;
          break;
        case "axes-bottom":
          refValue = firstPanel
            ? first.y + firstPanel.y + firstPanel.height
            : first.y + first.imgSize.height;
          break;
        default:
          return;
      }

      set((s) => ({
        placedFigures: s.placedFigures.map((fig) => {
          const panels = getPanelBboxes(fig);
          const panel = panels[0];

          switch (mode) {
            case "left":
              return { ...fig, x: refValue };
            case "right":
              return { ...fig, x: refValue - fig.imgSize.width };
            case "top":
              return { ...fig, y: refValue };
            case "bottom":
              return { ...fig, y: refValue - fig.imgSize.height };
            case "center-h":
              return { ...fig, x: refValue - fig.imgSize.width / 2 };
            case "center-v":
              return { ...fig, y: refValue - fig.imgSize.height / 2 };
            case "axes-left":
              return {
                ...fig,
                x: panel ? refValue - panel.x : refValue,
              };
            case "axes-right":
              return {
                ...fig,
                x: panel
                  ? refValue - panel.x - panel.width
                  : refValue - fig.imgSize.width,
              };
            case "axes-top":
              return {
                ...fig,
                y: panel ? refValue - panel.y : refValue,
              };
            case "axes-bottom":
              return {
                ...fig,
                y: panel
                  ? refValue - panel.y - panel.height
                  : refValue - fig.imgSize.height,
              };
            default:
              return fig;
          }
        }),
      }));
      pushUndoState();
    },

    /** Distribute figures evenly. */
    distributeFigures: (direction: "horizontal" | "vertical") => {
      const { placedFigures } = get();
      if (placedFigures.length < 3) return;

      const sorted = [...placedFigures].sort((a, b) =>
        direction === "horizontal" ? a.x - b.x : a.y - b.y,
      );

      const first = sorted[0];
      const last = sorted[sorted.length - 1];

      if (direction === "horizontal") {
        const totalSpan = last.x + last.imgSize.width - first.x;
        const totalFigWidth = sorted.reduce(
          (sum, f) => sum + f.imgSize.width,
          0,
        );
        const gap = (totalSpan - totalFigWidth) / (sorted.length - 1);

        let currentX = first.x;
        const updates = new Map<string, number>();
        for (const fig of sorted) {
          updates.set(fig.id, currentX);
          currentX += fig.imgSize.width + gap;
        }

        set((s) => ({
          placedFigures: s.placedFigures.map((f) => {
            const newX = updates.get(f.id);
            return newX !== undefined ? { ...f, x: newX } : f;
          }),
        }));
      } else {
        const totalSpan = last.y + last.imgSize.height - first.y;
        const totalFigHeight = sorted.reduce(
          (sum, f) => sum + f.imgSize.height,
          0,
        );
        const gap = (totalSpan - totalFigHeight) / (sorted.length - 1);

        let currentY = first.y;
        const updates = new Map<string, number>();
        for (const fig of sorted) {
          updates.set(fig.id, currentY);
          currentY += fig.imgSize.height + gap;
        }

        set((s) => ({
          placedFigures: s.placedFigures.map((f) => {
            const newY = updates.get(f.id);
            return newY !== undefined ? { ...f, y: newY } : f;
          }),
        }));
      }
      pushUndoState();
    },
  };
}
