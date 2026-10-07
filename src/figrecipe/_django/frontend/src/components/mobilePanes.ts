/** Stable SDK phone tabs: Data | Plot | Figure (composition canvas) | Details. */

import { useEffect, useState } from "react";
import {
  PHONE_QUERY,
  mountPanes as mountSdkPanes,
} from "@scitex/sdk/ui/ts/app/panes";
import type { Panes } from "@scitex/sdk/ui/ts/app/panes";
import "@scitex/sdk/ui/css/app/panes.css";

export type EditorPane = "figure" | "data" | "plot" | "details";

// The released SDK keeps a page registry without disposing detached roots.
// Keep the controller for each leaf root so StrictMode can rebind the same
// instance, and host DOM replacement cannot select a detached first instance.
const editors = new WeakMap<HTMLElement, Panes>();
let currentEditor: Panes | null = null;

export function mountEditorPanes(host: HTMLElement): Panes | null {
  const body = host.querySelector<HTMLElement>('[data-stx-panes="figrecipe"]');
  if (!body) return null;
  const panes = editors.get(body)
    ?? mountSdkPanes(host).find((item) => item.root === body)
    ?? null;
  if (panes) {
    editors.set(body, panes);
    currentEditor = panes;
  }
  return panes;
}

export function releaseEditorPanes(body: HTMLElement): void {
  if (currentEditor?.root === body) currentEditor = null;
}

/** Switch this leaf's connected phone root through the canonical SDK. */
export function showEditorPane(pane: EditorPane): void {
  if (currentEditor?.root.isConnected) currentEditor.show(pane);
}

function phoneQuery(): MediaQueryList | null {
  return typeof window !== "undefined" && typeof window.matchMedia === "function"
    ? window.matchMedia(PHONE_QUERY)
    : null;
}

/** True at the panes' phone breakpoint, where collapse title bars do not apply. */
export function usePhoneLayout(): boolean {
  const [phone, setPhone] = useState(() => Boolean(phoneQuery()?.matches));
  useEffect(() => {
    const media = phoneQuery();
    if (!media) return;
    const onChange = (e: MediaQueryListEvent) => setPhone(e.matches);
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);
  return phone;
}
