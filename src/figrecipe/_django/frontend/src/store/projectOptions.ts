/** Pure logic that builds the scitex-ui ProjectSelector's options from
 * figrecipe's app-local project knowledge (TODO 145 / 147).
 *
 * The ProjectSelector SDK component owns the *pattern* (the dropdown, the
 * change event, the vocabulary); figrecipe owns the *data* — which projects
 * this app knows about and which one it is currently on. The data is app-local
 * (current working dir + recent projects, both namespaced figrecipe-* state),
 * NOT the hub's global "Current Project" list, so figrecipe controls "which
 * project to target" without depending on a forced global UI state.
 *
 * Pure and dependency-free (imports only a type), so it is unit-testable under
 * Node without React, the DOM, or the SDK component.
 */

import type { ProjectOption } from "@scitex/ui/src/scitex_ui/static/scitex_ui/ts/app/project-selector/types";

/** A directory's display name: its last path segment, or the raw path when it
 * has none (root or empty). */
export function projectDirName(dir: string): string {
  const d = dir.trim().replace(/\/+$/, "");
  if (d === "") return dir;
  const seg = d.split("/").filter(Boolean).pop();
  return seg && seg !== "" ? seg : d;
}

/** Build the selector's options from app-local knowledge.
 *
 * `current` (the project figrecipe is on right now) always comes first and is
 * the selected one; recent projects follow, most-recent first, deduped against
 * the current. Returns `{ options, currentId }` — `currentId` is null when
 * there is no current project (the selector then shows its placeholder).
 */
export function buildProjectOptions(
  current: string | null | undefined,
  recent: string[] = [],
): { options: ProjectOption[]; currentId: string | null } {
  const cur = (current ?? "").trim();
  const seen = new Set<string>();
  const options: ProjectOption[] = [];
  const push = (dir: string) => {
    const d = dir.trim();
    if (d === "" || seen.has(d)) return;
    seen.add(d);
    options.push({ id: d, name: projectDirName(d), detail: d });
  };
  if (cur) push(cur);
  for (const r of recent) push(r);
  return { options, currentId: cur || null };
}
