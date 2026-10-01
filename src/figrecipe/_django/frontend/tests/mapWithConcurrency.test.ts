/** Node test for the thumbnail-burst concurrency cap (site audit D2).
 *
 * The gallery must never open one connection per tile at once: at most `limit`
 * thumbnail requests may be in flight simultaneously. `mapWithConcurrency` is
 * the pure primitive that enforces that. Run under Node strip-types (no
 * React/DOM):
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/mapWithConcurrency.test.ts
 */
import assert from "node:assert/strict";
import { mapWithConcurrency } from "../src/utils/mapWithConcurrency.ts";

let passed = 0;
function ok(name: string, fn: () => void | Promise<void>) {
  const p = fn();
  return p.then
    ? p.then(() => {
        passed++;
        console.log("  ok - " + name);
      })
    : (fn(), passed++, console.log("  ok - " + name));
}

async function main() {
  console.log("mapWithConcurrency (D2 thumbnail burst cap):");

  await ok("empty input -> empty result, no work", async () => {
    const r = await mapWithConcurrency([], 4, async (x: number) => x * 2);
    assert.deepEqual(r, []);
  });

  await ok("results preserve input order regardless of completion order", async () => {
    // Reverse-order completion: item i resolves after (n - i) ticks, so the
    // last item finishes FIRST. Output must still be in input order.
    const r = await mapWithConcurrency([0, 1, 2, 3, 4], 2, async (i) => {
      await new Promise((res) => setTimeout(res, (4 - i) * 3));
      return i * 10;
    });
    assert.deepEqual(r, [0, 10, 20, 30, 40]);
  });

  await ok("at most `limit` tasks in flight simultaneously", async () => {
    let inFlight = 0;
    let peak = 0;
    await mapWithConcurrency([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 4, async () => {
      inFlight++;
      peak = Math.max(peak, inFlight);
      await new Promise((res) => setTimeout(res, 5));
      inFlight--;
    });
    assert.ok(peak <= 4, `peak was ${peak}, must be <= 4`);
    assert.ok(peak >= 2, `peak was ${peak}, expected real overlap (>=2)`);
  });

  await ok("limit larger than the input runs everything, still bounded by n", async () => {
    let inFlight = 0;
    let peak = 0;
    await mapWithConcurrency([1, 2, 3], 50, async () => {
      inFlight++;
      peak = Math.max(peak, inFlight);
      await new Promise((res) => setTimeout(res, 2));
      inFlight--;
    });
    assert.ok(peak <= 3, `peak was ${peak}, cannot exceed the 3 items`);
    assert.equal(peak, 3, "all 3 small items should overlap (peak == 3)");
  });

  await ok("index is passed correctly to fn", async () => {
    const r = await mapWithConcurrency(["a", "b", "c"], 2, async (item, i) => `${i}:${item}`);
    assert.deepEqual(r, ["0:a", "1:b", "2:c"]);
  });

  await ok("a per-item rejection does not abort the batch (caller swallows it)", async () => {
    // fn swallows its own errors (as the gallery thumbnail fetch does), so a
    // single bad item must not take the whole batch down. fn is (item, index);
    // make the item with value 2 fail -> it degrades to null, the rest resolve.
    const r = await mapWithConcurrency([1, 2, 3, 4], 2, async (item) => {
      try {
        if (item === 2) throw new Error("boom");
        return item;
      } catch {
        return null; // degrade to "no thumbnail", keep going
      }
    });
    assert.deepEqual(r, [1, null, 3, 4]);
  });

  await ok("an UNhandled rejection propagates (fail-loud when caller doesn't catch)", async () => {
    let threw = false;
    try {
      await mapWithConcurrency([1, 2], 2, async (i) => {
        if (i === 1) throw new Error("unhandled");
        return i;
      });
    } catch (e) {
      threw = true;
      assert.match(String(e), /unhandled/);
    }
    assert.equal(threw, true);
  });

  console.log("\n" + passed + " assertion-groups passed");
}

main().then(
  () => console.log("mapWithConcurrency: ok"),
  (e) => {
    console.error(e);
    process.exit(1);
  },
);
