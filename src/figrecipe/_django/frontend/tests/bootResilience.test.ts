/** Boot-resilience gate (figrecipe-boot-resilience-20261016).
 *
 * The app-shell init fetch paths (file tree, repo monitor) run at module
 * scope beside the React render. Every failure class — blocked fetch
 * (reject), HTTP error, malformed body — must resolve to the degraded
 * value the HTTP-error path already returned, never an unhandled
 * rejection that leaves a shell pane empty.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/bootResilience.test.ts
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  createFileTreeFetcher,
  createRecentFilesFetcher,
} from "../src/bootstrap/bootFetch.ts";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = join(here, "..", "src");
const read = (rel: string) => readFileSync(join(SRC, rel), "utf8");

let passed = 0;
async function ok(name: string, fn: () => void | Promise<void>) {
  await fn();
  passed++;
  console.log(`  ok   ${name}`);
}

// The helper module stays dependency-free (importable without SDK/DOM).
ok("bootFetch stays importable under node --experimental-strip-types", () => {
  const source = read("bootstrap/bootFetch.ts");
  assert.doesNotMatch(source, /from\s+["']react["']/);
  assert.doesNotMatch(source, /from\s+["']@scitex\/sdk/);
  assert.doesNotMatch(source, /\bdocument\./);
  assert.doesNotMatch(source, /\bwindow\./);
});

const apiUrl = (endpoint: string) => `http://test/${endpoint}`;
const blockedFetch = () => Promise.reject(new TypeError("fetch failed"));
const httpError = () =>
  Promise.resolve({
    ok: false,
    status: 500,
    statusText: "Internal Server Error",
    json: () => Promise.resolve({}),
  });
const malformedBody = () =>
  Promise.resolve({
    ok: true,
    status: 200,
    statusText: "OK",
    json: () => Promise.reject(new SyntaxError("Unexpected token")),
  });

// fileTree: blocked fetch degrades, never rejects.
await ok("fetchTree resolves success:false on blocked fetch", async () => {
  const { fetchTree } = createFileTreeFetcher({
    fetchImpl: blockedFetch,
    apiUrl,
  });
  const result = await fetchTree();
  assert.equal(result.success, false);
  assert.deepEqual(result.tree, []);
  assert.match(result.error ?? "", /fetch failed/);
});

// fileTree: HTTP error keeps the established degraded contract.
await ok("fetchTree resolves success:false on HTTP error", async () => {
  const { fetchTree } = createFileTreeFetcher({ fetchImpl: httpError, apiUrl });
  const result = await fetchTree("some/dir");
  assert.equal(result.success, false);
  assert.deepEqual(result.tree, []);
  assert.match(result.error ?? "", /HTTP 500/);
});

// fileTree: malformed body degrades instead of throwing.
await ok("fetchTree resolves success:false on malformed body", async () => {
  const { fetchTree } = createFileTreeFetcher({
    fetchImpl: malformedBody,
    apiUrl,
  });
  const result = await fetchTree();
  assert.equal(result.success, false);
  assert.deepEqual(result.tree, []);
});

// fileTree: healthy path still passes data through.
await ok("fetchTree passes tree + rootPath through on success", async () => {
  const seen: string[] = [];
  const { fetchTree } = createFileTreeFetcher({
    fetchImpl: (url: string) => {
      seen.push(url);
      return Promise.resolve({
        ok: true,
        status: 200,
        statusText: "OK",
        json: () =>
          Promise.resolve({ tree: [{ path: "a.yaml" }], working_dir: "/proj" }),
      });
    },
    apiUrl,
  });
  const root = await fetchTree();
  assert.equal(root.success, true);
  assert.deepEqual(root.tree, [{ path: "a.yaml" }]);
  assert.equal(root.rootPath, "/proj");
  const sub = await fetchTree("sub/dir");
  assert.match(seen[1], /working_dir=sub%2Fdir/);
});

// repo monitor: every failure class degrades to [].
await ok("fetchRecentFiles resolves [] on blocked fetch", async () => {
  const { fetchRecentFiles } = createRecentFilesFetcher({
    fetchImpl: blockedFetch,
    apiUrl,
  });
  assert.deepEqual(await fetchRecentFiles(), []);
});

await ok("fetchRecentFiles resolves [] on HTTP error", async () => {
  const { fetchRecentFiles } = createRecentFilesFetcher({
    fetchImpl: httpError,
    apiUrl,
  });
  assert.deepEqual(await fetchRecentFiles(), []);
});

// repo monitor: healthy path keeps the established normalization.
await ok("fetchRecentFiles normalizes entries on success", async () => {
  const { fetchRecentFiles } = createRecentFilesFetcher({
    fetchImpl: () =>
      Promise.resolve({
        ok: true,
        status: 200,
        statusText: "OK",
        json: () =>
          Promise.resolve({
            files: [
              { path: "fig.yaml", modified_at: "2026-10-16T00:00:00Z" },
              { path: "sub/b.yaml", name: "b", mtime: "2026-10-15T00:00:00Z" },
            ],
          }),
      }),
    apiUrl,
  });
  const files = await fetchRecentFiles();
  assert.equal(files.length, 2);
  assert.equal(files[0].name, "fig.yaml");
  assert.equal(files[0].modified_at, "2026-10-16T00:00:00Z");
  assert.equal(files[1].name, "b");
  assert.equal(files[1].modified_at, "2026-10-15T00:00:00Z");
});

// main.tsx must never inject the bare global: a detached `fetch` reference
// loses its Window receiver and throws "Illegal invocation" on first call
// (Files pane, 2026-10-19 — card
// figrecipe-files-pane-fetch-illegal-invocation-20261019). The injected impl
// must call fetch as a bare global (arrow) or carry a bound receiver.
await ok("main.tsx injects a bound fetch, never the bare global", () => {
  const main = read("main.tsx");
  assert.doesNotMatch(main, /fetchImpl:\s*fetch\s*[,}]/);
});

console.log(`\nall boot-resilience checks passed (${passed} assertion-groups).`);
