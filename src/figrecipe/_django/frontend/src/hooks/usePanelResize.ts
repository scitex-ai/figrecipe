/**
 * Panel resize + collapse hook — React port of vis_app WorkspacePanelResizer.
 *
 * Features:
 * - Drag resize via mousedown on resizer element
 * - Auto-collapse when dragged to minWidth
 * - Explicit collapse/expand button (the pane header renders `.panel-toggle-btn`)
 * - Drag from collapsed state auto-expands
 * - localStorage persistence for width + collapsed state
 *
 * Collapse is driven by a visible button, not a double-click gesture:
 * double-click was a hidden affordance discoverable only by trial.
 */

import { useCallback, useEffect, useRef, useState } from "react";

export interface PanelResizeConfig {
  direction: "left" | "right";
  minWidth: number;
  defaultWidth: number;
  storageKey: string;
  collapseKey: string;
}

export interface PanelResizeResult {
  width: number;
  collapsed: boolean;
  panelRef: React.RefObject<HTMLElement | null>;
  resizerProps: {
    onMouseDown: (e: React.MouseEvent) => void;
  };
  toggleCollapse: () => void;
}

function readStorage(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* quota exceeded — ignore */
  }
}

export function usePanelResize(config: PanelResizeConfig): PanelResizeResult {
  const { direction, minWidth, defaultWidth, storageKey, collapseKey } = config;

  // Restore initial state from localStorage
  const [width, setWidth] = useState(() => {
    const saved = readStorage(storageKey);
    if (saved) {
      const w = parseInt(saved, 10);
      if (w >= minWidth) return w;
    }
    return defaultWidth;
  });

  const [collapsed, setCollapsed] = useState(() => {
    return readStorage(collapseKey) === "true";
  });

  // Refs for drag state (avoid re-renders during drag)
  const dragging = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(0);
  const wasCollapsed = useRef(false);

  // Persist width changes
  const saveWidth = useCallback(
    (w: number) => {
      writeStorage(storageKey, w.toString());
    },
    [storageKey],
  );

  // Persist collapse state
  const saveCollapsed = useCallback(
    (c: boolean) => {
      writeStorage(collapseKey, c.toString());
    },
    [collapseKey],
  );

  // Toggle collapse/expand
  const toggleCollapse = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      saveCollapsed(next);
      if (!next) {
        // Expanding: restore saved width
        const saved = readStorage(storageKey);
        if (saved) {
          const w = parseInt(saved, 10);
          if (w > minWidth + 10) {
            setWidth(w);
            return next;
          }
        }
        setWidth(defaultWidth);
      }
      return next;
    });
  }, [saveCollapsed, storageKey, minWidth, defaultWidth]);

  // Mouse handlers for drag resize
  const onMouseDown = useCallback(
    (e: React.MouseEvent) => {
      wasCollapsed.current = collapsed;

      // If collapsed, auto-expand first
      if (collapsed) {
        setCollapsed(false);
        saveCollapsed(false);
        setWidth(minWidth);
      }

      dragging.current = true;
      startX.current = e.clientX;
      startWidth.current = collapsed ? minWidth : width;

      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      e.preventDefault();
    },
    [collapsed, width, minWidth, saveCollapsed],
  );

  // Track live width during drag via ref (no React re-renders)
  const liveWidth = useRef(0);
  const panelRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!dragging.current) return;
      const delta = e.clientX - startX.current;
      const newWidth =
        direction === "left"
          ? startWidth.current + delta
          : startWidth.current - delta;

      if (newWidth >= minWidth) {
        liveWidth.current = newWidth;
        // Direct DOM update for smooth drag (no React re-render)
        if (panelRef.current) {
          panelRef.current.style.width = `${newWidth}px`;
        }
      } else {
        liveWidth.current = minWidth;
        // Panel at minimum — propagate force to workspace shell
        window.dispatchEvent(
          new CustomEvent("stx-app-resize-overflow", {
            detail: {
              direction: direction === "left" ? "left" : "right",
              delta: minWidth - newWidth,
              clientX: e.clientX,
            },
          }),
        );
      }
    };

    const onMouseUp = (e: MouseEvent) => {
      if (!dragging.current) return;
      // Apply final mouse position (fixes fast drag not reaching destination)
      onMouseMove(e);
      dragging.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";

      const finalWidth = liveWidth.current;
      if (finalWidth <= minWidth + 10) {
        // Auto-collapse
        setCollapsed(true);
        saveCollapsed(true);
        setWidth(defaultWidth);
      } else {
        setWidth(finalWidth);
        saveWidth(finalWidth);
      }

      wasCollapsed.current = false;
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
  }, [direction, minWidth, defaultWidth, saveWidth, saveCollapsed]);

  return {
    width,
    collapsed,
    panelRef,
    resizerProps: { onMouseDown },
    toggleCollapse,
  };
}
