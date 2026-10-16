/** App-header metrics gate (operator mandate xch_20261016T232922Z).
 *
 * Header row too small: raise to Writer title-row scale with larger
 * app-name/version/selector text, unified per the SDK header mandate.
 * Values (all measured from Writer/SDK sources, cited per check):
 * - row min-height 44px (fits the 36px SDK trigger + padding-block),
 *   padding 4px 12px, min-height (never fixed height) per SDK mandate;
 * - app name 15px (writer toolbar logo), version 13px (writer file label);
 * - selector trigger: NO leaf override (SDK 36px / 0.85rem, verified in
 *   scitex-sdk ui/css/app/project-selector.css, identical everywhere);
 * - actions: order 2, no margin-left:auto (SDK mandate pair — the slot's
 *   margin-right:auto does the pushing).
 *
 * Source-conformance gate (Node, no framework), same pattern as
 * appHeaderPlacement.test.ts.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/appHeaderMetrics.test.ts
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = join(here, "..", "src");
const layout = readFileSync(join(SRC, "styles/layout.css"), "utf8");

let failures = 0;
function check(name: string, cond: boolean) {
  if (cond) console.log(`  ok   ${name}`);
  else {
    failures++;
    console.error(`  FAIL ${name}`);
  }
}

/** First top-level rule body for a selector (desktop base, not media). */
function rule(selector: string): string {
  const m = layout.match(
    new RegExp(`${selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*{([^}]*)}`),
  );
  return m ? m[1] : "";
}

const header = rule(".stx-app-header");
const title = rule(".stx-app-header__title");
const version = rule(".stx-app-header__version");
const actions = rule(".stx-app-header__actions");
const trigger = rule(
  ".project-scope-selector .stx-app-project-selector__trigger",
);

console.log("appHeaderMetrics:");

// Row geometry: Writer-scale breathing room, SDK min-height discipline.
check("row min-height is 44px", /min-height:\s*44px/.test(header));
check(
  "row has no fixed height (SDK mandate: min-height, not height)",
  !/(?<![a-z-])height:\s*\d+px/.test(header),
);
check("row padding is 4px 12px", /padding:\s*4px 12px/.test(header));

// Type scale: Writer toolbar metrics, not the old cramped ones.
check("app name is 15px (writer logo scale)", /font-size:\s*15px/.test(title));
check(
  "version is 13px (writer file-label scale)",
  /font-size:\s*13px/.test(version),
);

// Selector trigger: identical everywhere — no leaf override remains.
check(
  "trigger carries no leaf height override",
  !/height:\s*\d+px/.test(trigger),
);
check(
  "trigger carries no leaf font-size override",
  !/font-size:/.test(trigger),
);

// Actions: SDK pair rule — order 2, pushing left to the slot.
check("actions order is 2", /order:\s*2/.test(actions));
check(
  "actions have no margin-left:auto",
  !/margin-left:\s*auto/.test(actions),
);

if (failures > 0) {
  console.error(`\n${failures} check(s) FAILED`);
  process.exit(1);
}
console.log("\nAll app-header metrics checks passed.");
