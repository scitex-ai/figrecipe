/** Node test for the example-seed rule (card
 * figrecipe-data-column-and-plot-variant-ux-20260916 / spec scitex-hub PR 923).
 *
 * The empty-canvas surface used to POST `api/gallery/demo` by itself on mount,
 * and the server seeds a demo recipe plus its data directory into the workspace
 * — example artifacts written into a project because a pane rendered, which the
 * Private Beta spec forbids ("Create or import a project explicitly; never
 * silently select an example").
 *
 * The rule is now a transition table in `exampleSeed`: nothing can start a seed
 * except an explicit user request. That property, and the wiring that relies on
 * it, are checked here.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/exampleSeed.test.ts
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  isSeeding,
  nextSeedState,
  offersExampleSeed,
  type SeedEvent,
  type SeedState,
} from "../src/components/Gallery/exampleSeed.ts";

const STATES: SeedState[] = ["idle", "seeding", "open", "unavailable"];
const EVENTS: SeedEvent[] = [
  "user-request",
  "seed-opened",
  "seed-declined",
  "seed-failed",
];

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

console.log("example seed (explicit, never automatic):");

ok("only an explicit request starts a seed, from every state", () => {
  const startedByImplicit = EVENTS.filter((e) => e !== "user-request").filter(
    (e) => nextSeedState("idle", e) !== "idle",
  );
  assert.deepEqual(startedByImplicit, []);
});

ok("a seed event arriving unbidden is a no-op in every state but seeding", () => {
  const leaked = STATES.filter((s) => s !== "seeding").flatMap((s) =>
    EVENTS.map((e) => [s, e] as const).filter(([st, ev]) => {
      const next = nextSeedState(st, ev);
      return ev !== "user-request" && next !== st;
    }),
  );
  assert.deepEqual(leaked, []);
});

ok("an explicit request moves idle -> seeding", () => {
  assert.equal(nextSeedState("idle", "user-request"), "seeding");
});

ok("a second click while seeding does not fire a second write", () => {
  assert.equal(nextSeedState("seeding", "user-request"), "seeding");
  assert.equal(nextSeedState("open", "user-request"), "open");
});

ok("a successful seed opens; a declined or failed one is unavailable", () => {
  assert.equal(nextSeedState("seeding", "seed-opened"), "open");
  assert.equal(nextSeedState("seeding", "seed-declined"), "unavailable");
  assert.equal(nextSeedState("seeding", "seed-failed"), "unavailable");
});

ok("the spinner belongs to a seed the user asked for", () => {
  assert.equal(isSeeding("seeding"), true);
  for (const s of ["idle", "open", "unavailable"] as SeedState[]) {
    assert.equal(isSeeding(s), false);
  }
});

ok("the offer is spent once the seed has run", () => {
  assert.equal(offersExampleSeed("idle"), true);
  for (const s of ["seeding", "open", "unavailable"] as SeedState[]) {
    assert.equal(offersExampleSeed(s), false);
  }
});

// ---- the wiring relies on that rule -------------------------------------
//
// Operator batch apps-figrecipe-ui-feedback-20261023 item 2: the example
// block is gone, so NO UI surface may start a seed at all. The state
// machine above still guards the module (the rule holds for any future
// caller); this block pins that GalleryStart carries zero seed call sites.

ok("GalleryStart starts no seed from anywhere (example block removed)", () => {
  const src = readFileSync(
    join(
      dirname(fileURLToPath(import.meta.url)),
      "..",
      "src",
      "components",
      "Gallery",
      "GalleryStart.tsx",
    ),
    "utf8",
  );
  // No seeding function, no seed state, no effect that could run one.
  const calls = src.match(/openDemoFigure\(/g) ?? [];
  assert.equal(calls.length, 0, `expected 0 seed call sites, found ${calls.length}`);
  assert.doesNotMatch(src, /nextSeedState|offersExampleSeed|isSeedingState/);
  assert.doesNotMatch(src, /useEffect/);
});

console.log("\n" + passed + " assertion-groups passed");
