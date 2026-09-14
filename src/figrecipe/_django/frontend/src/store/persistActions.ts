/** Save / Restore / Style / Theme actions — extracted from editor store. */

import { api } from "../api/client";
import type {
  PlacedFigure,
  PreviewResponse,
  StyleOverrides,
} from "../types/editor";
import { gettext, interpolate } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts";

type Get = () => {
  placedFigures: PlacedFigure[];
  selectedFigureId: string | null;
  workingDir: string | null;
  darkMode: boolean;
  overrides: StyleOverrides;
  showToast: (msg: string, type?: "info" | "success" | "error") => void;
};
type Set = (
  partial:
    | Partial<ReturnType<Get> & { loading: boolean; currentTheme: string }>
    | ((
        s: ReturnType<Get> & { loading: boolean; currentTheme: string },
      ) => Partial<
        ReturnType<Get> & { loading: boolean; currentTheme: string }
      >),
) => void;

/** Build the figures payload for compose, including preview images. */
function buildComposePayload(get: Get) {
  const { placedFigures, workingDir, darkMode } = get();
  const figures = placedFigures.map((f) => ({
    path: f.path,
    x: f.x,
    y: f.y,
    width: f.imgSize.width,
    height: f.imgSize.height,
    image: f.previewImage,
    panel_letter: f.panelLetter,
    panel_letter_pos: f.panelLetterPos,
  }));
  return { figures, working_dir: workingDir, dark_mode: darkMode };
}

export function createPersistActions(set: Set, get: Get) {
  return {
    switchTheme: async (theme: string) => {
      set({ loading: true });
      try {
        const data = await api.post<PreviewResponse & { theme: string }>(
          "switch_theme",
          { theme },
        );
        const selId = get().selectedFigureId;
        if (selId) {
          set((s) => ({
            placedFigures: s.placedFigures.map((f) =>
              f.id === selId
                ? {
                    ...f,
                    previewImage: data.image,
                    bboxes: data.bboxes,
                    imgSize: data.img_size,
                  }
                : f,
            ),
            currentTheme: theme,
          }));
        } else {
          set({ currentTheme: theme });
        }
        get().showToast(interpolate(gettext("Theme: %s"), [theme]), "success");
      } catch (e) {
        console.error("[Editor] Failed to switch theme:", e);
        get().showToast(interpolate(gettext("Error: %s"), [e]), "error");
      } finally {
        set({ loading: false });
      }
    },

    updateOverrides: async (overrides: StyleOverrides) => {
      set({ loading: true });
      try {
        const data = await api.post<PreviewResponse>("update", { overrides });
        const selId = get().selectedFigureId;
        if (selId) {
          set((s) => ({
            placedFigures: s.placedFigures.map((f) =>
              f.id === selId
                ? {
                    ...f,
                    previewImage: data.image,
                    bboxes: data.bboxes,
                    imgSize: data.img_size,
                  }
                : f,
            ),
            overrides: { ...get().overrides, ...overrides },
          }));
        }
      } catch (e) {
        console.error("[Editor] Failed to update:", e);
        get().showToast(interpolate(gettext("Error: %s"), [e]), "error");
      } finally {
        set({ loading: false });
      }
    },

    save: async () => {
      const { placedFigures } = get();
      if (placedFigures.length === 0) {
        try {
          await api.post("save", { overrides: get().overrides });
          get().showToast(gettext("Saved"), "success");
        } catch (e) {
          console.error("[Editor] Failed to save:", e);
          get().showToast(interpolate(gettext("Error: %s"), [e]), "error");
        }
        return;
      }
      set({ loading: true });
      try {
        const payload = buildComposePayload(get);
        const result = await api.post<{ success: boolean; path: string }>(
          "api/compose",
          { ...payload, filename: "composed" },
        );
        get().showToast(interpolate(gettext("Composed → %s"), [result.path]), "success");
      } catch (e) {
        console.error("[Editor] Failed to compose:", e);
        get().showToast(interpolate(gettext("Error: %s"), [e]), "error");
      } finally {
        set({ loading: false });
      }
    },

    restore: async () => {
      set({ loading: true });
      try {
        const data = await api.post<PreviewResponse>("restore");
        const selId = get().selectedFigureId;
        if (selId) {
          set(
            (s) =>
              ({
                placedFigures: s.placedFigures.map((f) =>
                  f.id === selId
                    ? {
                        ...f,
                        previewImage: data.image,
                        bboxes: data.bboxes,
                        imgSize: data.img_size,
                      }
                    : f,
                ),
                overrides: {} as StyleOverrides,
                selectedElement: null,
                selectedBbox: null,
              }) as never,
          );
        }
        get().showToast(gettext("Restored to original"), "success");
      } catch (e) {
        console.error("[Editor] Failed to restore:", e);
        get().showToast(interpolate(gettext("Error: %s"), [e]), "error");
      } finally {
        set({ loading: false });
      }
    },
  };
}

/** Build compose export payload (for ExportDialog). */
export function buildExportPayload(
  placedFigures: PlacedFigure[],
  workingDir: string | null,
  darkMode: boolean,
  filename: string,
) {
  return {
    figures: placedFigures.map((f) => ({
      path: f.path,
      x: f.x,
      y: f.y,
      width: f.imgSize.width,
      height: f.imgSize.height,
      image: f.previewImage,
      panel_letter: f.panelLetter,
      panel_letter_pos: f.panelLetterPos,
    })),
    working_dir: workingDir,
    dark_mode: darkMode,
    filename,
  };
}
