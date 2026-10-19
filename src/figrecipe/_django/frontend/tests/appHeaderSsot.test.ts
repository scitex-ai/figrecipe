/** SSoT header-row gate (operator CCT4254, card figrecipe-ssot-header-row-20261017).
 *
 * FigRecipe templates carried only asset refs — no shared `.stx-app-header`
 * row. The fix adopts the SDK SSoT header like Storage PR #128 / Writer
 * editor.html: a `_app_header.html` partial (leaf VALUES, SDK chrome),
 * included by standalone.html + workspace_partial.html under the
 * `app_header_rendered` host guard, with InnerEditor yielding its owned row
 * and portaling the live picker into the server slot while a
 * `header[data-ssot]` row is present.
 *
 * Source-conformance gate (Node, no framework).
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/appHeaderSsot.test.ts
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const FRONTEND = join(here, "..");
const SRC = join(FRONTEND, "src");
const TPL = join(FRONTEND, "..", "templates", "figrecipe");
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

const partial = read(TPL, "_app_header.html");
const standalone = read(TPL, "standalone.html");
const workspacePartial = read(TPL, "workspace_partial.html");
const inner = read(SRC, "InnerEditor.tsx");

console.log("appHeaderSsot:");

// The partial is the shared row: SDK chrome, leaf values.
check(
  "partial links the SDK app-header.css (no leaf fork)",
  partial.includes("scitex_sdk/ui/css/app/app-header.css"),
);
check(
  "partial renders header.stx-app-header marked data-ssot",
  /<header[^>]*class="[^"]*stx-app-header[^"]*"[^>]*data-ssot/.test(partial) ||
    /<header[^>]*data-ssot[^>]*class="[^"]*stx-app-header/.test(partial),
);
check(
  "partial carries leaf title + version badge",
  partial.includes("stx-app-header__title") &&
    partial.includes("stx-app-header__version") &&
    partial.includes("app_version"),
);
check(
  "partial keeps the picker + actions slots",
  partial.includes("stx-app-header__slot--project-selector") &&
    partial.includes("stx-app-header__actions"),
);
check(
  "partial hides the badge when no version was passed (never a wrong badge)",
  /{%\s*if\s+app_version\s*%}/.test(partial),
);

// Standalone shell owns NO server header row (operator CCT4601): the row
// the templates used to include rendered as a first title above the
// React-owned fallback header (which renders whenever no server SSoT row
// is present) — two stacked "FigRecipe v…" rows. Standalone therefore
// renders no server row; the owned React header is the single header.
// The hub-embedded partial keeps the SSoT row for its mount (host mount
// path untouched), and InnerEditor still portals the live picker into any
// server slot when one is present.
check(
  "standalone.html renders no server header row (React-owned row is single)",
  !standalone.includes('figrecipe/_app_header.html'),
);
for (const [name, tpl] of [["workspace_partial.html", workspacePartial]] as const) {
  check(
    `${name} includes the SSoT partial`,
    tpl.includes('{% include "figrecipe/_app_header.html" %}'),
  );
  check(
    `${name} honors the app_header_rendered host guard`,
    /{%\s*if\s+not\s+app_header_rendered\s*%}[\s\S]*?figrecipe\/_app_header\.html/.test(
      tpl,
    ),
  );
}

// React yields: owned row renders only with NO server SSoT row present,
// and the single live picker portals into the server slot otherwise.
check(
  "InnerEditor queries the server SSoT row",
  inner.includes("header.stx-app-header[data-ssot]"),
);
check(
  "InnerEditor portals the picker into the server slot when present",
  inner.includes("createPortal(picker, ssotSlot)"),
);
check(
  "owned header is the fallback path, not an additional row",
  /if\s*\(ssotSlot\)\s*return\s+createPortal/.test(inner),
);

if (failures > 0) {
  console.error(`\n${failures} check(s) FAILED`);
  process.exit(1);
}
console.log("\nAll app-header SSoT checks passed.");
