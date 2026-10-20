/** Stored-theme gate (card figrecipe-dark-theme-forced-20261018).
 *
 * Defect: with `stx-theme=light` stored, FigRecipe reset to dark on every
 * load — main.tsx stamped `data-theme="dark"` unconditionally at boot,
 * clobbering the value the shell theme boot had resolved pre-paint from
 * localStorage (`stx-theme`, fallback `scitex-theme-preference`, else the
 * shell default). Same root as Stats.
 *
 * Contract after the fix: the standalone entry only stamps the legacy dark
 * default when NO theme was resolved at all (raw SPA fallback with no shell
 * boot) — a stored preference is never overwritten. Storage reads are
 * guarded so blocked storage cannot break the mount.
 *
 * Source-conformance gate (Node, no framework).
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/themePreference.test.ts
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

const main = read("main.tsx");
console.log("themePreference:");

// The defect pattern: an unconditional dark stamp at boot.
check(
  "no unconditional data-theme=dark stamp (the defect)",
  !/document\.documentElement\.setAttribute\(\s*"data-theme",\s*"dark"\s*\);/.test(
    main.replace(
      /if\s*\(\s*!storedTheme\s*&&\s*!document\.documentElement\.hasAttribute\(\s*"data-theme"\s*\)\s*\)\s*\{\s*document\.documentElement\.setAttribute\(\s*"data-theme",\s*"dark"\s*\);?\s*\}/,
      "",
    ),
  ),
);

// The fix: read the stored preference (both keys the shell boot honors).
check(
  "reads the stored stx-theme preference",
  main.includes('localStorage.getItem("stx-theme")'),
);
check(
  "reads the scitex-theme-preference fallback key",
  main.includes('localStorage.getItem("scitex-theme-preference")'),
);

// The fix: a pre-resolved theme (shell boot) is never overwritten.
check(
  "dark default only when no theme attribute was resolved",
  /!document\.documentElement\.hasAttribute\(\s*"data-theme"\s*\)/.test(main),
);

// The fix: blocked storage must not break the mount.
check(
  "storage reads guarded by try/catch",
  /try\s*\{\s*storedTheme\s*=[\s\S]*?localStorage\.getItem[\s\S]*?\}\s*catch/.test(
    main,
  ),
);

if (failures > 0) {
  console.error(`\n${failures} check(s) FAILED`);
  process.exit(1);
}
console.log("\nAll theme-preference checks passed.");
