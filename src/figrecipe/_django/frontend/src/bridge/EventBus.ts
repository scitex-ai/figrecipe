/**
 * FigRecipe event bus — typed wrapper around generic bridge events.
 *
 * Events flow bidirectionally:
 *   React (figrecipe store changes) → CustomEvent → TS managers
 *   TS managers (file tree clicks)  → CustomEvent → React (store updates)
 */

import { emitBridgeEvent, onBridgeEvent } from "@scitex/ui/src/scitex_ui/static/scitex_ui/react/app/bridge";

const SLUG = "figrecipe";

// ── Event type map ──────────────────────────────────────────────

export interface FigrecipeEventMap {
  /** React → TS: a file was selected in figrecipe's file tree */
  fileSelect: { path: string };
  /** React → TS: a canvas element was clicked */
  elementSelect: {
    elementId: string;
    bbox: { x: number; y: number; w: number; h: number } | null;
  };
  /** React → TS: a property was changed */
  propertyChange: { key: string; value: unknown };
  /** React → TS: data was imported or changed */
  dataChange: { columns: string[]; rowCount: number };
  /** React → TS: a stat bracket was added */
  statBracketAdd: {
    bracket_id: string;
    ax_index: number;
    x1: number;
    x2: number;
    p_value: number;
    stars: string;
  };
  /** TS → React: switch to a different recipe file */
  switchFile: { path: string };
}

export type FigrecipeEventName = keyof FigrecipeEventMap;

// ── Typed emit / listen helpers ─────────────────────────────────

export function emitEvent<K extends FigrecipeEventName>(
  name: K,
  detail: FigrecipeEventMap[K],
): void {
  emitBridgeEvent(SLUG, name, detail);
}

export function onEvent<K extends FigrecipeEventName>(
  name: K,
  handler: (detail: FigrecipeEventMap[K]) => void,
): () => void {
  return onBridgeEvent(SLUG, name, handler);
}
