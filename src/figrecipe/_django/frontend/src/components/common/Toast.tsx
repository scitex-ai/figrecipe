/** Toast notification component. */

import { useEditorStore } from "../../store/useEditorStore";

export function Toast() {
  const { toast, clearToast } = useEditorStore();

  // Errors are surfaced by the AlertBanner (persistent, fail-loud); the toast
  // handles only transient info/success notifications.
  if (!toast || toast.type === "error") return null;

  return (
    <div className={`toast toast--${toast.type}`} onClick={clearToast}>
      {toast.message}
    </div>
  );
}
