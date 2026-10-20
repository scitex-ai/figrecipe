/** Ruler/guides/toggle gate (operator mandate xch_20261017T000323Z).
 *
 * (1) Ruler tick labels carry bare numbers; the unit appears once per axis
 *     (no more "0mm10mm" collisions); column labels mark only the guided
 *     0.5/1.5 columns instead of duplicating the mm scale (1.0/2.0 dropped).
 * (2) Dotted column guides at 0.5/1.5 cols render inside the canvas
 *     container (pan/zoom with the page, above the grid, below figures).
 * (3) Theme toggle reads instantly (fa-circle-half-stroke, never gear-like
 *     fa-sun) at all three toggle sites; toggle/button actives use the
 *     full-outline Snap-style state (no partial glows).
 *
 * Source-conformance gate (Node, no framework).
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/rulerGuidesToggle.test.ts
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

const rulers = read("components/Canvas/Rulers.tsx");
console.log("rulerGuidesToggle:");

// (1a) No tick carries its unit anymore (tooltips keep full text for i18n).
check(
  "no mm-unit tick text",
  !/\}mm<\/text>/.test(rulers) && !/>0mm<\/text>/.test(rulers),
);
check(
  "no inch-unit tick text",
  !/\}"<\/text>/.test(rulers) && !/>0"<\/text>/.test(rulers),
);
// (1b) Unit exactly once per axis: mm + in, horizontal + vertical.
check(
  "unit shown once per axis (2x mm, 2x in)",
  (rulers.match(/>mm<\/text>/g) || []).length === 2 &&
    (rulers.match(/>in<\/text>/g) || []).length === 2,
);
// (1c) Column labels only at the guided columns.
check(
  "column labels at 0.5/1.5 only (1.0/2.0 dropped)",
  /\["0\.5"\]/.test(rulers) &&
    /\["1\.5"\]/.test(rulers) &&
    !/\["1\.0"\]/.test(rulers) &&
    !/\["2\.0"\]/.test(rulers),
);

// (2) Dotted guides at 0.5/1.5 inside the canvas container.
const guides = read("components/Canvas/ColumnGuides.tsx");
check(
  "ColumnGuides marks 0.5/1.5 from the shared COLUMN_WIDTH_MM",
  /0\.5, 1\.5/.test(guides) && /COLUMN_WIDTH_MM/.test(guides),
);
const canvas = read("components/Canvas/Canvas.tsx");
check(
  "Canvas renders ColumnGuides right after the grid layer",
  /<CanvasGrid[^/]*\/>[\s\S]*?<ColumnGuides \/>/.test(canvas),
);
const canvasCss = read("styles/canvas.css");
check(
  "column-guide is dotted, non-interactive decoration",
  /\.column-guide\s*{[^}]*border-left:\s*2px dotted/.test(canvasCss) &&
    /\.column-guide\s*{[^}]*pointer-events:\s*none/.test(canvasCss),
);

// (3a) Instant-read theme glyph at every toggle site, no sun anywhere.
for (const site of [
  "components/CanvasPane/CanvasPane.tsx",
  "components/Ribbon/Ribbon.tsx",
  "components/Properties/Properties.tsx",
]) {
  const code = read(site);
  const short = site.split("/").pop();
  check(
    `${short}: no gear-like fa-sun`,
    !/fa-sun/.test(code),
  );
  check(
    `${short}: instant-read fa-circle-half-stroke`,
    /fa-circle-half-stroke/.test(code),
  );
}

// (3b) Underline-only actives, identical on every toggle control (operator:
// the shared 2px accent bar is the only indicator — no fills, no outlines).
for (const [file, cls] of [
  ["styles/layout.css", ".pane-header-btn--active"],
  ["styles/ribbon.css", ".ribbon-btn--active"],
] as const) {
  const css = read(file);
  const body = css.match(new RegExp(`${cls.replace(/\./g, "\\.")}\\s*{([^}]*)}`))?.[1] ?? "";
  check(
    `${cls} uses accent underline, no outline`,
    /border-bottom-color:\s*var\(--accent-primary\)/.test(body) &&
      !/outline:\s*2px solid/.test(body),
  );
  check(
    `${cls} carries no border-color accent box (underline is the indicator)`,
    !/border-color:\s*var\(--accent-primary\)/.test(body),
  );
}

if (failures > 0) {
  console.error(`\n${failures} check(s) FAILED`);
  process.exit(1);
}
console.log("\nAll ruler/guides/toggle checks passed.");
