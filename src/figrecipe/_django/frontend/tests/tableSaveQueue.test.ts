/** Node test for the Data pane's save queue: serialised, revision-gated writes.
 *
 * `datatable/import` REPLACES the stored table, so the order the pane's saves
 * arrive in decides what the project keeps, and the state the pane reads back is
 * what the user sees next. Both were left to chance: a burst of edits fired
 * overlapping POSTs (last response wins, not newest table), and every response
 * reloaded the table even when a newer edit was already on its way back.
 *
 * The queue is written against an injected `write`, so ordering, coalescing and
 * the gate are asserted here without React, a server or a clock. The queue's
 * decisions are asynchronous by nature, so this file runs its checks in order
 * and awaits each one.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/tableSaveQueue.test.ts
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  createTableSaveQueue,
  type SaveOutcome,
} from "../src/components/DataTablePane/tableSaveQueue.ts";

const checks: { name: string; body: () => unknown }[] = [];
function ok(name: string, body: () => unknown) {
  checks.push({ name, body });
}

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel: string) =>
  readFileSync(join(here, "..", "src", rel), "utf8");

/** A write the test controls: records the order it was called in, and how many
 *  writes were running at once. */
function controlledWrite() {
  const calls: string[] = [];
  const resolvers: (() => void)[] = [];
  const rejecters: ((error: unknown) => void)[] = [];
  let concurrent = 0;
  let maxConcurrent = 0;

  const write = (csv: string) => {
    calls.push(csv);
    concurrent += 1;
    maxConcurrent = Math.max(maxConcurrent, concurrent);
    return new Promise<void>((resolve, reject) => {
      resolvers.push(() => {
        concurrent -= 1;
        resolve();
      });
      rejecters.push((error) => {
        concurrent -= 1;
        reject(error);
      });
    });
  };

  return {
    write,
    calls,
    maxConcurrent: () => maxConcurrent,
    /** Complete the nth write (0-based) successfully. */
    finish: (n: number) => resolvers[n](),
    fail: (n: number, error: unknown = new Error("boom")) => rejecters[n](error),
  };
}

/** Let the queue's promise chain run. */
const tick = () => new Promise((resolve) => setTimeout(resolve, 0));

console.log("tableSaveQueue:");

// ── serialisation ─────────────────────────────────────────────────────────

ok("two edits never write at the same time", async () => {
  // Arrange
  const io = controlledWrite();
  const queue = createTableSaveQueue(io.write);
  // Act: the second edit arrives while the first write is still running.
  const first = queue.enqueue("a");
  const second = queue.enqueue("b");
  // Assert: only the first write has started, and nothing else is in flight.
  assert.deepEqual(io.calls, ["a"]);
  assert.equal(io.maxConcurrent(), 1);
  // Act: the first completes; the queued edit goes next.
  io.finish(0);
  await tick();
  assert.deepEqual(io.calls, ["a", "b"]);
  assert.equal(io.maxConcurrent(), 1);
  io.finish(1);
  // Assert: both callers were answered — neither is left hanging.
  const outcomes = await Promise.all([first, second]);
  assert.deepEqual(
    outcomes.map((o) => [o.revision, o.status]),
    [
      [1, "superseded"],
      [2, "applied"],
    ],
  );
});

ok("a burst of edits coalesces to the newest one", async () => {
  // Arrange
  const io = controlledWrite();
  const queue = createTableSaveQueue(io.write);
  // Act: five edits while the first write runs (a paste, then typing).
  const edits = ["e1", "e2", "e3", "e4", "e5"].map((csv) => queue.enqueue(csv));
  io.finish(0);
  await tick();
  io.finish(1);
  const outcomes = await Promise.all(edits);
  // Assert: the first and the newest were written; the middle ones were
  // superseded rather than queued up.
  assert.deepEqual(io.calls, ["e1", "e5"]);
  assert.deepEqual(
    outcomes.map((o) => o.status),
    ["superseded", "superseded", "superseded", "superseded", "applied"],
  );
  // ...and the newest edit is the one the caller may adopt.
  assert.equal(outcomes[4].revision, 5);
});

