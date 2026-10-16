/** Mount-failure gate (live defect 2026-10-16: shell only, body never mounts).
 *
 * workspace.ts evaluates at module scope on the hub-embedded path. A
 * throwing mountFigrecipeEditor (undeclared/invalid app mount) used to
 * escape module evaluation: React never mounted, no error UI, and the
 * half-latched mountedContainer blocked every later retry. The fix:
 * mount in try/catch, render a role=alert error state into the
 * container, latch mountedContainer only after success, and keep the
 * workspace:module-injected subscription so a later injection retries.
 *
 * workspace.ts imports CSS + the React bridge chain, so it cannot run
 * under plain node here (no esbuild/SDK vendored); this gate asserts
 * the structure the same way csrfTokenOnMutatingCalls.test.ts does.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/workspaceMountError.test.ts
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = join(here, "..", "src");
const read = (rel: string) => readFileSync(join(SRC, rel), "utf8");

let failures = 0;
function check(name: string, cond: boolean) {
  if (cond) console.log(`  ok   ${name}`);
  else {
    console.log(`  FAIL ${name}`);
    failures += 1;
  }
}

const workspace = read("workspace.ts");
console.log("workspaceMountError:");

// The mount call is guarded: a throw resolves to UI, never escapes.
check(
  "mountFigrecipeEditor runs inside try",
  /try\s*\{\s*\n?\s*mountFigrecipeEditor\(\{/.test(workspace),
);
check(
  "mount failure renders renderMountError(container, …)",
  /catch\s*\([^)]*\)\s*\{[^}]*renderMountError\(container/.test(workspace),
);
// The error state is an assertive alert, not a silent blank.
check(
  "renderMountError sets role=alert",
  /function renderMountError[\s\S]*?setAttribute\("role",\s*"alert"\)/.test(
    workspace,
  ),
);
{
  const body = workspace.match(/function renderMountError[\s\S]*?\n\}/)?.[0] ?? "";
  check("renderMountError never rethrows", !/\bthrow\b/.test(body));
}
// Latch-after-success: a failed mount must not block later retries.
{
  const mountCall = workspace.indexOf("mountFigrecipeEditor({");
  const latch = workspace.indexOf("mountedContainer = container;");
  check(
    "mountedContainer latches only after a successful mount",
    mountCall >= 0 && latch > mountCall,
  );
}
// The retry rail stays intact: later host injections re-run the sync.
check(
  "workspace:module-injected subscription intact",
  /addEventListener\("workspace:module-injected",\s*syncWorkspaceMount\)/.test(
    workspace,
  ),
);
// The unmount path cannot kill module evaluation either.
check(
  "unmountFigrecipeEditor runs inside try",
  /try\s*\{\s*\n?\s*unmountFigrecipeEditor\(\)/.test(workspace),
);

if (failures) {
  console.error(`\n${failures} mount-error gate check(s) failed`);
  process.exit(1);
}
console.log(`\nall mount-error gates passed`);
