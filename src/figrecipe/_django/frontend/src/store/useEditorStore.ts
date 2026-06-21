/** Central Zustand store — single source of truth for the editor. */

import { create } from "zustand";
import { api } from "../api/client";
import { DPI } from "../hooks/useSnap";
import type { SnapGuide } from "../hooks/useSnap";
import { pushUndoState } from "../hooks/useUndoRedo";
import type {
  AxesLabels,
  BBox,
  CallRecord,
  ColumnDef,
  ElementDataLink,
  FileTreeItem,
  FilesResponse,
  HitmapResponse,
  PlacedFigure,
  PreviewResponse,
  StatBracket,
  StyleOverrides,
  TabData,
  ThemeInfo,
} from "../types/editor";
import { createFigureActions } from "./figureActions";
import { createPersistActions } from "./persistActions";
import { createSyncActions } from "./syncActions";

interface ZoomControls {
  zoomIn: () => void;
  zoomOut: () => void;
  zoomToFit: () => void;
  resetView: () => void;
}

interface EditorState {
  // ── Canvas figures ──────────────────────────────────────
  placedFigures: PlacedFigure[];
  selectedFigureId: string | null;
  selectedFigureIds: string[];

  // ── Legacy ──────────────────────────────────────────────
  hitmapImage: string | null;
  colorMap: Record<string, unknown>;
  loading: boolean;

  // ── Selection ───────────────────────────────────────────
  selectedElement: string | null;
  selectedBbox: BBox | null;

  // ── Files ───────────────────────────────────────────────
  files: FileTreeItem[];
  currentFile: string | null;
  workingDir: string | null;

  // ── Data ────────────────────────────────────────────────
  datatableTabs: Record<string, TabData>;
  activeTabId: string | null;

  // ── Style ───────────────────────────────────────────────
  darkMode: boolean;
  currentTheme: string;
  themes: string[];
  overrides: StyleOverrides;

  // ── Panel positions (mm) ────────────────────────────────
  panelPositions: Record<
    string,
    { left: number; top: number; width: number; height: number }
  >;
  figSizeMm: { width: number; height: number } | null;

  // ── Sync: Element ↔ Data ────────────────────────────────
  elementDataMap: Record<string, ElementDataLink>;
  highlightedDataRows: number[];

  // ── Sync: Calls & Labels (moved from Properties local state) ──
  calls: Record<string, CallRecord[]>;
  labels: Record<string, AxesLabels>;

  // ── Sync: Stat brackets ───────────────────────────────
  statBrackets: Record<string, StatBracket[]>;

  // ── Clipboard ──────────────────────────────────────────
  clipboard: PlacedFigure | null;

  // ── Snap ───────────────────────────────────────────────
  snapEnabled: boolean;
  activeSnapGuides: SnapGuide[];

  // ── Zoom / Debug / Rulers / Toast ──────────────────────
  zoomControls: ZoomControls | null;
  showHitmap: boolean;
  showRulers: boolean;
  rulerUnit: "mm" | "inch";
  toast: { message: string; type: "info" | "success" | "error" } | null;

  // ── Actions ─────────────────────────────────────────────
  loadPreview: () => Promise<void>;
  loadHitmap: () => Promise<void>;
  loadFiles: () => Promise<void>;
  loadThemes: () => Promise<void>;
  loadDatatable: () => Promise<void>;
  loadPanelPositions: () => Promise<void>;

  addFigure: (path: string) => Promise<void>;
  removeFigure: (id: string) => void;
  selectFigure: (id: string | null) => void;
  moveFigure: (id: string, x: number, y: number) => void;
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
  ) => void;
  distributeFigures: (direction: "horizontal" | "vertical") => void;
  reorderPanelLetters: () => void;
  groupFigures: (ids: string[]) => void;
  ungroupFigures: (groupId: string) => void;

  toggleFigureSelection: (id: string) => void;

  copyFigure: () => void;
  pasteFigure: () => void;
  bringToFront: (id: string) => void;
  sendToBack: (id: string) => void;

  selectElement: (id: string | null, bbox?: BBox, figureId?: string) => void;
  switchFile: (path: string) => Promise<void>;
  switchTheme: (theme: string) => Promise<void>;
  updateOverrides: (overrides: StyleOverrides) => Promise<void>;
  save: () => Promise<void>;
  restore: () => Promise<void>;

  // ── Sync actions ───────────────────────────────────────
  loadCalls: (axIndex: number) => Promise<void>;
  loadLabels: (axIndex: number) => Promise<void>;
  highlightDataForElement: (elementId: string | null) => void;
  refreshAfterMutation: () => Promise<void>;

  // ── Stats bracket actions ─────────────────────────────
  loadStatBrackets: (axIndex?: number) => Promise<void>;
  addStatBracket: (
    bracket: Omit<StatBracket, "bracket_id"> & { bracket_id?: string },
  ) => Promise<string | null>;
  removeStatBracket: (axIndex: number, bracketId: string) => Promise<boolean>;
  moveLegend: (axIndex: number, x: number, y: number) => Promise<boolean>;

  setDarkMode: (dark: boolean) => void;
  toggleHitmap: () => void;
  toggleSnap: () => void;
  toggleRulers: () => void;
  toggleRulerUnit: () => void;
  showToast: (msg: string, type?: "info" | "success" | "error") => void;
  clearToast: () => void;
}

