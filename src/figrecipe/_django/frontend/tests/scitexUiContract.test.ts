/** Node test for figrecipe's dependency contract with the real @scitex/ui owner.
 *
 * The frontend imports the owner's SOURCE by deep path
 * (`@scitex/ui/src/scitex_ui/static/scitex_ui/...`), resolved by vite's alias in
 * the bundle and by tsconfig `paths` in the type-checker, against the sibling
 * checkout the hub and CI materialize. The same owner release is also what the
 * Python extras install. Nothing checked that those declarations agreed, that
 * the checkout was new enough for the imported paths, that the lockfile agreed
 * with it, or that the imported symbols still existed — a stale lock/source
 * surfaced only as a broken production container (#329's class of outage).
 *
 * This test is CROSS-LANGUAGE: it fails when
 *   - any Python `scitex-ui` floor in pyproject.toml differs from the declared
 *     release (`scitexUi.version`) — a `file:` frontend dependency is not
 *     upgraded by the Python extras, so both sides must say the same thing,
 *   - the declared release's tag/commit are inconsistent with each other,
 *   - the lockfile records a different owner version than figrecipe declares,
 *   - the checked-out owner source is older than the declared release, or is not
 *     a @scitex/ui checkout at all (a dangling `file:` link),
 *   - an `@scitex/ui/...` specifier in `src/` resolves to nothing in the owner
 *     source, or uses a specifier form the build cannot resolve,
 *   - a named import is not exported by the owner module it comes from,
 *   - the type-checker's mapping and the bundler's alias disagree about where
 *     the owner root is.
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/scitexUiContract.test.ts
 */

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

let passed = 0;
function ok(name: string, fn: () => void) {
  fn();
  passed++;
  console.log("  ok - " + name);
}

const here = dirname(fileURLToPath(import.meta.url));
const FRONTEND = join(here, "..");
const REPO = join(FRONTEND, "..", "..", "..", "..");
const read = (rel: string) => readFileSync(join(FRONTEND, rel), "utf8");
const readRepo = (rel: string) => readFileSync(join(REPO, rel), "utf8");

const pkg = JSON.parse(read("package.json")) as {
  dependencies: Record<string, string>;
  scitexUi?: { version: string; tag: string; commit: string };
};
const lock = JSON.parse(read("package-lock.json")) as {
  lockfileVersion: number;
  packages: Record<string, { version?: string; link?: boolean; resolved?: string }>;
};
const tsconfig = JSON.parse(read("tsconfig.json")) as {
  compilerOptions: { paths?: Record<string, string[]> };
};

/** The hub/CI resolution contract: the owner repo is a SIBLING of figrecipe's
 *  checkout, and `@scitex/ui` resolves to its repo root. */
const SPECIFIER = "file:../../../../../scitex-ui";
const LOCK_KEY = SPECIFIER.replace(/^file:/, "");
const OWNER = resolve(FRONTEND, "node_modules/@scitex/ui");
const OWNER_PREFIX = "@scitex/ui/";

/** A git query against the owner checkout; null when it cannot answer (a
 *  shallow clone may not carry a tag object, and that is not a failure — the
 *  ancestry check covers the commit itself). */
