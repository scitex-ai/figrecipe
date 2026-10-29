/** Core type definitions for the figrecipe editor. */

export interface BBox {
  x: number;
  y: number;
  width: number;
  height: number;
  type: string;
  label: string;
  ax_index?: number;
  call_id?: string;
}

export interface ImgSize {
  width: number;
  height: number;
}

export interface PlacedFigure {
  id: string;
  path: string;
  /** Owning canvas (figure) — the recipe path whose canvas this panel lives
   *  on. 1 Figure = 1 Canvas: the canvas page shows one figure's panels.
   *  Optional: figures placed before canvas keys existed (or restored from
   *  an old session) keep their own canvas — see canvasOf(). */
  canvasKey?: string;
  x: number;
  y: number;
  previewImage: string;
  bboxes: Record<string, BBox>;
  imgSize: ImgSize;
  groupId?: string;
  panelLetter?: string;
  panelLetterPos?: { x: number; y: number };
  /** Clew-tracked save: the recipe was written under an active scitex-clew
   *  session. Shown as a marker on the figure tab, never blocking. */
  clewTracked?: boolean;
}

/** Owning canvas of a placed figure. Figures without a key (placed before
 *  canvases existed, or restored from an old session) keep their own
 *  canvas, keyed by their recipe path. */
export function canvasOf(f: Pick<PlacedFigure, "canvasKey" | "path">): string {
  return f.canvasKey || f.path;
}

export interface FileTreeItem {
  name: string;
  path: string;
  type: "file" | "directory";
  is_current?: boolean;
  has_image?: boolean;
  children?: FileTreeItem[];
}

export interface TabData {
  id: string;
  label: string;
  columns: ColumnDef[];
  rows: (string | number)[][];
  /** Where the shown table came from (backend datatable/data `source`):
   *  "project" (stored, revision-guarded), "import" (session import),
   *  "record" (derived from the figure's recorded data — read-only until
   *  adopted), or null when unknown. Drives the edit-lock. */
  source: "project" | "import" | "record" | null;
}

export interface ColumnDef {
  name: string;
  dtype: string;
}

export interface StyleOverrides {
  [key: string]: unknown;
}

export interface CallRecord {
  call_id: string;
  method: string;
  ax_index: number;
  kwargs: Record<string, unknown>;
}

export interface PreviewResponse {
  image: string;
  bboxes: Record<string, BBox>;
  img_size: ImgSize;
  dark_mode?: boolean;
  /** True when the recipe was saved under an active scitex-clew session. */
  clew_tracked?: boolean;
}

export interface HitmapResponse {
  image: string;
  color_map: Record<string, unknown>;
}

export interface FilesResponse {
  tree: FileTreeItem[];
  files: string[];
  current_file: string | null;
  working_dir: string | null;
}

export interface ThemeInfo {
  themes: string[];
  current: string;
}

/** Labels for axes (title, xlabel, ylabel). */
export interface AxesLabels {
  title: string;
  xlabel: string;
  ylabel: string;
  suptitle: string;
}

/** Mapping from element to data columns/rows it uses. */
export interface ElementDataLink {
  columns: string[];
  rowIndices: number[];
}

/** One inspected canvas element, from the element_details endpoint.
 * Only the fields the element kind reports are present: a bar carries
 * value/row/column, a matrix cell value/row/col, a series count/ranges. */
export interface ElementDetails {
  element: string;
  type: string;
  label: string;
  ax_index: number;
  call_id?: string | null;
  series?: string | null;
  value?: number | [number, number] | null;
  row?: number | null;
  row_label?: string | number | null;
  col?: number | null;
  column?: string | number | null;
  index?: number | null;
  position?: number | null;
  orientation?: string | null;
  count?: number | null;
  shape?: [number, number] | null;
  minimum?: number | null;
  maximum?: number | null;
  mean?: number | null;
  levels?: number[] | null;
  x_range?: [number, number] | null;
  y_range?: [number, number] | null;
}

/** Statistical bracket annotation. */
export interface StatBracket {
  bracket_id: string;
  ax_index: number;
  x1: number;
  x2: number;
  y: number | null;
  p_value: number;
  stars: string;
  label: string;
  style: "bracket" | "asterisk" | "text" | "compact";
  effect_size: number | null;
  effect_size_name: string | null;
}
