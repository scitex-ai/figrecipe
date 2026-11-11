/** Real production builds must preserve chunks imported by cached entry scripts. */
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";

const frontend = dirname(dirname(fileURLToPath(import.meta.url)));
const sourceAssets = join(frontend, "../static/figrecipe/assets");
const temporary = mkdtempSync(join(tmpdir(), "figrecipe-chunk-retention-"));
const output = join(temporary, "output");
const assets = join(output, "assets");
mkdirSync(assets, {recursive: true});
const previous = new Map<string, Buffer>();
for (const name of readdirSync(sourceAssets).filter((name) => /^mobile-[\w-]+\.js(?:\.map)?$/.test(name))) {
  previous.set(name, readFileSync(join(sourceAssets, name)));
}
// An owned prior-build module remains distinct even after future chunk hashes change.
previous.set("previous-00000000.js", Buffer.from("export const previousBuild = true;\n"));
for (const [name, bytes] of previous) writeFileSync(join(assets, name), bytes);
try {
  const build = spawnSync(process.execPath, [join(frontend, "node_modules/vite/bin/vite.js"), "build", "--outDir", output], {
    cwd: frontend, encoding: "utf8", timeout: 60000,
  });
  assert.equal(build.status, 0, build.stdout + build.stderr);
  const manifest = JSON.parse(readFileSync(join(output, ".vite/manifest.json"), "utf8"));
  const emitted = new Set<string>();
  for (const entry of Object.values(manifest) as {file: string; css?: string[]}[]) {
    emitted.add(entry.file);
    emitted.add(entry.file + ".map");
    assert.ok(existsSync(join(output, entry.file)), `New build entry missing: ${entry.file}`);
    for (const css of entry.css ?? []) assert.ok(existsSync(join(output, css)));
  }
  const hash = (bytes: Buffer) => createHash("sha256").update(bytes).digest("hex");
  for (const [name, bytes] of previous) {
    // Current files may be rebuilt; their maps legitimately depend on output location.
    if (emitted.has("assets/" + name)) continue;
    assert.ok(existsSync(join(assets, name)), `Cached import was removed: ${name}`);
    assert.equal(hash(readFileSync(join(assets, name))), hash(bytes), `Cached import changed: ${name}`);
  }
  console.log("Previous cached imports retained; current production manifest files exist.");
} finally {
  rmSync(temporary, {recursive: true, force: true});
}
