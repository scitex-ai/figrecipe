/** CSRF regression gate (live-audit finding #1: demo open refused HTTP 403).
 *
 * The hub mounts figrecipe behind Django's CSRF check and does NOT csrf_exempt
 * the mount (scitex-hub, 2026-09-14). The editor's POST/PATCH/DELETE calls did
 * not send the CSRF token, so e.g. api/gallery/demo 403'd. The fix: a shared
 * csrfToken() helper (reads Django's csrftoken cookie) attached to EVERY
 * non-GET API call.
 *
 * Source-conformance gate (Node, no framework): verifies the helper exists and
 * that each known mutating call site carries the X-CSRFToken header, so a
 * future refactor that drops the token on one endpoint fails loudly instead of
 * silently 403-ing again on the hub.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/csrfTokenOnMutatingCalls.test.ts
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

const client = read("api/client.ts");
const main = read("main.tsx");
const wsInt = read("bridge/WorkspaceIntegration.ts");
const chatAd = read("bootstrap/chatAdapter.ts");

console.log("csrfTokenOnMutatingCalls:");

// The shared helper exists and reads the csrftoken cookie.
check(
  "client.ts exports a csrfToken() helper",
  /export function csrfToken\(\)\s*:\s*string/.test(client),
);
check(
  "csrfToken() reads the csrftoken cookie",
  /csrftoken=/.test(client) && /document\.cookie/.test(client),
);
// The shared request() attaches the token for non-GET/HEAD methods.
check(
  "request() sets X-CSRFToken for mutating methods",
  /X-CSRFToken/.test(client) && /csrfToken\(\)/.test(client),
);
// postBlob (raw POST) attaches it too.
check(
  "postBlob attaches X-CSRFToken",
  /postBlob[\s\S]{0,400}X-CSRFToken/.test(client),
);

// Every known raw non-GET fetch site carries the token.
// (Each block: a `method: "POST|PATCH|DELETE"` near an X-CSRFToken header.)
const MUTATING = /method:\s*"(POST|PATCH|DELETE)"/g;
for (const [file, code] of [
  ["main.tsx", main],
  ["WorkspaceIntegration.ts", wsInt],
  ["chatAdapter.ts", chatAd],
] as const) {
  const sites = [...code.matchAll(MUTATING)];
  check(`${file}: found ${sites.length} mutating raw fetch site(s)`, sites.length > 0);
  for (const m of sites) {
    const idx = m.index ?? 0;
    // Look within ~140 chars after the method for the token header.
    const window_ = code.slice(idx, idx + 140);
    check(
      `${file}: ${m[1]} site sends X-CSRFToken`,
      /X-CSRFToken/.test(window_),
    );
  }
}

if (failures) {
  console.error(`\n${failures} CSRF gate check(s) failed`);
  process.exit(1);
}
console.log(`\nall CSRF gates passed`);
