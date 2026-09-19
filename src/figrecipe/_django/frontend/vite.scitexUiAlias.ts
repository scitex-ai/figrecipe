import { execSync } from "child_process";

/**
 * The `@scitex/ui` alias every figrecipe build must use.
 *
 * The contract (scripts/maintenance/setup-worktree-frontend-deps.sh, and the
 * frontend-build CI leg): `@scitex/ui` resolves to the OWNER REPO ROOT, so
 * `@scitex/ui/src/scitex_ui/static/scitex_ui/<module>` is a real file path.
 * figrecipe's sources import the owner's source that way, and it is what makes
 * directory modules (`react/app/data-table`, `ts/shell`, …) resolve through
 * their `index.ts` — the package's own `exports` map points `./src/*` at the
 * same files but requires a FILE target, so an extensionless directory import
 * only resolves under this alias.
 *
 * BOTH vite configs use this helper on purpose: when only the app build had it,
 * the library build failed on the same specifiers the app build resolved — two
 * resolvers disagreeing about where the owner is, which is the drift this
 * dependency alignment exists to remove.
 *
 * Discovery order: SCITEX_UI_STATIC (explicit, used by CI and Docker) then the
 * installed python package (pip-installed or editable), matching the historical
 * behaviour of vite.config.ts.
 */
export function discoverScitexUiStatic(): string {
  if (process.env.SCITEX_UI_STATIC) {
    return process.env.SCITEX_UI_STATIC;
  }
  try {
    const pkgPath = execSync(
      'python3 -c "import scitex_ui; print(scitex_ui.get_static_dir())"',
      { encoding: "utf-8", timeout: 5000 },
    ).trim();
    if (pkgPath) return pkgPath;
  } catch {
    // scitex_ui not installed — fall through to the error below.
  }
  throw new Error(
    "scitex-ui not found. Install it (pip install scitex-ui) or set SCITEX_UI_STATIC env var.",
  );
}

/** `@scitex/ui` -> the owner repo root, as both configs and tsconfig expect. */
export function scitexUiAlias(): Record<string, string> {
  const staticDir = discoverScitexUiStatic();
  return {
    "@scitex/ui": staticDir.replace(/\/src\/scitex_ui\/static\/scitex_ui$/, ""),
  };
}
