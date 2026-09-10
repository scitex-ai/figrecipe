/** App-local recent-projects memory (TODO 142 / 145 / 147 / 149).
 *
 * figrecipe owns a small, namespaced record of the projects it has recently
 * worked in, independent of the hub's global "Current Project" state. This is
 * the app-local data that feeds the shared scitex-ui ProjectSelector: the
 * *pattern* (the dropdown) comes from the SDK; the *data* (which projects this
 * app knows about) comes from here.
 *
 * A namespaced `figrecipe-` localStorage key, the same app-local convention as
 * `figrecipe-last-project` / `figrecipe-app-tab` / `figrecipe-session` — so it
 * is stored yet SEPARATE from the global UI state (TODO 149). Pure and
 * environment-defensive: every storage access is guarded, so it no-ops safely
 * with no localStorage (SSR, plain node, privacy mode).
 */

export const RECENT_PROJECTS_KEY = "figrecipe-recent-projects";
export const RECENT_PROJECTS_MAX = 8;

function storage(): Storage | null {
  try {
    return typeof localStorage !== "undefined" ? localStorage : null;
  } catch {
    return null;
  }
}

/** Record that figrecipe just worked in `dir`. Idempotent (moves it to the
 * front), bounded, ignores empty/absent values. */
export function addRecentProject(dir: string | null | undefined): void {
  if (typeof dir !== "string") return;
  const value = dir.trim();
  if (value === "") return;
  const s = storage();
  if (!s) return;
  try {
    const existing = readRecentRaw(s).filter((d) => d !== value);
    existing.unshift(value);
    s.setItem(RECENT_PROJECTS_KEY, JSON.stringify(existing.slice(0, RECENT_PROJECTS_MAX)));
  } catch {
    /* quota / serialization — best-effort */
  }
}

/** The app's recent projects, most-recent first (never throws). */
export function getRecentProjects(): string[] {
  const s = storage();
  if (!s) return [];
  return readRecentRaw(s);
}

/** Forget all recent projects (used by tests and a future "clear" control). */
export function clearRecentProjects(): void {
  const s = storage();
  if (!s) return;
  try {
    s.removeItem(RECENT_PROJECTS_KEY);
  } catch {
    /* ignore */
  }
}

function readRecentRaw(s: Storage): string[] {
  try {
    const raw = s.getItem(RECENT_PROJECTS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((d): d is string => typeof d === "string")
      .map((d) => d.trim())
      .filter((d) => d !== "");
  } catch {
    return [];
  }
}
