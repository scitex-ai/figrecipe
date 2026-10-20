/** Host-consumer regression: the leaf version badge works where
 * __FIGRECIPE_VERSION__ is ABSENT.
 *
 * Defect (figrecipe-hub-mount-leaf-version-20260916): at /apps/figrecipe/ (both
 * 1440px and 390px) the Hub mount had one .stx-app-header but ZERO
 * .stx-app-header__version. Root cause: the Hub compiles figrecipe's bridge
 * frontend with ITS OWN Vite config, which does not bake in figrecipe's
 * version — so the build-time constant __FIGRECIPE_VERSION__ is UNDEFINED in
 * the Hub bundle. The old mount code did:
 *
 *     appVersion: typeof __FIGRECIPE_VERSION__ !== "undefined"
 *                ? __FIGRECIPE_VERSION__ : undefined
 *
 * i.e. it sourced appVersion ONLY from the build-time constant. In the Hub
 * bundle that constant is undefined, so appVersion was undefined, and
 * InnerEditor's fallback chain (prop -> #root[data-version] -> build const ->
 * "") resolved to "" -> the version element was never rendered.
 *
 * FIX: the leaf mount reads a stable `data-app-version` mount metadata
 * attribute (the host stamps the installed leaf version generically) and passes
 * it as appVersion, falling back to the build-time constant. resolveAppVersion
 * is the single source for that decision.
 *
 * This is the HOST-CONSUMER regression: it runs under `node
 * --experimental-strip-types`, where NO Vite `define` runs — so
 * __FIGRECIPE_VERSION__ is genuinely ABSENT in this process (typeof "undefined"),
 * which is precisely the Hub bundle condition. A test that passed because it
 * relied on the build constant would be testing the wrong (standalone) path;
 * the meaningful assertion is that the stamped value still wins when the
 * constant is missing.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/appVersionHostConsumer.test.ts
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { resolveAppVersion } from "../src/bridge/appVersion.ts";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = join(here, "..", "src");
const read = (rel: string) => readFileSync(join(SRC, rel), "utf8");

// 0. Precondition for the whole test: the build-time constant is ABSENT in
//    this Node process (no Vite `define` ran). If it were present, we'd be
//    testing the standalone path, not the host-consumer path — fail loudly.
assert.equal(
  typeof __FIGRECIPE_VERSION__,
  "undefined",
  "__FIGRECIPE_VERSION__ must be absent in this host-consumer regression " +
    "(no Vite define in node --experimental-strip-types). If this fails, the " +
    "test is running in a bundled/standalone context and no longer models the " +
    "Hub mount.",
);

// 1. THE regression: host stamps data-app-version="0.35.0", constant absent.
//    The badge must show the installed leaf version -> v0.35.0 (the element
//    renders "v" + resolvedVersion).
assert.equal(
  resolveAppVersion("0.35.0"),
  "0.35.0",
  "stamped host version must be returned even when __FIGRECIPE_VERSION__ is absent",
);

// 2. Whitespace-stamped value is trimmed, not dropped and not padded.
assert.equal(resolveAppVersion("  0.35.0  "), "0.35.0");

// 3. No stamp (null / undefined / blank) -> undefined, so the mount OMITS the
//    appVersion prop and InnerEditor runs its own chain. Must NOT return a
//    literal "undefined" or "" that InnerEditor would treat as a real version.
assert.equal(resolveAppVersion(null), undefined);
assert.equal(resolveAppVersion(undefined), undefined);
assert.equal(resolveAppVersion(""), undefined);
assert.equal(resolveAppVersion("   "), undefined);

// 4. The mount actually reads the attribute and threads it to the editor.
const mount = read("bridge/MountPoint.ts");
assert.match(
  mount,
  /getAttribute\(\s*"data-app-version"\s*\)/,
  "MountPoint must read data-app-version from the mount container",
);
assert.match(
  mount,
  /appVersion:\s*resolveAppVersion\(/,
  "MountPoint must pass resolveAppVersion(...) as the appVersion prop",
);
// The old defect: appVersion sourced ONLY from the build constant. Ensure that
// line is gone (no direct "appVersion: typeof __FIGRECIPE_VERSION__ ..." form).
assert.doesNotMatch(
  mount,
  /appVersion:\s*typeof __FIGRECIPE_VERSION__/,
  "MountPoint must not source appVersion solely from the build-time constant",
);

// 5. resolveAppVersion is a standalone module (importable without React/JSX),
//    so a future host can reuse it; it must not pull in the editor.
const appVersionSrc = read("bridge/appVersion.ts");
assert.doesNotMatch(
  appVersionSrc,
  /from\s*["']react["']|from\s*["'].*FigrecipeEditor|from\s*["'].*InnerEditor/,
  "appVersion.ts must stay dependency-free (no React/editor imports) so it is " +
    "importable under node --experimental-strip-types",
);

console.log("All host-consumer app-version checks passed (constant absent).");
