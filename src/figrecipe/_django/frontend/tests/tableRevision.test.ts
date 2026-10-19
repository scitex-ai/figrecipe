/** Table-revision gate (card figrecipe-datatable-save-ordering-20261015).
 *
 * Defect: project saves were unconditional overwrites — a stale save
 * clobbered newer edits. The server now versions the stored table
 * (mtime-ns, opaque string) and refuses a write based on a superseded table
 * (409 + current revision). This gate pins the CLIENT half of the contract:
 * the pane sends its adopted revision as base_revision, adopts the revision
 * from every import response, and on 409 adopts the newer server table
 * (reload + toast) instead of re-sending the conflicted edit.
 *
 * Source-conformance gate (Node, no framework).
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/tableRevision.test.ts
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

const pane = read("components/DataTablePane/DataTablePane.tsx");
const client = read("api/client.ts");
const store = read("store/useEditorStore.ts");

console.log("tableRevision:");

// The queue write is conditional on the adopted revision.
check(
  "pane sends base_revision on queued saves",
  pane.includes("base_revision"),
);
check(
  "pane adopts the revision from the import response",
  /datatable\/import[\s\S]*?datatableRevision/.test(pane),
);

// A 409 adopts the newer server table — never re-sends the conflicted edit.
check(
  "pane branches on 409 conflicts",
  /status === 409/.test(pane),
);
check(
  "409 path reloads the newer table",
  /409[\s\S]*?loadDatatable\(\)/.test(pane),
);
check(
  "409 path toasts instead of reporting a generic save failure",
  /another session/.test(pane),
);

// The client exposes what the branch needs: status + body.
check(
  "ApiError carries the HTTP status",
  /class ApiError[\s\S]*?status:\s*number/.test(client),
);
check(
  "ApiError carries the server error body",
  /class ApiError[\s\S]*?body:\s*unknown/.test(client),
);

// The store holds the adopted revision; loads refresh it.
check(
  "store holds datatableRevision",
  store.includes("datatableRevision: string | null"),
);
check(
  "loadDatatable refreshes the revision from the data response",
  /data\.revision/.test(store),
);

if (failures > 0) {
  console.error(`\n${failures} check(s) FAILED`);
  process.exit(1);
}
console.log("\nAll table-revision checks passed.");