ok("revisions count the edits the pane handed over, newest last", async () => {
  // Arrange
  const io = controlledWrite();
  const queue = createTableSaveQueue(io.write);
  assert.equal(queue.revision, 0);
  // Act
  const first = queue.enqueue("a");
  assert.equal(queue.revision, 1);
  const second = queue.enqueue("b");
  assert.equal(queue.revision, 2);
  io.finish(0);
  await tick();
  io.finish(1);
  // Assert
  assert.equal((await first).revision, 1);
  assert.equal((await second).revision, 2);
  assert.equal(queue.revision, 2);
});

ok("an edit made after the queue drained is applied again", async () => {
  // Arrange
  const io = controlledWrite();
  const queue = createTableSaveQueue(io.write);
  // Act: a quiet save…
  const first = queue.enqueue("a");
  io.finish(0);
  const firstOutcome: SaveOutcome = await first;
  // …then a later, unrelated edit.
  const second = queue.enqueue("b");
  io.finish(1);
  const secondOutcome = await second;
  // Assert: the gate is about a NEWER edit, not about how many were made.
  assert.equal(firstOutcome.status, "applied");
  assert.equal(secondOutcome.status, "applied");
});

// ── failures ──────────────────────────────────────────────────────────────

ok("a failed write is reported with its error and does not block the queue", async () => {
  // Arrange
  const io = controlledWrite();
  const queue = createTableSaveQueue(io.write);
  const error = new Error("Save failed: HTTP 500");
  // Act
  const failed = queue.enqueue("a");
  const next = queue.enqueue("b");
  io.fail(0, error);
  await tick();
  io.finish(1);
  const [firstOutcome, secondOutcome] = await Promise.all([failed, next]);
  // Assert: the caller gets the error to show, and the newer edit still ran.
  assert.equal(firstOutcome.status, "failed");
  assert.equal(firstOutcome.error, error);
  assert.equal(secondOutcome.status, "applied");
  assert.deepEqual(io.calls, ["a", "b"]);
});

ok("the newest edit failing is a failure, never an adoption", async () => {
  // Arrange: adopting the server state after a failed write would put a table
  // the server never accepted back on screen.
  const io = controlledWrite();
  const queue = createTableSaveQueue(io.write);
  // Act
  const outcome = queue.enqueue("a");
  io.fail(0);
  const settled = await outcome;
  // Assert
  assert.equal(settled.status, "failed");
});

ok("a failed write leaves the queue usable", async () => {
  // Arrange
  const io = controlledWrite();
  const queue = createTableSaveQueue(io.write);
  // Act
  const first = queue.enqueue("a");
  io.fail(0);
  await first;
  const second = queue.enqueue("b");
  io.finish(1);
  const settled = await second;
  // Assert
  assert.equal(settled.status, "applied");
  assert.equal(queue.busy, false);
});

// ── busy / idle ───────────────────────────────────────────────────────────

ok("busy is true from the first edit until the last write settles", async () => {
  // Arrange
  const io = controlledWrite();
  const queue = createTableSaveQueue(io.write);
  assert.equal(queue.busy, false);
  // Act / Assert
  const first = queue.enqueue("a");
  assert.equal(queue.busy, true);
  io.finish(0);
  await first;
  assert.equal(queue.busy, false);
});

ok("idle resolves only once nothing is running or waiting", async () => {
  // Arrange
  const io = controlledWrite();
  const queue = createTableSaveQueue(io.write);
  let drained = false;
  // Act: two edits, then wait for the queue to drain.
  queue.enqueue("a");
  queue.enqueue("b");
  const idle = queue.idle().then(() => {
    drained = true;
  });
  await tick();
  assert.equal(drained, false, "a write is still running");
  // Assert: the queued edit keeps the queue busy after the first completes.
  io.finish(0);
  await tick();
  assert.equal(drained, false, "the coalesced edit is still to write");
  io.finish(1);
  await idle;
  assert.equal(drained, true);
  assert.equal(queue.busy, false);
});