function tryGit(args: string[]): string | null {
  try {
    return execFileSync("git", ["-C", OWNER, ...args], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
  } catch {
    return null;
  }
}

/** The shared alias helper both vite configs must use. */
function aliasContract(): { appUses: boolean; libUses: boolean; strips: boolean; root: boolean } {
  const app = read("vite.config.ts");
  const lib = read("vite.config.lib.ts");
  const helper = read("vite.scitexUiAlias.ts");
  return {
    appUses: /alias:\s*scitexUiAlias\(\)/.test(app),
    libUses: /alias:\s*scitexUiAlias\(\)/.test(lib),
    // The owner root is the repo root: the `/src/scitex_ui/static/scitex_ui`
    // suffix is stripped, so `@scitex/ui/src/...` is a real file path.
    strips: /staticDir\.replace\(\s*\/\\\/src\\\/scitex_ui\\\/static\\\/scitex_ui\$\/,\s*""?\s*,?\s*\)/.test(helper),
    root: /"@scitex\/ui":\s*staticDir\.replace/.test(helper),
  };
}

/** owner-relative path for a specifier ("@scitex/ui/a/b" -> "a/b"). */
function ownerRelative(specifier: string): string {
  return specifier.slice(OWNER_PREFIX.length).split("?")[0];
}

/** Bundler-style resolution against the owner SOURCE: an explicit file, a file
 *  with a TS/JS extension, or a directory with an index. */
function resolveOwnerModule(specifier: string): string | null {
  const base = join(OWNER, ownerRelative(specifier));
  const candidates = [
    base,
    `${base}.ts`,
    `${base}.tsx`,
    `${base}.js`,
    `${base}.mjs`,
    `${base}.css`,
    join(base, "index.ts"),
    join(base, "index.tsx"),
    join(base, "index.js"),
  ];
  for (const candidate of candidates) {
    if (existsSync(candidate) && statSync(candidate).isFile()) return candidate;
  }
  return null;
}

/** Every export a module offers, following re-exports (bounded, cycle-safe). */
function exportsOf(file: string, seen = new Set<string>()): Set<string> {
  const names = new Set<string>();
  if (seen.has(file) || !existsSync(file)) return names;
  seen.add(file);
  const source = readFileSync(file, "utf8");
  const directory = dirname(file);

  for (const match of source.matchAll(/export\s+(?:type\s+)?\{([^}]*)\}/g)) {
    for (const entry of match[1].split(",")) {
      const name = entry.trim().split(/\s+as\s+/).pop()?.trim();
      if (name) names.add(name);
    }
  }
  for (const match of source.matchAll(
    /export\s+(?:declare\s+)?(?:const|let|var|function|class|enum|interface|type|namespace|abstract\s+class)\s+([A-Za-z_$][\w$]*)/g,
  )) {
    names.add(match[1]);
  }
  if (/export\s+default\b/.test(source)) names.add("default");
  for (const match of source.matchAll(
    /export\s+\*\s+as\s+([A-Za-z_$][\w$]*)\s+from\s+["']([^"']+)["']/g,
  )) {
    names.add(match[1]);
  }
  for (const match of source.matchAll(/export\s+\*\s+from\s+["']([^"']+)["']/g)) {
    const target = resolveSpecifierFrom(directory, match[1]);
    if (target) for (const name of exportsOf(target, seen)) names.add(name);
  }
  for (const match of source.matchAll(
    /export\s+(?:type\s+)?\{(?:[^}]*)\}\s+from\s+["']([^"']+)["']/g,
  )) {
    // Named re-exports are already collected above; following the module keeps
    // `export { X } from "./y"` honest when X is itself re-exported there.
    const target = resolveSpecifierFrom(directory, match[1]);
    if (target) for (const name of exportsOf(target, seen)) names.add(name);
  }
  return names;
}

/** Resolve a relative/owner specifier that appears INSIDE the owner source. */
function resolveSpecifierFrom(directory: string, specifier: string): string | null {
  const bases = specifier.startsWith(OWNER_PREFIX)
    ? [join(OWNER, ownerRelative(specifier))]
    : [resolve(directory, specifier)];
  for (const base of bases) {
    for (const candidate of [
      base,
      `${base}.ts`,
      `${base}.tsx`,
      `${base}.js`,
      join(base, "index.ts"),
      join(base, "index.tsx"),
    ]) {
      if (existsSync(candidate) && statSync(candidate).isFile()) return candidate;
    }
  }
  return null;
}

/** Every .ts/.tsx file under src/, minus the tests. */
function sourceFiles(): string[] {
  const out: string[] = [];
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (/\.tsx?$/.test(entry.name)) out.push(full);
    }
  };
  walk(join(FRONTEND, "src"));
  return out;
}

interface ImportSite {
  file: string;
  specifier: string;
  names: string[];
  typeOnly: boolean;
  sideEffectOnly: boolean;
}

