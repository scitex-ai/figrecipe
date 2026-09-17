/**
 * resolveAppVersion — the leaf's single source for the header version badge.
 *
 * Dependency-free (no React/JSX/DOM) so it can be imported and exercised by the
 * Node `--experimental-strip-types` host-consumer regression test, where the
 * build-time constant `__FIGRECIPE_VERSION__` is genuinely ABSENT (no Vite
 * `define` runs). That is exactly the Hub #app-mount situation: the Hub compiles
 * figrecipe's bridge frontend with ITS OWN Vite config, which does not bake in
 * figrecipe's version, so the constant is undefined there.
 *
 * Priority:
 *   1. `stamped` — the `data-app-version` mount metadata attribute the host
 *      reads from the leaf's #app-mount container and stamps generically (the
 *      Hub stamps the installed leaf version; not FigRecipe-specific). This is
 *      the value that EXISTS on the Hub mount path.
 *   2. `__FIGRECIPE_VERSION__` — derived from pyproject.toml and baked in by
 *      figrecipe's own Vite `define` (standalone build / a host that runs the
 *      leaf's own build). Referenced via `typeof` so an absent constant neither
 *      throws nor yields a literal-undefined version.
 *
 * Returns `undefined` when neither source yields a value, so the caller omits
 * the `appVersion` prop entirely and `InnerEditor` runs its own resolution
 * chain (prop -> #root[data-version] -> build constant -> "").
 */
export function resolveAppVersion(
  stamped: string | null | undefined,
): string | undefined {
  if (stamped !== null && stamped !== undefined) {
    const s = stamped.trim();
    if (s !== "") return s;
  }
  const built =
    typeof __FIGRECIPE_VERSION__ !== "undefined" ? __FIGRECIPE_VERSION__ : undefined;
  if (built !== null && built !== undefined) {
    const b = String(built).trim();
    if (b !== "") return b;
  }
  return undefined;
}
