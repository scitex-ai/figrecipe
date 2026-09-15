/** Phone tabs (scitex-ui panes) for the hub-mounted editor: Figure | Data | Plot | Details. */

import { useEffect, useState } from "react";
import {
  PHONE_QUERY,
  mountPanes,
  showPane,
} from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/app/panes";
import "@scitex/ui/src/scitex_ui/static/scitex_ui/css/app/panes.css";

export type EditorPane = "figure" | "data" | "plot" | "details";

export { mountPanes };

/** Switch the phone tab; a no-op before the panes mount (standalone). */
export function showEditorPane(pane: EditorPane): void {
  showPane(pane, "figrecipe");
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