/** All `@scitex/ui` / bare `scitex-ui` imports in figrecipe's own sources. */
function importSites(): ImportSite[] {
  const sites: ImportSite[] = [];
  for (const file of sourceFiles()) {
    const source = readFileSync(file, "utf8");
    const pattern = /import\s+(type\s+)?([^;]*?)\s*from\s*["']([^"']+)["']|import\s*["']([^"']+)["']/g;
    for (const match of source.matchAll(pattern)) {
      const specifier = match[3] ?? match[4];
      if (!specifier.startsWith(OWNER_PREFIX) && !specifier.startsWith("scitex-ui")) {
        continue;
      }
      const clause = match[2] ?? "";
      const names: string[] = [];
      const braced = clause.match(/\{([^}]*)\}/);
      if (braced) {
        for (const entry of braced[1].split(",")) {
          const name = entry.trim().split(/\s+as\s+/)[0]?.trim();
          if (name) names.push(name);
        }
      }
      sites.push({
        file: file.slice(FRONTEND.length + 1),
        specifier,
        names,
        typeOnly: Boolean(match[1]),
        sideEffectOnly: !match[3] && Boolean(match[4]),
      });
    }
  }
  return sites;
}

const SITES = importSites();

/** Compare dotted versions as the owner releases them. */
function versionAtLeast(actual: string, required: string): boolean {
  const parse = (v: string) => v.split("-")[0].split(".").map((n) => Number(n) || 0);
  const [a, b] = [parse(actual), parse(required)];
  for (let i = 0; i < 3; i++) {
    if ((a[i] ?? 0) > (b[i] ?? 0)) return true;
    if ((a[i] ?? 0) < (b[i] ?? 0)) return false;
  }
  return true;
}

console.log("scitexUiContract:");

// ── the dependency declaration ────────────────────────────────────────────

ok("the dependency keeps the hub's sibling-checkout resolution contract", () => {
  // Arrange / Act / Assert
  assert.equal(pkg.dependencies["@scitex/ui"], SPECIFIER);
  const entry = lock.packages[LOCK_KEY];
  assert.ok(entry, `package-lock.json must record ${LOCK_KEY}`);
  assert.equal(lock.lockfileVersion, 3);
  assert.equal(lock.packages["node_modules/@scitex/ui"]?.link, true);
  assert.equal(lock.packages["node_modules/@scitex/ui"]?.resolved, LOCK_KEY);
});

ok("figrecipe declares which owner release it needs", () => {
  // Arrange / Act / Assert: a declared requirement is what makes a stale lock or
  // an old checkout detectable at all.
  assert.ok(pkg.scitexUi, "package.json must declare scitexUi.version");
  assert.match(pkg.scitexUi!.version, /^\d+\.\d+\.\d+$/);
});

ok("the lockfile records the declared owner version, not a stale one", () => {
  // Arrange
  const pinned = pkg.scitexUi!.version;
  // Act
  const locked = lock.packages[LOCK_KEY]?.version;
  // Assert
  assert.equal(
    locked,
    pinned,
    `package-lock.json records @scitex/ui ${locked}; the declared requirement is ${pinned} — re-run npm install against the owner checkout`,
  );
});

// ── the cross-language half: the Python extras must name the same release ──

ok("every Python scitex-ui declaration names the declared owner release", () => {
  // Arrange: a `file:` frontend dependency is NOT upgraded by the Python extras,
  // so a lagging floor means a `pip install figrecipe[app]` environment can
  // resolve an owner tree the frontend was not built against.
  const pyproject = readRepo("pyproject.toml");
  // Act
  const declared = [...pyproject.matchAll(/"scitex-ui([^"]*)"/g)].map((m) => m[1]);
  const expected = `>=${pkg.scitexUi!.version}`;
  const drifters = declared.filter((spec) => spec !== expected);
  // Assert
  assert.ok(
    declared.length >= 3,
    `expected the Python extras to declare scitex-ui (found ${declared.length})`,
  );
  assert.deepEqual(
    drifters,
    [],
    `pyproject.toml declares scitex-ui${drifters.join(", scitex-ui")}; every declaration must be "scitex-ui${expected}"`,
  );
});

