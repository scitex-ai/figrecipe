/** App-local memory of the last project (working dir) FigRecipe opened.
 *
 * TODO 142 + 149: "each App remembers the Project it last used" and "the last
 * opened project may be persisted, but must be SEPARATE from the Global UI
 * state". The hub's global "Current Project" is injected per request
 * (?working_dir= / FIGRECIPE_WORKING_DIR) and is NOT FigRecipe's to own; this
 * is FigRecipe's own last-project preference, stored under a namespaced
 * `figrecipe-` key — the same app-local convention as `figrecipe-app-tab`,
 * `figrecipe-ruler-unit` and `figrecipe-session` — so it never leaks into, or
 * is overwritten by, the global header state.
 *
 * Pure and environment-defensive: every storage access is guarded, so the
 * module loads and degrades to no-op in a context with no localStorage (SSR,
 * a plain node run, a privacy mode) instead of throwing.
 */

export const LAST_PROJECT_KEY = "figrecipe-last-project";

function storage(): Storage | null {
  try {
    return typeof localStorage !== "undefined" ? localStorage : null;
  } catch {
    return null;
  }
}

/** Remember the project FigRecipe just opened. Ignored for empty/absent dirs. */
export function rememberLastProject(dir: string | null | undefined): void {
  if (typeof dir !== "string") return;
  const value = dir.trim();
  if (value === "") return;
  const s = storage();
  if (!s) return;
  try {
    s.setItem(LAST_PROJECT_KEY, value);
  } catch {
    // quota / serialization — non-critical, memory is best-effort
  }
}

/** The project FigRecipe last opened, or null when none is remembered. */
export function getLastProject(): string | null {
  const s = storage();
  if (!s) return null;
  try {
    const value = s.getItem(LAST_PROJECT_KEY);
    if (value === null) return null;
    const trimmed = value.trim();
    return trimmed === "" ? null : trimmed;
  } catch {
    return null;
  }
}

/** Forget the remembered project (used by tests and a future "clear" control). */
export function clearLastProject(): void {
  const s = storage();
  if (!s) return;
  try {
    s.removeItem(LAST_PROJECT_KEY);
  } catch {
    // ignore
  }
}
