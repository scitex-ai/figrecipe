/** Mount latch/retry gate (live defect 2026-10-16: shell only, body never mounts).
 *
 * workspace.ts evaluates at module scope on the hub-embedded path. A
 * throwing mountFigrecipeEditor used to escape module evaluation AND
 * half-latch mountedContainer, blocking every later retry. The kept
 * correction: mount in try/catch (log + return unlatched), latch only
 * after success, keep the workspace:module-injected subscription so a
 * later injection retries.
 *
 * Operator order 2026-10-16: STOP leaf-side error-state additions — the
 * shared error-state primitive will live in the SDK. This gate enforces
 * that: workspace.ts must contain NO leaf error UI (no role=alert, no
 * mount-error DOM).
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

// The mount call is guarded: a throw logs and returns, never escapes.
check(
  "mountFigrecipeEditor runs inside try",
  /try\s*\{\s*\n?\s*mountFigrecipeEditor\(\{/.test(workspace),
);
check(
  "mount failure path returns without latching",
  /catch\s*\([^)]*\)\s*\{[^}]*console\.error\([^)]*mount failed[^)]*\)[^}]*return;/.test(
    workspace,
  ),
);
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
// Operator stop-order: NO leaf-owned error-state UI in workspace.ts.
check(
  "no leaf error UI (no renderMountError)",
  !/renderMountError/.test(workspace),
);
check("no leaf error UI (no role=alert)", !/role=.alert/.test(workspace));
check(
  "no leaf error UI (no mount-error DOM class)",
  !/mount-error/.test(workspace),
);

if (failures) {
  console.error(`\n${failures} mount-error gate check(s) failed`);
  process.exit(1);
}
console.log(`\nall mount-error gates passed`);
