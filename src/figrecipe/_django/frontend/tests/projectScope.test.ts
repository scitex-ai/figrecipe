/** Node tests for figrecipe's app-local project-scope logic (TODO 142/145/147/149).
 *
 * The SDK ProjectSelector owns the pattern; figrecipe owns the data. This
 * exercises the two pure, figrecipe-owned pieces — the recent-projects memory
 * and the option builder — under Node strip-types (no React/DOM/SDK):
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/projectScope.test.ts
 */

import assert from "node:assert/strict";

import {
  RECENT_PROJECTS_KEY,
  addRecentProject,
  getRecentProjects,
  clearRecentProjects,
} from "../src/store/recentProjects.ts";
import {
  buildProjectOptions,
  projectDirName,
} from "../src/store/projectOptions.ts";

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

const storage = makeLocalStorage();
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

console.log("projectDirName:");
ok("last segment is the name", () => assert.equal(projectDirName("/home/u/proj/alpha"), "alpha"));
ok("trailing slashes are stripped", () => assert.equal(projectDirName("/home/u/proj/alpha/"), "alpha"));
ok("a bare name is its own name", () => assert.equal(projectDirName("alpha"), "alpha"));
ok("root '/' falls back to the raw path", () => assert.equal(projectDirName("/"), "/"));

console.log("addRecentProject / getRecentProjects (TODO 142/149):");
ok("records and returns most-recent-first", () => {
  clearRecentProjects();
  addRecentProject("/p/one");
  addRecentProject("/p/two");
  assert.deepEqual(getRecentProjects(), ["/p/two", "/p/one"]);
});
ok("is idempotent (re-adding moves to front, no dup)", () => {
  addRecentProject("/p/one");
  assert.deepEqual(getRecentProjects(), ["/p/one", "/p/two"]);
});
ok("is bounded", () => {
  clearRecentProjects();
  for (let i = 0; i < 20; i++) addRecentProject(`/p/${i}`);
  assert.ok(getRecentProjects().length <= 8);
});
ok("is stored under a namespaced figrecipe- key (separate from global state)", () => {
  assert.ok(RECENT_PROJECTS_KEY.startsWith("figrecipe-"));
  assert.ok(storage.getItem(RECENT_PROJECTS_KEY) !== null);
  // and it does NOT collide with other figrecipe app keys
  storage.setItem("figrecipe-last-project", "/p/x");
  assert.ok(storage.getItem("figrecipe-last-project") === "/p/x");
  assert.ok(storage.getItem(RECENT_PROJECTS_KEY)!.startsWith("["));
});
ok("ignores null/undefined/empty/whitespace without writing", () => {
  clearRecentProjects();
  addRecentProject(null);
  addRecentProject(undefined);
  addRecentProject("");
  addRecentProject("   ");
  assert.deepEqual(getRecentProjects(), []);
  assert.equal(storage.getItem(RECENT_PROJECTS_KEY), null);
});
ok("clears", () => {
  addRecentProject("/p/keep");
  clearRecentProjects();
  assert.deepEqual(getRecentProjects(), []);
});

console.log("buildProjectOptions (TODO 145/147):");
ok("current first + selected; recents after, deduped", () => {
  clearRecentProjects();
  addRecentProject("/p/b");
  addRecentProject("/p/a"); // most recent first now
  const { options, currentId } = buildProjectOptions("/p/a", getRecentProjects());
  assert.equal(currentId, "/p/a");
  assert.equal(options[0].id, "/p/a");
  assert.equal(options[0].name, "a");
  assert.equal(options[0].detail, "/p/a");
  // a appears once; b after it
  assert.deepEqual(
    options.map((o) => o.id),
    ["/p/a", "/p/b"],
  );
});
ok("no current → null currentId, recents still listed", () => {
  clearRecentProjects();
  addRecentProject("/p/only");
  const { options, currentId } = buildProjectOptions(null, getRecentProjects());
  assert.equal(currentId, null);
  assert.deepEqual(options.map((o) => o.id), ["/p/only"]);
});
ok("empty knowledge → empty options, null current", () => {
  clearRecentProjects();
  const { options, currentId } = buildProjectOptions(undefined, []);
  assert.deepEqual(options, []);
  assert.equal(currentId, null);
});
ok("trims/ignores blank recents and dedupes current-vs-recent", () => {
  clearRecentProjects();
  const { options } = buildProjectOptions(" /p/x ", [" /p/x", "/p/y", "  "]);
  assert.deepEqual(options.map((o) => o.id), ["/p/x", "/p/y"]);
});

console.log(`\n${passed} assertion-groups passed`);