// ── the pane must actually use it ─────────────────────────────────────────

ok("every table write goes through the queue", () => {
  // Arrange
  const pane = read("components/DataTablePane/DataTablePane.tsx");
  // Act / Assert: one write path, so no edit can bypass serialisation. The
  // queue's write is the one that carries a serialised table; a user-file
  // import (handleImportCsv) is a different gesture with its own payload.
  assert.match(pane, /createTableSaveQueue\(/);
  assert.match(
    pane,
    /createTableSaveQueue\(async \(csv: string\) => \{[\s\S]{0,240}?api\.post\("datatable\/import", \{ content: csv, format: "csv" \}\)/,
  );
  assert.match(
    pane,
    /const persistTable = useCallback\(\s*async \(table: TableModel, message: string\) => \{[\s\S]*?await saveQueue\.enqueue\(serializeTableToCsv\(table\)\);/,
  );
});

ok("the pane adopts the server's table only for an applied save", () => {
  // Arrange
  const pane = read("components/DataTablePane/DataTablePane.tsx");
  // Act / Assert
  assert.match(pane, /if \(outcome\.status === "failed"\)/);
  assert.match(pane, /if \(outcome\.status !== "applied"\) return;/);
  // The reload sits behind that gate.
  assert.ok(
    pane.indexOf('if (outcome.status !== "applied") return;') <
      pane.indexOf("await loadDatatable("),
    "the reload must not run for a superseded or failed save",
  );
});

ok("the reload is gated against an edit that lands while it is in flight", () => {
  // Arrange: the response of an older read must not overwrite a newer edit that
  // reached the store while that read was running.
  const pane = read("components/DataTablePane/DataTablePane.tsx");
  const store = read("store/useEditorStore.ts");
  // Act / Assert
  assert.match(pane, /const revision = outcome\.revision;/);
  assert.match(
    pane,
    /loadDatatable\(\{ isCurrent: \(\) => saveQueue\.revision === revision \}\)/,
  );
  assert.match(store, /isCurrent\?: \(\) => boolean/);
  assert.match(store, /if \(isCurrent && !isCurrent\(\)\) return;/);
});

ok("a user-file import waits for pending table edits to drain", () => {
  // Arrange: an import writes the SAME stored table, so an edit still in the
  // queue would otherwise land after it and overwrite the chosen file.
  const pane = read("components/DataTablePane/DataTablePane.tsx");
  // Act / Assert
  assert.match(
    pane,
    /const handleImportCsv = useCallback\(\s*async \(file: File\) => \{[\s\S]*?await saveQueue\.idle\(\);[\s\S]*?await api\.post\("datatable\/import", \{ content, format \}\);/,
  );
});

// ── module hygiene ────────────────────────────────────────────────────────

ok("the module stays importable under node --experimental-strip-types", () => {
  // Arrange
  const source = read("components/DataTablePane/tableSaveQueue.ts");
  // Act / Assert — no React, no app alias, no DOM, and no timers of its own:
  // the ordering is a promise chain, not a setTimeout.
  assert.doesNotMatch(source, /from\s+["']react["']/);
  assert.doesNotMatch(source, /from\s+["']@scitex\/ui/);
  assert.doesNotMatch(source, /gettext\s*\(/);
  assert.doesNotMatch(source, /\bdocument\./);
  assert.doesNotMatch(source, /setTimeout|setInterval/);
});

// ── run (the queue's decisions are asynchronous) ──────────────────────────

(async () => {
  let passed = 0;
  for (const check of checks) {
    await check.body();
    passed++;
    console.log("  ok - " + check.name);
  }
  console.log(
    "\nAll table-save-queue checks passed (" + passed + " assertion-groups).",
  );
})().catch((error: unknown) => {
  console.error(error);
  process.exit(1);
});
