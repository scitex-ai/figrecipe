/** The Data pane's save queue: serialised, revision-gated table writes.
 *
 * `datatable/import` REPLACES the stored table, so two properties decide what a
 * project ends up keeping and what the user sees next. Neither was guaranteed:
 *
 *   1. SERIALISED. Every edit used to fire its own POST. A burst of edits — type
 *      in three cells, add a row, add a column before the first response
 *      returned — put overlapping writes in the air, and whichever response
 *      landed last decided the stored table, which is not necessarily the newest
 *      one on screen.
 *
 *   2. REVISION-GATED. After a write the pane reloads the table from the server,
 *      because that is the only proof the edit really landed. A reload that
 *      belongs to an edit which has since been superseded would put the OLDER
 *      table back on screen, and the next edit would write that older table back
 *      to the server. So each edit gets a revision, and a completion may only be
 *      ADOPTED when no newer edit has been handed over.
 *
 * The queue keeps one write in flight, coalesces the edits that arrive while it
 * runs to the newest one (only the newest table has to reach the server), and
 * answers EVERY caller: a coalesced edit is reported "superseded" rather than
 * left hanging.
 *
 * React-free and injectable — the caller supplies the write — so the ordering,
 * coalescing and the gate are asserted under `node --experimental-strip-types`
 * with a fake write (tests/tableSaveQueue.test.ts).
 */

/** What became of one edit's write.
 *
 *  - "applied": the write landed and nothing newer was handed over, so the
 *    caller may adopt the server's state (reload the table, show the toast).
 *  - "superseded": a newer edit replaced this one in the queue. Nothing to show;
 *    the newer edit's own completion speaks for the table.
 *  - "failed": the write rejected. The caller reports it and must NOT adopt the
 *    server's state — the server never accepted this table.
 */
export type SaveStatus = "applied" | "superseded" | "failed";

export interface SaveOutcome {
  /** This edit's revision: 1, 2, 3… in the order the pane handed edits over. */
  revision: number;
  status: SaveStatus;
  /** The rejection reason, for "failed". */
  error?: unknown;
}

export interface TableSaveQueue {
  /** Hand a serialised table to the queue; resolves when this edit's write
   *  settles, supersedes, or fails. Never rejects. */
  enqueue(csv: string): Promise<SaveOutcome>;
  /** The newest revision handed over (0 before any edit). A caller that captured
   *  a revision can use it to ignore a response a newer edit has overtaken. */
  readonly revision: number;
  /** A write is running, or one is waiting. */
  readonly busy: boolean;
  /** Resolves once nothing is running and nothing is waiting. */
  idle(): Promise<void>;
}

export function createTableSaveQueue(
  write: (csv: string) => Promise<void>,
): TableSaveQueue {
  interface Job {
    revision: number;
    csv: string;
    settle: (outcome: SaveOutcome) => void;
  }

  let revision = 0;
  /** The revision of the write in flight, or null when the queue is idle. */
  let running: number | null = null;
  /** At most ONE waiting job: newer edits replace it instead of stacking up. */
  let waiting: Job | null = null;
  let idleWaiters: (() => void)[] = [];

  const drainIdleWaiters = (): void => {
    if (running !== null || waiting !== null) return;
    const waiters = idleWaiters;
    idleWaiters = [];
    for (const resolve of waiters) resolve();
  };

  const finish = (job: Job, failed: boolean, error?: unknown): void => {
    running = null;
    if (failed) {
      job.settle({ revision: job.revision, status: "failed", error });
    } else {
      // A completion may only be adopted when nothing newer has been handed
      // over; otherwise the caller would reload an older table over a newer edit.
      const superseded = job.revision < revision;
      job.settle({
        revision: job.revision,
        status: superseded ? "superseded" : "applied",
      });
    }
    pump();
    drainIdleWaiters();
  };

  /** Start the waiting job when the queue is free. */
  function pump(): void {
    if (running !== null || waiting === null) return;
    const job = waiting;
    waiting = null;
    running = job.revision;
    write(job.csv).then(
      () => finish(job, false),
      (error: unknown) => finish(job, true, error),
    );
  }

  return {
    get revision(): number {
      return revision;
    },

    get busy(): boolean {
      return running !== null || waiting !== null;
    },

    enqueue(csv: string): Promise<SaveOutcome> {
      revision += 1;
      const job: Job = { revision, csv, settle: () => {} };
      const outcome = new Promise<SaveOutcome>((resolve) => {
        job.settle = resolve;
      });
      // Coalesce: an edit that arrives while another is waiting replaces it —
      // only the newest table has to reach the server. The replaced caller is
      // answered now, so awaiting it cannot hang forever.
      if (waiting) {
        waiting.settle({ revision: waiting.revision, status: "superseded" });
      }
      waiting = job;
      pump();
      return outcome;
    },

    idle(): Promise<void> {
      if (running === null && waiting === null) return Promise.resolve();
      return new Promise<void>((resolve) => {
        idleWaiters.push(resolve);
      });
    },
  };
}
