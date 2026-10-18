/** Load-error retry gate (card figrecipe-error-fallback-ui-20261016).
 *
 * Remainder after PR #458 (mount leg): a FAILED data load left a silently
 * empty table — the load failure was console.warn only, and the empty state
 * was indistinguishable from "no data yet" with no way to retry. The store
 * now records the failure (datatableLoadError, cleared on the next load)
 * and the Data pane renders it as an explanatory alert with a Retry button
 * that re-runs the load.
 *
 * Source-conformance gate (Node, no framework).
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/loadErrorRetry.test.ts
 */

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
    failures++;
    console.error(`  FAIL ${name}`);
  }
}

const store = read("store/useEditorStore.ts");
const pane = read("components/DataTablePane/DataTablePane.tsx");

console.log("loadErrorRetry:");

// The store records the failure instead of swallowing it.
check(
  "store holds datatableLoadError",
  store.includes("datatableLoadError: string | null"),
);
check(
  "failed load records a user-facing message",
  /datatableLoadError:\s*gettext\(/.test(store),
);
check(
  "new load clears the previous failure",
  /loadDatatable[\s\S]*?set\(\{\s*datatableLoadError:\s*null\s*\}\)/.test(store),
);

// The pane turns the failure into an explanatory state with a retry.
check(
  "pane reads the load error",
  pane.includes("datatableLoadError"),
);
check(
  "failed load renders as an alert, not a silent empty state",
  /role=\{datatableLoadError \? "alert"/.test(pane),
);
check(
  "pane offers a Retry button on load failure",
  />\s*\{gettext\("Retry"\)\}/.test(pane),
);
check(
  "retry re-runs the load",
  /onClick=\{\(\) => void loadDatatable\(\)\}/.test(pane),
);

if (failures > 0) {
  console.error(`\n${failures} check(s) FAILED`);
  process.exit(1);
}
console.log("\nAll load-error retry checks passed.");