/* eslint-disable @typescript-eslint/no-explicit-any */
export const useEditorStore = create<EditorState>((set, get) => ({
  // ── Initial state ───────────────────────────────────────
  placedFigures: [],
  selectedFigureId: null,
  selectedFigureIds: [],
  hitmapImage: null,
  colorMap: {},
  loading: false,
  selectedElement: null,
  selectedBbox: null,
  files: [],
  currentFile: null,
  workingDir: null,
  datatableTabs: {},
  activeTabId: null,
  elementDataMap: {},
  highlightedDataRows: [],
  calls: {},
  labels: {},
  statBrackets: {},
  panelPositions: {},
  figSizeMm: null,
  darkMode: false,
  currentTheme: "SCITEX",
  themes: [],
  overrides: {},
  clipboard: null,
  snapEnabled: true,
  activeSnapGuides: [],
  zoomControls: null,
  showHitmap: false,
  showRulers: true,
  rulerUnit:
    (localStorage.getItem("figrecipe-ruler-unit") as "mm" | "inch") || "mm",
  toast: null,

  // ── Figure actions (from slice) ─────────────────────────
  ...createFigureActions(set as any, get as any),

  // ── Persist actions (save/restore/theme/overrides) ──────
  ...createPersistActions(set as any, get as any),

  // ── Multi-selection ────────────────────────────────────
  toggleFigureSelection: (id: string) => {
    set((s) => {
      const current = s.selectedFigureIds;
      // If nothing selected yet, start multi-select from current + new
      let base =
        current.length > 0
          ? current
          : s.selectedFigureId
            ? [s.selectedFigureId]
            : [];
      const ids = base.includes(id)
        ? base.filter((fid) => fid !== id)
        : [...base, id];
      return {
        selectedFigureIds: ids,
        selectedFigureId: ids.length > 0 ? ids[ids.length - 1] : null,
        selectedElement: null,
        selectedBbox: null,
      };
    });
  },

  // ── Clipboard & layer operations ──────────────────────
  copyFigure: () => {
    const { selectedFigureId, placedFigures } = get();
    const fig = placedFigures.find((f) => f.id === selectedFigureId);
    if (fig) set({ clipboard: { ...fig } });
  },

  pasteFigure: () => {
    const { clipboard, placedFigures } = get();
    if (!clipboard) return;
    const newFig: PlacedFigure = {
      ...clipboard,
      id: crypto.randomUUID(),
      x: clipboard.x + 20,
      y: clipboard.y + 20,
      groupId: undefined,
    };
    set({
      placedFigures: [...placedFigures, newFig],
      selectedFigureId: newFig.id,
    });
    pushUndoState();
  },

  bringToFront: (id: string) => {
    set((s) => {
      const idx = s.placedFigures.findIndex((f) => f.id === id);
      if (idx < 0 || idx === s.placedFigures.length - 1) return {};
      const figs = [...s.placedFigures];
      const [fig] = figs.splice(idx, 1);
      figs.push(fig);
      return { placedFigures: figs };
    });
    pushUndoState();
  },

  sendToBack: (id: string) => {
    set((s) => {
      const idx = s.placedFigures.findIndex((f) => f.id === id);
      if (idx <= 0) return {};
      const figs = [...s.placedFigures];
      const [fig] = figs.splice(idx, 1);
      figs.unshift(fig);
      return { placedFigures: figs };
    });
    pushUndoState();
  },

  // ── Load actions ────────────────────────────────────────
  loadPreview: async () => {
    set({ loading: true });
    try {
      const dark = get().darkMode;
      const data = await api.get<PreviewResponse>(
        `preview?dark_mode=${dark}&dpi=${DPI}`,
      );
      if (data.dark_mode !== undefined) set({ darkMode: data.dark_mode });
      const { placedFigures, selectedFigureId, currentFile } = get();
      if (placedFigures.length === 0) {
        const recipeParam =
          new URLSearchParams(window.location.search).get("recipe") || "";
        const recipePath =
          currentFile ?? recipeParam.split("/").pop() ?? "preview";
        const fig: PlacedFigure = {
          id: crypto.randomUUID(),
          path: recipePath,
          x: 0,
          y: 0,
          previewImage: data.image,
          bboxes: data.bboxes,
          imgSize: data.img_size,
          panelLetter: "A",
        };
        set({ placedFigures: [fig], selectedFigureId: fig.id });
      } else if (selectedFigureId) {
        set((s) => ({
          placedFigures: s.placedFigures.map((f) =>
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
    } catch (e) {
      console.error("[Editor] Failed to load preview:", e);
      get().showToast("Failed to load preview", "error");
    } finally {
      set({ loading: false });
    }
  },

  loadHitmap: async () => {
    try {
      const data = await api.get<HitmapResponse>("hitmap");
      set({ hitmapImage: data.image, colorMap: data.color_map });
    } catch (e) {
      console.error("[Editor] Failed to load hitmap:", e);
    }
  },

  loadFiles: async () => {
    try {
      const data = await api.get<FilesResponse>("api/files");
      set({
        files: data.tree,
        currentFile: data.current_file,
        workingDir: data.working_dir ?? null,
      });
    } catch (e) {
      console.error("[Editor] Failed to load files:", e);
    }
  },

  loadThemes: async () => {
    try {
      const data = await api.get<ThemeInfo>("list_themes");
      set({ themes: data.themes, currentTheme: data.current });
    } catch (e) {
      console.error("[Editor] Failed to load themes:", e);
    }
  },

  loadDatatable: async () => {
    try {
      const data = await api.get<{
        columns: ColumnDef[];
        rows: (string | number)[][];
        element_data_map?: Record<
          string,
          { columns: string[]; row_indices: number[] }
        >;
      }>("datatable/data");
      const tab: TabData = {
        id: "main",
        label: "Data",
        columns: data.columns ?? [],
        rows: data.rows ?? [],
      };
      // Build element-data mapping if provided by backend
      const elementDataMap: Record<
        string,
        { columns: string[]; rowIndices: number[] }
      > = {};
      if (data.element_data_map) {
        for (const [key, val] of Object.entries(data.element_data_map)) {
          elementDataMap[key] = {
            columns: val.columns,
            rowIndices: val.row_indices,
          };
        }
      }
      set({
        datatableTabs: { main: tab },
        activeTabId: "main",
        elementDataMap,
      });
    } catch (e) {
      console.warn("[Editor] No datatable data available:", e);
    }
  },

  loadPanelPositions: async () => {
    try {
      const data = await api.get<Record<string, any>>("get_axes_positions");
      const figsize = data._figsize as
        | { width_mm: number; height_mm: number }
        | undefined;
      const positions: Record<
        string,
        { left: number; top: number; width: number; height: number }
      > = {};
      for (const [key, val] of Object.entries(data)) {
        if (key !== "_figsize" && val && "left" in val) positions[key] = val;
      }
      set({
        panelPositions: positions,
        figSizeMm: figsize
          ? { width: figsize.width_mm, height: figsize.height_mm }
          : null,
      });
    } catch (e) {
      console.warn("[Editor] No panel positions available:", e);
    }
  },

  // ── Sync actions (calls, labels, highlights, stats brackets) ──
  ...createSyncActions(set as any, get as any),

  // ── Selection ───────────────────────────────────────────
  selectElement: (elementId, bbox, figureId) => {
    set({
      selectedElement: elementId,
      selectedBbox: bbox ?? null,
      selectedFigureId: figureId ?? get().selectedFigureId,
    });
    // Sync gap fix: load calls/labels and highlight data rows
    if (bbox?.ax_index !== undefined) {
      get().loadCalls(bbox.ax_index);
      get().loadLabels(bbox.ax_index);
    }
    get().highlightDataForElement(elementId);
  },

  switchFile: async (path) => get().addFigure(path),

  // ── UI toggles ──────────────────────────────────────────
  setDarkMode: async (dark) => {
    set({ darkMode: dark });
    // Only update backend if figures are loaded (avoids "No recipe loaded" error)
    const { placedFigures } = get();
    if (placedFigures.length === 0) return;
    try {
      const data = await api.post<PreviewResponse>("update", {
        dark_mode: dark,
      });
      if (data?.image) {
        const { selectedFigureId } = get();
        if (selectedFigureId) {
          set((s) => ({
            placedFigures: s.placedFigures.map((f) =>
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
      }
    } catch (e) {
      console.error("[Editor] setDarkMode API failed:", e);
    }
  },
  toggleHitmap: () => set((s) => ({ showHitmap: !s.showHitmap })),
  toggleSnap: () => set((s) => ({ snapEnabled: !s.snapEnabled })),
  toggleRulers: () => set((s) => ({ showRulers: !s.showRulers })),
  toggleRulerUnit: () =>
    set((s) => {
      const next = s.rulerUnit === "mm" ? "inch" : "mm";
      localStorage.setItem("figrecipe-ruler-unit", next);
      return { rulerUnit: next };
    }),
  showToast: (message, type = "info") => {
    set({ toast: { message, type } });
    // Errors persist until dismissed (shown in the AlertBanner -- fail-loud);
    // info/success auto-clear as transient toasts.
    if (type !== "error") {
      setTimeout(() => set({ toast: null }), 3000);
    }
  },
  clearToast: () => set({ toast: null }),
}));
