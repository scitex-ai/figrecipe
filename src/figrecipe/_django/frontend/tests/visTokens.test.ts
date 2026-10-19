/** vis-token namespace gate (ssot-ui-standard item 3, card
 * figrecipe-ssot-ui-standard-20261016).
 *
 * Audit item: "--vis-* namespace throughout instead of SDK theme tokens —
 * map onto SDK primitives/colors + shell/theme.css". The mapping lives in
 * styles/app-variables.css as pure aliases: every --vis-* definition
 * resolves to an SDK token (--workspace-*, --text-*, --status-*,
 * --app-accent-*, --color-*), so the 200+ usages already render SDK values.
 * A bulk rename to --workspace-* names would be zero-value churn.
 *
 * This gate pins the alias layer: no --vis-* definition may introduce a
 * leaf-local literal, except the documented brand exceptions below.
 *
 * Source-conformance gate (Node, no framework).
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/visTokens.test.ts
 */

import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = join(here, "..", "src");
const read = (rel: string) => readFileSync(join(SRC, rel), "utf8");

let failures = 0;
function check(name: string, cond: boolean) {
  if (cond) console.log(`  ok   ${name}`);
  else {
    failures++;
    console.error(`  FAIL ${name}`);
  }
}

// Deliberate leaf-local values (brand, not theme): changing these to SDK
// tokens would erase figrecipe's own accent wash.
const BRAND_EXCEPTIONS = new Set(["--vis-accent-bg"]);

// SDK token namespaces a --vis-* alias may resolve to.
const SDK_NS = /var\(\s*--(workspace-|text-|status-|app-accent-|color-)/;

const vars = read("styles/app-variables.css");
const defs = [...vars.matchAll(/^\s*(--vis-[a-z-]+)\s*:\s*([^;]+);/gm)];

console.log("visTokens:");
check("vis tokens are defined in exactly one layer", defs.length > 0);

const offenders = defs.filter(
  ([, name, value]) =>
    !BRAND_EXCEPTIONS.has(name) && !SDK_NS.test(value),
);
check(
  "every --vis-* resolves to an SDK token (except brand allowlist)",
  offenders.length === 0,
);
for (const [, name, value] of offenders) {
  console.error(`  offender ${name}: ${value.trim()}`);
}

function cssFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((e: string) => {
    const p = join(dir, e);
    if (statSync(p).isDirectory()) return cssFiles(p);
    return p.endsWith(".css") ? [p] : [];
  });
}
const stray = cssFiles(join(SRC, "styles"))
  .filter((f) => !f.endsWith("app-variables.css"))
  .filter((f) => /^\s*--vis-[a-z-]+\s*:/m.test(readFileSync(f, "utf8")));
check("no --vis-* redefined outside app-variables.css", stray.length === 0);
for (const f of stray) console.error(`  redefines: ${f}`);

if (failures > 0) {
  console.error(`\n${failures} check(s) FAILED`);
  process.exit(1);
}
console.log("\nAll vis-token checks passed.");
