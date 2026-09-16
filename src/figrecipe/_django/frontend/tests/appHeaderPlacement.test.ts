/** App-header placement gate (scitex-ui 0.22.0 canonical, compass-impl L381 (a)).
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
const versionBadge = read(SRC, "components/FigrecipeVersionBadge.tsx");

// 1. Canonical app header exists in the editor tree.
check(
  "InnerEditor renders a .stx-app-header element",
  /<header\s+className="stx-app-header"/.test(inner),
);

// 2. The project selector is INSIDE the canonical slot, not the tab row.
check(
  "selector wrapped in .stx-app-header__slot--project-selector",
  /<div\s+className="stx-app-header__slot--project-selector">[\s\S]*?<ProjectScopeSelector\s*\/>[\s\S]*?<\/div>/.test(
    inner,
  ),
);
check(
  "ProjectScopeSelector appears exactly once (no duplicate picker)",
  (inner.match(/<ProjectScopeSelector\s*\/>/g) || []).length === 1,
);
check(
  "selector NOT in the tab row (moved out of .inner-editor__tabs)",
  !/<div className="inner-editor__tabs">[\s\S]*?<ProjectScopeSelector\s*\/>/.test(
    inner,
  ),
);

// 3. Exactly one title; the brand title is figrecipe's own.
check(
  "a header title element exists",
  /<span className="stx-app-header__title">/.test(inner),
);
check(
  "title is the invariant brand name 'FigRecipe' via gettext (not hardcoded EN/JA mix)",
  /gettext\("FigRecipe"\)/.test(inner),
);

// 4. Version is DERIVED, not hardcoded: resolved as the host-supplied prop ->
//    #root[data-version] -> __FIGRECIPE_VERSION__ (standalone leaf build).
check(
  "InnerEditor renders the version badge with its appVersion prop",
  /<FigrecipeVersionBadge\s+appVersion=\{appVersion\}\s*\/>/.test(inner),
);
check(
  "version falls back to build-derived __FIGRECIPE_VERSION__",
  /__FIGRECIPE_VERSION__/.test(versionBadge),
);
check(
  "version read from #root data-version attribute (standalone path)",
  /getAttribute\("data-version"\)/.test(versionBadge),
);
check(
  "version badge rendered conditionally (hidden only when all sources empty)",
  /if\s*\(!resolvedVersion\)\s*return null/.test(versionBadge),
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

// 6. Base header CSS exists (figrecipe owns the row; scitex-ui owns the slot).
const layout = read(SRC, "styles/layout.css");
check(
  "layout.css defines .stx-app-header, __title, and __version",
  /\.stx-app-header\s*{/.test(layout) &&
    /\.stx-app-header__title\s*{/.test(layout) &&
    /\.stx-app-header__version\s*{/.test(layout),
);

if (failures > 0) {
  console.error(`\n${failures} check(s) FAILED`);
  process.exit(1);
}
console.log("\nAll app-header placement checks passed.");
