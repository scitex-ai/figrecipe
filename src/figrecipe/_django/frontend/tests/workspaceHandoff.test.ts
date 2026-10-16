/** Hub-path workspace handoff gate (live defect 2026-10-16).
 *
 * Lead-verified root cause: the hub-served page loads the index.js bundle
 * ONLY, never workspace.js, so the body never mounts. The fix: when this
 * standalone bundle lands on a hub-embedded figrecipe container instead of
 * its own #root, it dynamically imports the workspace sync and skips the
 * standalone shell init (no #root to mount into; the standalone shell must
 * not drive the host's DOM).
 *
 * main.tsx imports CSS + the React bridge chain, so it cannot run under
 * plain node here (no esbuild/SDK vendored); this gate asserts the
 * structure the same way csrfTokenOnMutatingCalls.test.ts does. Real
 * browser behavior is verified separately with the esbuild harness
 * (see the card).
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/workspaceHandoff.test.ts
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

const main = read("main.tsx");
console.log("workspaceHandoff:");

// The handoff fires only when there is no #root AND a hub-embedded
// figrecipe container is present — never on the standalone page,
// never on unrelated pages that happen to load the bundle.
check(
  "handoff gated on missing #root plus embedded figrecipe container",
  /if\s*\(\s*!root\s*&&\s*document\.querySelector\('\[data-app-slug="figrecipe"\]\[data-embedded="true"\]'\)\s*\)/.test(
    main,
  ),
);
// The handoff pulls in the workspace sync (separate chunk), and a failed
// pull never kills module evaluation.
check(
  "handoff dynamically imports ./workspace with a caught failure",
  /await\s+import\("\.\/workspace"\)\.catch\(/.test(main),
);
// The standalone shell init is skipped without #root.
{
  const handoffAt = main.indexOf('await import("./workspace")');
  const guardAt = main.indexOf("if (root) {\nconst figrecipeFileTreeAdapter");
  check(
    "standalone shell init wrapped in if (root) after the handoff",
    handoffAt >= 0 && guardAt > handoffAt,
  );
}
check(
  "standalone init block closed at end of module",
  /end if \(root\): standalone shell init only/.test(main),
);

if (failures) {
  console.error(`\n${failures} handoff gate check(s) failed`);
  process.exit(1);
}
console.log(`\nall handoff gates passed`);
