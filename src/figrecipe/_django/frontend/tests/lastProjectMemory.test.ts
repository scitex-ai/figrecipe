/** Node test for the app-local last-project memory (TODO 142 + 149).
 *
 * There is no JS test runner in the figrecipe frontend (CI gates the build
 * with `npx vite build`, not vitest/jest), so this is a self-contained script
 * run directly under Node's TypeScript strip-types:
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/lastProjectMemory.test.ts
 *
 * It exercises the pure module (no DOM, no store) against an in-memory
 * localStorage stub, then against an ABSENT localStorage to prove the
 * environment-defensive no-op path.
 */

import assert from "node:assert/strict";

import {
  LAST_PROJECT_KEY,
  rememberLastProject,
  getLastProject,
  clearLastProject,
} from "../src/store/lastProjectMemory.ts";

// ── in-memory localStorage stub ─────────────────────────────────────────
function makeLocalStorage(): Storage {
  const map = new Map<string, string>();
  return {
    getItem: (k) => (map.has(k) ? map.get(k)! : null),
    setItem: (k, v) => void map.set(k, String(v)),
    removeItem: (k) => void map.delete(k),
    clear: () => map.clear(),
    key: (i) => [...map.keys()][i] ?? null,
    get length() {
      return map.size;
    },
  };
}

let storage = makeLocalStorage();
Object.defineProperty(globalThis, "localStorage", {
  value: storage,
  configurable: true,
  writable: true,
});

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log(`  ok - ${name}`);
}

console.log("lastProjectMemory (with localStorage):");

ok("persists a remembered project under the namespaced key", () => {
  clearLastProject();
  rememberLastProject("/home/u/proj/alpha");
  assert.equal(storage.getItem(LAST_PROJECT_KEY), "/home/u/proj/alpha");
});

ok("reads it back", () => {
  assert.equal(getLastProject(), "/home/u/proj/alpha");
});

ok("overwrites on the next project (last-wins)", () => {
  rememberLastProject("/home/u/proj/beta");
  assert.equal(getLastProject(), "/home/u/proj/beta");
});

ok("clears", () => {
  clearLastProject();
  assert.equal(getLastProject(), null);
});

ok("returns null when nothing has been remembered", () => {
  assert.equal(getLastProject(), null);
});

ok("ignores null / undefined / empty / whitespace-only (no crash, no write)", () => {
  rememberLastProject(null);
  rememberLastProject(undefined);
  rememberLastProject("");
  rememberLastProject("   ");
  assert.equal(getLastProject(), null);
  assert.equal(storage.getItem(LAST_PROJECT_KEY), null);
});

ok("trims surrounding whitespace before storing", () => {
  rememberLastProject("  /home/u/proj/gamma  ");
  assert.equal(getLastProject(), "/home/u/proj/gamma");
  clearLastProject();
});

ok("is SEPARATE from other figrecipe app keys (global-UI-state isolation)", () => {
  // Simulate unrelated app state living in the same storage.
  storage.setItem("figrecipe-app-tab", "plot");
  storage.setItem("figrecipe-session", '{"x":1}');
  rememberLastProject("/home/u/proj/delta");
  // The remembered project does not touch, and is not touched by, those keys.
  assert.equal(getLastProject(), "/home/u/proj/delta");
  assert.equal(storage.getItem("figrecipe-app-tab"), "plot");
  assert.equal(storage.getItem("figrecipe-session"), '{"x":1}');
  clearLastProject();
  assert.equal(getLastProject(), null);
  assert.equal(storage.getItem("figrecipe-app-tab"), "plot"); // untouched by clear
});

console.log("lastProjectMemory (NO localStorage — must no-op safely):");

// Remove the global to exercise the environment-defensive path.
delete (globalThis as { localStorage?: Storage }).localStorage;
ok("rememberLastProject is a no-op and does not throw", () => {
  rememberLastProject("/home/u/proj/ephemeral"); // must not throw
});
ok("getLastProject returns null", () => {
  assert.equal(getLastProject(), null);
});
ok("clearLastProject is a no-op and does not throw", () => {
  clearLastProject();
});

console.log(`\n${passed} assertions-groups passed`);
