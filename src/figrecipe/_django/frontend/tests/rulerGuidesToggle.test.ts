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

// (4) Rulers-grid docking contract (evidence 2026-10-19/10-22, live 1920px:
// the right ruler read ~700px off the page edge when the canvas cell pooled
// spare pane pixels). The grid must shrink-wrap the fixed page so all four
// rulers park OUTSIDE it: both axes exactly `60px auto 60px` (1fr forbidden),
// rulers 60px on their minor axis, canvas cell start-aligned on both axes.
const rulersGrid = canvasCss.match(/\.vis-rulers-area\s*{([^}]*)}/)?.[1] ?? "";
check(
  "vis-rulers-area columns are 60px auto 60px (canvas cell shrink-wraps page)",
  /grid-template-columns:\s*60px\s+auto\s+60px/.test(rulersGrid),
);
check(
  "vis-rulers-area rows are 60px auto 60px",
  /grid-template-rows:\s*60px\s+auto\s+60px/.test(rulersGrid),
);
check(
  "no 1fr track in vis-rulers-area (spare pane pixels must not pool at the page edge)",
  !/1fr/.test(rulersGrid),
);
check(
  "horizontal rulers are 60px tall",
  /\.ruler-horizontal\s*{[^}]*height:\s*60px/.test(canvasCss),
);
check(
  "vertical rulers are 60px wide",
  /\.ruler-vertical\s*{[^}]*width:\s*60px/.test(canvasCss),
);
{
  // NOTE: [^}]* cannot span the multi-line comment inside the grid block —
  // match across the whole stylesheet instead, scoped by the selector.
  const gridBlock = canvasCss
    .slice(canvasCss.indexOf(".vis-rulers-area"), canvasCss.indexOf(".ruler-corner"));
  check(
    "rulers grid shrink-wraps the page, never stretches to the pane",
    /width:\s*max-content/.test(gridBlock) &&
      /max-width:\s*max-content/.test(gridBlock) &&
      !/flex:\s*1;/.test(gridBlock),
  );
}
check(
  "canvas cell is start-aligned on both axes (hugs top-left, pan math unaffected)",
  /\.vis-canvas-container\s*{[^}]*justify-self:\s*start/.test(canvasCss) &&
    /\.vis-canvas-container\s*{[^}]*align-self:\s*start/.test(canvasCss),
);

if (failures > 0) {
  console.error(`\n${failures} check(s) FAILED`);
  process.exit(1);
}

// (6) Empty-state copy never contradicts itself. The example door is gone
// (operator batch apps-figrecipe-ui-feedback-20261023 item 2), so no
// empty surface may point at it: Properties, the tree and the empty Panel
// all name the same quiet "Go to Data" way in.
{
  const props = read("components/Properties/Properties.tsx");
  check(
    "properties names one next step, never the removed example door",
    !props.includes("Nothing open yet? Pick a figure in Objects above") &&
      !props.includes("open an example on the canvas to begin.") &&
      props.includes('gettext("Go to Data")'),
  );
  const tree = read("components/ObjectTree/ObjectTree.tsx");
  check(
    "tree keeps only the quiet Go to Data way in",
    (tree.match(/Open an example figure/g) || []).length === 0 &&
      tree.includes('gettext("Go to Data")'),
  );
  const start = read("components/Gallery/GalleryStart.tsx");
  check(
    "empty Panel carries no example block",
    !start.includes("Start from an example") &&
      !start.includes("Open an example figure") &&
      !start.includes("Show %s example") &&
      (start.match(/gallery-start-demo|gallery-start-expand|gallery-start-grid|gallery-start-item/g) || []).length === 0 &&
      start.includes('gettext("Go to Data")'),
  );
}

// (5) One actions row on the empty canvas: the single Go-to-Data CTA,
// centered under the head — never two sibling buttons loose in the pane,
// and never the removed example doors.
{
  const start = readFileSync(
    join(here, "..", "src", "components", "Gallery", "GalleryStart.tsx"),
    "utf8",
  );
  const rowAt = start.indexOf("gallery-start-actions");
  const single =
    rowAt !== -1 &&
    (() => {
      const rowBlock = start.slice(rowAt, rowAt + 2200);
      const primaryAt = rowBlock.indexOf("gallery-start-primary");
      return (
        primaryAt !== -1 &&
        rowBlock.indexOf("gallery-start-demo") === -1 &&
        rowBlock.indexOf("gallery-start-expand") === -1 &&
        rowBlock.includes('gettext("Go to Data")')
      );
    })();
  check("empty canvas offers one actions row, Go to Data only", single);
}

console.log("\nAll ruler/guides/toggle checks passed.");
