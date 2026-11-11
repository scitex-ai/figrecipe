/** Both actual Vite builds must receive the Python package's version. */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { loadConfigFromFile } from "vite";

const frontend = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const pyproject = readFileSync(resolve(frontend, "../../../../pyproject.toml"), "utf8");
const project = pyproject.split(/^\[project\]\s*$/m)[1]?.split(/^\[/m)[0];
const version = project?.match(/^version\s*=\s*"([^"]+)"/m)?.[1];
assert.ok(version, "owning Python package must declare its version");
for (const filename of ["vite.config.ts", "vite.config.lib.ts"]) {
  const loaded = await loadConfigFromFile(
    { command: "build", mode: "production" }, resolve(frontend, filename), frontend,
  );
  assert.equal(loaded?.config.define?.__FIGRECIPE_VERSION__, JSON.stringify(version), filename);
}
console.log("2 actual Vite build version contracts passed");
