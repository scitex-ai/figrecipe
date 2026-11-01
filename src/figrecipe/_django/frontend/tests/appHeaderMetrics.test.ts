/** App-header metrics gate (SSoT edition).
 *
 * Supersedes the Writer-scale leaf gate from #460 (operator mandate
 * xch_20261016T232922Z): the header is OWNED BY THE SDK SSoT since the
 * [infra/fig-header] migration — scitex-ui all.css (app-header.css) renders
 * .stx-app-header, and the leaf must not redefine any of it (see the banner
 * at the top of src/styles/layout.css). Asserting leaf-side 44px/15px/13px
 * rules therefore collided with the shipped architecture and failed the
 * v0.44.0 release (run 40140835338, "Run the native frontend controls",
 * 5 checks FAILED) on code that was otherwise green.
 *
 * Current operator direction (apps-lead 2026-11-01, cross-app header
 * consistency 2026-10-23) keeps the SSoT: this gate now pins the SSoT
 * contract instead of a leaf fork —
 * - the SDK (pinned owner, resolved the same way the contract test
 *   resolves it) provides the row: min-height 40px, padding-block 4px
 *   with 12px inline base, actions slot order 2;
 * - the leaf carries NO header geometry/type override: no height,
 *   min-height, padding, font-size, or order on .stx-app-header or its
 *   __title/__version/__actions elements (selector-trigger pin already
 *   covered: SDK 36px / 0.85rem, identical everywhere).
 *
 * A hollow header (SDK drops the rule) or a reintroduced leaf fork both
 * fail loudly here. Writer-scale (44px/15px/13px) can only return via an
 * SDK change + pin bump — never a leaf override.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/appHeaderMetrics.test.ts
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
check("sdk title scale is 0.85rem", /font-size:\s*0\.85rem/.test(sdkTitle));
const sdkVersion = rule(sdkHeader, ".stx-app-header__version");
check(
  "sdk version scale is 0.78rem",
  /font-size:\s*0\.78rem/.test(sdkVersion),
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
