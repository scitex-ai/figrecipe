/** Template ownership gate. React lifecycle/slot behavior: editorAppHeader.test.ts. */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const read = (path: string) => readFileSync(resolve(root, path), "utf8");
const partial = read("../templates/figrecipe/_app_header.html");
const workspace = read("../templates/figrecipe/workspace_partial.html");
assert.match(partial, /data-stx-app-header/);
assert.match(partial, /data-app-version="{{ app_version }}"/);
assert.doesNotMatch(partial, /<header\b/);
assert.match(workspace, /if not app_header_rendered/);
assert.doesNotMatch(read("src/InnerEditor.tsx"), /<header\b/);
assert.match(read("src/components/EditorAppHeader.tsx"), /@scitex\/sdk\/ui\/react\/app\/app-header/);
console.log("Canonical header ownership and host guard passed.");
