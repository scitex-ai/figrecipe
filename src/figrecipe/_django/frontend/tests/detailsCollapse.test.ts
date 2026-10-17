/** Details-rightmost-collapsible gate (operator layout rule xch_20261017T000849Z).
 *
 * Details/inspector minutiae live in the rightmost column AND are
 * minimizable/collapsible. In figrecipe that is the Details pane
 * (PropertiesPane): last pane order, far-right group, header toggle button,
 * drag-to-collapse/expand, persisted state, minimized strip with vertical
 * title + expand control. On phones the same content is a first-class
 * Details tab (tabs are the phone idiom; collapse bars do not apply).
 *
 * Source-conformance gate (Node, no framework).
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/detailsCollapse.test.ts
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

const inner = read("InnerEditor.tsx");
const props = read("components/PropertiesPane/PropertiesPane.tsx");
const hook = read("hooks/usePanelResize.ts");
const panes = read("components/mobilePanes.ts");
const layout = read("styles/layout.css");
console.log("detailsCollapse:");

// Rightmost: Details group pushed far right, last pane order.
check(
  "details group pinned far right",
  /className="stx-layout-most-right"[\s\S]{0,300}?paneAttrs\("details"[\s\S]{0,60}?,\s*4\)/.test(
    inner,
  ),
);

// Collapse control: explicit toggle button with both directions labeled.
check(
  "PropertiesPane renders an explicit collapse/expand button",
  /onToggleCollapse/.test(props) &&
    /Expand details/.test(props) &&
    /Collapse details/.test(props),
);
check(
  "InnerEditor wires the toggle into the right panel",
  /onToggleCollapse=\{rightPanel\.toggleCollapse\}/.test(inner) &&
    /collapsed=\{detailsCollapsed\}/.test(inner),
);

// Collapse mechanics: drag both ways + persisted state.
check(
  "hook persists collapsed state under a collapseKey",
  /readStorage\(collapseKey/.test(hook) &&
    /writeStorage\(collapseKey/.test(hook),
);
check(
  "drag to min-width collapses, drag from collapsed expands",
  /Auto-collapse/.test(hook) && /auto-expand first/.test(hook),
);

// Minimized strip: vertical title + toggle stay visible when collapsed.
check(
  "minimized strip keeps title and toggle visible",
  /\.split-pane\.collapsed[\s\S]*?\.panel-toggle-btn/.test(layout) &&
    /\.split-pane\.collapsed \.panel-title\s*{[^}]*display:\s*flex/.test(layout),
);

// Phones: Details is a first-class tab (collapse bars N/A by design).
check(
  "phone panes include details",
  /EditorPane = "[^"]*details[^"]*"/.test(panes) ||
    /"figure" \| "data" \| "plot" \| "details"/.test(panes),
);

if (failures > 0) {
  console.error(`\n${failures} check(s) FAILED`);
  process.exit(1);
}
console.log("\nAll details-collapse checks passed.");
