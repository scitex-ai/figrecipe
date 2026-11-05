/** App-header placement gate (public SDK 0.3.18 canonical ownership).
 *
 * Hub ruling (9/16, both-owner confirmation): the 'dotfiles' dropdown on the
 * /apps/figrecipe mount is FIGRECIPE's own ProjectScopeSelector (A), NOT a hub
 * global selector. figrecipe must relocate that existing selector into the
 * canonical .stx-app-header__slot--project-selector and NOT add a second
 * picker/provider. figrecipe's OWN version (from figrecipe.__version__,
 * stamped by the Django view onto #root data-version) sits beside its own
 * title, distinct from the Hub global header's Hub-version.
 *
 * Source-conformance gate (Node, no framework): verifies the canonical header
 * placement actually happened and stayed — a future refactor that re-drops the
 * selector into the tab row, duplicates the title/picker, or hardcodes the
 * version fails loudly.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/appHeaderPlacement.test.ts
 */

import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const FRONTEND = join(here, "..");
const SRC = join(FRONTEND, "src");
const DJANGO = join(FRONTEND, ".."); // the _django package (parent of frontend)
const read = (base: string, rel: string) =>
  readFileSync(join(base, rel), "utf8");

let failures = 0;
function check(name: string, cond: boolean) {
  if (cond) console.log(`  ok   ${name}`);
  else {
    failures++;
    console.error(`  FAIL ${name}`);
  }
}

const inner = read(SRC, "InnerEditor.tsx");

// The leaf delegates rendering to the SDK React binding, or portals the same
// picker into the SDK-owned server row. The real editorAppHeader.spec.ts suite
// exercises both paths under React StrictMode, including rerender and unmount.
const bridge = read(SRC, "components/EditorAppHeader.tsx");
check("InnerEditor delegates its title/version/picker to EditorAppHeader",
  /<EditorAppHeader\s+title=\{gettext\("FigRecipe"\)\}\s+version=\{resolvedVersion\}/.test(inner) &&
  /projectSelector=\{<ProjectScopeSelector\s*\/>\}/.test(inner));
check("editor has no handwritten shared header markup",
  !/<header\b/.test(inner) && !/<(?:span|div)\s+className="stx-app-header__/.test(inner));
check("one project selector is declared, outside the tab row",
  (inner.match(/<ProjectScopeSelector\s*\/>/g) || []).length === 1 &&
  !/<div className="inner-editor__tabs"[\s\S]*?<ProjectScopeSelector\s*\/>/.test(inner));
check("SPA bridge uses the public SDK AppHeader binding",
  /import\s*\{\s*AppHeader\s*\}\s*from\s*"@scitex\/sdk\/ui\/react\/app\/app-header"/.test(bridge) &&
  /<AppHeader\s+title=\{title\}\s+version=\{version\}\s+projectSelector=\{projectSelector\}/.test(bridge));
check("server bridge mounts the SDK row and portals into its canonical slot",
  /mountAppHeader\(region,\s*\{\s*projectSlot:\s*true\s*\}\)/.test(bridge) &&
  /serverRoot\.querySelector<HTMLElement>\("\.stx-app-header__slot--project-selector"\)/.test(bridge) &&
  /createPortal\(projectSelector,\s*slot\)/.test(bridge));
check("bridge never duplicates the shared header renderer",
  !/<header\b/.test(bridge) && !/<(?:span|div)\s+className="stx-app-header__/.test(bridge));

// 4. Version is DERIVED, not hardcoded: resolved as prop -> #root
//    [data-version] -> __FIGRECIPE_VERSION__ (build-time from pyproject.toml).
//    The baked constant covers the Hub #app-mount path where neither a prop
//    nor #root[data-version] is present.
check(
  "version falls back to build-derived __FIGRECIPE_VERSION__ (covers #app-mount)",
  /__FIGRECIPE_VERSION__/.test(inner),
);
check(
  "version read from #root data-version attribute (standalone path)",
  /getAttribute\("data-version"\)/.test(inner),
);
check(
  "resolved version is delegated to the SDK-owned badge",
  /<EditorAppHeader[\s\S]*?version=\{resolvedVersion\}/.test(inner),
);

// 5. The Django view stamps data-version from figrecipe.__version__ (the
//    source of truth), and the template carries it onto #root.
const views = read(DJANGO, "views.py");
check(
  "editor_page derives app_version from figrecipe.__version__",
  /from figrecipe import __version__ as app_version/.test(views) &&
    /"app_version":\s*app_version/.test(views),
);
const template = read(DJANGO, "templates/figrecipe/standalone.html");
check(
  "standalone.html #root carries data-version from the context",
  /data-version="{\{\s*app_version\|default:''\s*\}}"/.test(template),
);

// 6. Base header CSS comes from the SDK SSoT (no leaf override per [infra/fig-header]).
const layout = read(SRC, "styles/layout.css");
check(
  "layout.css carries no .stx-app-header override (SDK SSoT owns it)",
  !/\.stx-app-header\s*{/.test(layout) &&
    !/\.stx-app-header__title\s*{/.test(layout) &&
    !/\.stx-app-header__version\s*{/.test(layout),
);

if (failures > 0) {
  console.error(`\n${failures} check(s) FAILED`);
  process.exit(1);
}
console.log("\nAll app-header placement checks passed.");
