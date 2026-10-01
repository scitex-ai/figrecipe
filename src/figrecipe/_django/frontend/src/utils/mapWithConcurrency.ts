/** Run an async `fn` over `items` with at most `limit` in flight at once.
 *
 * Pure and dependency-free (no DOM, no React) so it is unit-testable under
 * Node strip-types, like the other gallery helpers.
 *
 * WHY THIS EXISTS (site audit D2): the gallery's `useGalleryTemplates` fired
 * one `api/gallery/thumbnail/<name>` request per template — ~18 at once per
 * session — and a shared hub with many concurrent sessions exhausted its
 * Postgres pool ("too many clients", 120 in 15 min), which then showed the
 * visitor "Could not load the example gallery". Capping in-flight requests to
 * a small constant bounds the per-session connection burst; the per-item
 * caller still decides what each result does and how a failure degrades.
 *
 * Contract:
 *   - at most `limit` promises of `fn` run simultaneously;
 *   - `results[i] === await fn(items[i], i)` (input order is preserved);
 *   - if `fn` rejects for some index, the caller's `fn` is expected to swallow
 *     it per-item (this helper does not turn one failure into a batch
 *     failure); an unhandled rejection still propagates via `Promise.all`.
 */
export async function mapWithConcurrency<T, R>(
  items: readonly T[],
  limit: number,
  fn: (item: T, index: number) => Promise<R>,
): Promise<R[]> {
  const results = new Array<R>(items.length);
  if (items.length === 0) return results;
  // A limit < 1 would deadlock the worker loop (no worker ever runs); clamp.
  const workerCount = Math.min(Math.max(1, limit), items.length);
  let next = 0;
  const workers: Promise<void>[] = [];
  for (let w = 0; w < workerCount; w++) {
    workers.push(
      (async () => {
        for (;;) {
          const i = next++;
          if (i >= items.length) break;
          results[i] = await fn(items[i], i);
        }
      })(),
    );
  }
  await Promise.all(workers);
  return results;
}
