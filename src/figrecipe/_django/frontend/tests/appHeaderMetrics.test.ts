/** Canonical SDK header metrics and absence of leaf overrides.
 *
 * The declared SDK 0.3.17 owner (08ff4236) defines a 40px row, 4px block
 * padding, a 14px title and a 12px version. Verify the installed owner's CSS;
 * FigRecipe must not fork those rules. SDK 0.3.23 retains the same type sizes.
 * The old rem assertions described the retired scitex-ui stylesheet rather
 * than the declared SDK. Header changes belong in the SDK and its contract.
 *
 * Run: node --experimental-strip-types tests/appHeaderMetrics.test.ts
 */

import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = join(here, "..", "src");
const layout = readFileSync(join(SRC, "styles/layout.css"), "utf8");

/** Resolve the installed SDK owner the same way npm lays it out. */
function sdkDir(): string {
  const direct = join(here, "..", "node_modules", "@scitex", "sdk");
  if (existsSync(join(direct, "package.json"))) return direct;
  throw new Error("SDK owner not installed under node_modules/@scitex/sdk");
}

const sdkCssPath = join(
  sdkDir(),
  "ui",
  "static",
  "scitex_sdk",
  "ui",
  "css",
  "app",
  "app-header.css",
);
const sdkHeader = readFileSync(sdkCssPath, "utf8");

let failures = 0;
function check(name: string, cond: boolean) {
  if (cond) console.log(`  ok   ${name}`);
  else {
    failures++;
    console.error(`  FAIL ${name}`);
  }
}

/** First top-level rule body for a selector (desktop base, not media). */
function rule(css: string, selector: string): string {
  const m = css.match(
    new RegExp(`${selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*{([^}]*)}`),
  );
  return m ? m[1] : "";
}

console.log("appHeaderMetrics (SSoT):");

/* ── SSoT delivery: the SDK provides the header row contract. ── */
const sdkRow = rule(sdkHeader, ".stx-app-header");
check("sdk row min-height is 40px", /min-height:\s*40px/.test(sdkRow));
check("sdk row padding-block is 4px", /padding-block:\s*4px/.test(sdkRow));
check(
  "sdk row inline padding is 12px based",
  /padding-inline:\s*calc\(12px/.test(sdkRow),
);
check(
  "sdk row has no fixed height (min-height discipline)",
  !/(?<![a-z-])height:\s*\d+px/.test(sdkRow),
);
const sdkActions = rule(sdkHeader, ".stx-app-header__actions");
check("sdk actions order is 2", /order:\s*2/.test(sdkActions));
const sdkTitle = rule(sdkHeader, ".stx-app-header__title");
check("sdk title scale is 14px", /font-size:\s*14px/.test(sdkTitle));
const sdkVersion = rule(sdkHeader, ".stx-app-header__version");
check(
  "sdk version scale is 12px",
  /font-size:\s*12px/.test(sdkVersion),
);

/* ── No leaf fork: the leaf redefines none of the header. ── */
for (const selector of [
  ".stx-app-header",
  ".stx-app-header__title",
  ".stx-app-header__version",
  ".stx-app-header__actions",
]) {
  const body = rule(layout, selector);
  check(
    `leaf has no ${selector} geometry override`,
    !/(?<![a-z-])(min-height|height|padding|margin|order)\s*:/.test(body),
  );
  check(
    `leaf has no ${selector} type override`,
    !/font-size\s*:/.test(body),
  );
}
/* Selector trigger: identical everywhere — no leaf override remains. */
const trigger = rule(
  layout,
  ".project-scope-selector .stx-app-project-selector__trigger",
);
check(
  "trigger carries no leaf height override",
  !/height:\s*\d+px/.test(trigger),
);
check(
  "trigger carries no leaf font-size override",
  !/font-size:/.test(trigger),
);

if (failures > 0) {
  console.error(`\n${failures} check(s) FAILED`);
  process.exit(1);
}
console.log("\nAll app-header metrics checks passed.");