ok("the Python floor, the frontend pin and the lock name one release", () => {
  // Arrange
  const pin = pkg.scitexUi!;
  const pyproject = readRepo("pyproject.toml");
  // Act: the three documents that can be resolved independently.
  const pythonFloors = [
    ...new Set([...pyproject.matchAll(/"scitex-ui(>=?[^"]*)"/g)].map((m) => m[1])),
  ];
  const lockVersion = lock.packages[LOCK_KEY]?.version;
  const ownerVersion = JSON.parse(
    readFileSync(join(OWNER, "package.json"), "utf8"),
  ).version as string;
  // Assert: one release, named the same way in all four places.
  assert.deepEqual(pythonFloors, [`>=${pin.version}`]);
  assert.equal(pin.version, lockVersion);
  assert.equal(pin.version, pin.tag.replace(/^v/, ""));
  assert.ok(
    versionAtLeast(ownerVersion, pin.version) && ownerVersion === pin.version,
    `the checked-out owner is ${ownerVersion}; the declared release is ${pin.version}`,
  );
});

ok("the declared release names one tag and one commit", () => {
  // Arrange
  const pin = pkg.scitexUi!;
  // Act / Assert
  assert.equal(pin.tag, `v${pin.version}`, "tag and version must describe one release");
  assert.match(pin.commit, /^[0-9a-f]{40}$/, "commit must be a full SHA");
  if (!existsSync(join(OWNER, ".git"))) return;
  // The checkout can be asked directly when its history carries the tag (a
  // shallow clone may not; the ancestry check below still covers the commit).
  const tagCommit = tryGit(["rev-parse", `${pin.tag}^{commit}`]);
  if (tagCommit === null) return;
  assert.equal(
    tagCommit,
    pin.commit,
    `${pin.tag} resolves to ${tagCommit}, not the declared ${pin.commit}`,
  );
});

// ── the owner source actually present ─────────────────────────────────────

ok("the owner checkout is present and is @scitex/ui", () => {
  // Arrange: a dangling `file:` link is the failure this catches (it makes
  // `npm ci` succeed while every import resolves to nothing).
  assert.ok(
    existsSync(join(OWNER, "package.json")),
    `no @scitex/ui source at ${OWNER} — link the owner checkout (scripts/maintenance/setup-worktree-frontend-deps.sh) and run npm install`,
  );
  // Act
  const owner = JSON.parse(readFileSync(join(OWNER, "package.json"), "utf8")) as {
    name: string;
    version: string;
  };
  // Assert
  assert.equal(owner.name, "@scitex/ui");
});

ok("the owner source is not older than the declared release", () => {
  // Arrange: an older checkout lacks imported paths (0.20.2 had no
  // _base/gettext.ts, no React data-table/selector-nav, no newer shell paths).
  const pinned = pkg.scitexUi!.version;
  // Act
  const owner = JSON.parse(readFileSync(join(OWNER, "package.json"), "utf8")) as {
    version: string;
  };
  // Assert
  assert.ok(
    versionAtLeast(owner.version, pinned),
    `@scitex/ui on disk is ${owner.version}, older than the declared ${pinned}`,
  );
});

ok("the checked-out owner really is the declared release (Git present)", () => {
  // Arrange: a `file:` checkout is a Git working copy, so when Git can answer,
  // the pin must be VERIFIABLE. A missing object or a HEAD that has nothing to
  // do with the pin used to be a silent skip — which is how a floating
  // `develop` checkout could pass while not matching the declared release.
  const pin = pkg.scitexUi!;
  const head = tryGit(["rev-parse", "HEAD"]);
  // No Git working copy (a tarball/wheel install): the version checks above are
  // the only facts available, and they already ran.
  if (head === null) return;
  // Act
  const pinnedPresent =
    tryGit(["cat-file", "-e", `${pin.commit}^{commit}`]) !== null;
  const descendsFromPin =
    tryGit(["merge-base", "--is-ancestor", pin.commit, "HEAD"]) !== null;
  // Assert: both facts, so neither a missing object nor a stranger HEAD passes.
  assert.ok(
    pinnedPresent,
    `owner checkout at ${head} does not contain the declared commit ${pin.commit} — fetch that release (a missing object must not pass silently)`,
  );
  assert.ok(
    descendsFromPin || head === pin.commit,
    `owner HEAD ${head} is neither the declared release ${pin.commit} nor descends from it`,
  );
});

// ── the imports resolve, and to the right thing ───────────────────────────

ok("every @scitex/ui import resolves in the owner source", () => {
  // Arrange
  const unresolved: string[] = [];
  // Act
  for (const site of SITES) {
    if (!site.specifier.startsWith(OWNER_PREFIX)) continue;
    if (!resolveOwnerModule(site.specifier)) {
      unresolved.push(`${site.file}: ${site.specifier}`);
    }
  }
  // Assert
  assert.deepEqual(unresolved, [], `unresolvable @scitex/ui imports:\n${unresolved.join("\n")}`);
});

ok("no import uses a specifier form the build cannot resolve", () => {
  // Arrange: the bare `scitex-ui/...` form resolved only through a manual
  // configure.py symlink (tsc-only, no bundler alias) — one form, everywhere.
  const legacy = SITES.filter((site) => !site.specifier.startsWith(OWNER_PREFIX));
  // Act / Assert
  assert.deepEqual(
    legacy.map((site) => `${site.file}: ${site.specifier}`),
    [],
    "use @scitex/ui/src/scitex_ui/static/scitex_ui/... so the bundler alias and tsconfig paths agree",
  );
});

ok("every named import is exported by the owner module", () => {
  // Arrange
  const missing: string[] = [];
  // Act
  for (const site of SITES) {
    if (!site.specifier.startsWith(OWNER_PREFIX)) continue;
    const module = resolveOwnerModule(site.specifier);
    if (!module) continue; // reported above
    if (!/\.(ts|tsx)$/.test(module)) continue; // CSS carries no symbols
    const exported = exportsOf(module);
    for (const name of site.names) {
      if (!exported.has(name)) missing.push(`${site.file}: ${name} from ${site.specifier}`);
    }
  }
  // Assert
  assert.deepEqual(missing, [], `symbols the owner source does not export:\n${missing.join("\n")}`);
});

ok("the imports cover the owner sub-systems the editor depends on", () => {
  // Arrange: a sanity floor, so a broken import scanner cannot make the suite
  // above vacuous.
  const STATIC_PREFIX = "src/scitex_ui/static/scitex_ui/";
  const prefixes = new Set(
    SITES.map((site) => ownerRelative(site.specifier).slice(STATIC_PREFIX.length).split("/")[0]),
  );
  // Act / Assert
  assert.ok(SITES.length >= 20, `expected the whole UI surface, scanned ${SITES.length} imports`);
  assert.ok(prefixes.has("ts"), "the ts/ surface must be covered");
  assert.ok(prefixes.has("react"), "the react/ surface must be covered");
  assert.ok(prefixes.has("css"), "the css/ surface must be covered");
});

// ── the two resolvers must agree ──────────────────────────────────────────

ok("tsconfig maps the owner the way the bundler alias does", () => {
  // Arrange: without this mapping the type-checker reports every deep import as
  // TS2307 while the bundle builds fine — the divergence that hid the contract.
  const paths = tsconfig.compilerOptions.paths ?? {};
  const contract = aliasContract();
  // Act / Assert
  assert.deepEqual(paths["@scitex/ui"], ["./node_modules/@scitex/ui"]);
  assert.deepEqual(paths["@scitex/ui/*"], ["./node_modules/@scitex/ui/*"]);
  assert.equal(contract.appUses, true, "the app config must use the shared alias helper");
  assert.equal(contract.libUses, true, "the library config must use it too — it had no alias at all");
  assert.equal(contract.root, true, "the alias must resolve @scitex/ui to the owner ROOT");
  assert.equal(contract.strips, true, "the owner root is the static dir's repo root");
});

ok("the owner root the alias computes is the linked package directory", () => {
  // Arrange: the alias strips `/src/scitex_ui/static/scitex_ui` from
  // SCITEX_UI_STATIC (the owner's static dir, as the setup script and CI set it).
  const staticDir = "…/scitex-ui/src/scitex_ui/static/scitex_ui";
  // Act
  const aliasRoot = staticDir.replace(/\/src\/scitex_ui\/static\/scitex_ui$/, "");
  // Assert
  assert.equal(aliasRoot, "…/scitex-ui");
  assert.equal(ownerRelative("@scitex/ui/src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts"),
    "src/scitex_ui/static/scitex_ui/ts/_base/gettext.ts");
});

console.log(
  "\nAll @scitex/ui contract checks passed (" + passed + " assertion-groups).",
);
