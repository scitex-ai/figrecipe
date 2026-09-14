/** Adoption gate: figrecipe consumes the scitex-ui app-scope selector via the
 * SDK primitive and does NOT fork the selector (operator ledger #48, #140-149;
 * scitex-ui PR #227 / d931ff4).
 *
 * The no-fork ruling is a source-conformance gate: ProjectScopeSelector.tsx
 * must import `mountProjectSelectorByScope` from the SDK shell and must not
 * instantiate `new ProjectSelector(` itself. Run with:
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/appScopeAdoption.test.ts
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = join(here, "..", "src", "components", "ProjectScopeSelector.tsx");

const code = readFileSync(SRC, "utf8");

let failures = 0;
function check(name: string, cond: boolean) {
  if (cond) {
    console.log(`  ok  ${name}`);
  } else {
    console.log(`  FAIL ${name}`);
    failures += 1;
  }
}

console.log("appScopeAdoption:");
check(
  "imports mountProjectSelectorByScope from the SDK shell",
  /mountProjectSelectorByScope[\s\S]*from\s*["']@scitex\/ui\/[^"']*\/ts\/shell/.test(
    code,
  ),
);
check(
  "imports PROJECT_SELECTOR_CHANGE from the SDK shell (not a fork)",
  /PROJECT_SELECTOR_CHANGE[\s\S]*from\s*["']@scitex\/ui\/[^"']*\/ts\/shell/.test(
    code,
  ),
);
check(
  "does NOT instantiate new ProjectSelector( itself (no fork)",
  !/new\s+ProjectSelector\s*\(/.test(code),
);
check(
  "does NOT import the raw ProjectSelector class (the fork path)",
  !/import\s*[\s\S]*?\bProjectSelector\b[\s\S]*?from\s*["']@scitex\/ui\/[^"']*\/app\/project-selector/.test(
    code,
  ),
);
check(
  "still mounts into a local container (app-local surface, not the header)",
  /mountProjectSelectorByScope\s*\(/.test(code) && /container:\s*host/.test(code),
);

if (failures) {
  console.error(`\n${failures} adoption-gate check(s) failed`);
  process.exit(1);
}
console.log(`\nall adoption gates passed`);
