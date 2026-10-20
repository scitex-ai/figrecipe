/** i18n catalog-coverage gate (card figrecipe-i18n-theme-audit-20261016,
 * string half).
 *
 * The JA catalog (locale/ja/LC_MESSAGES/djangojs.po) is maintained by hand
 * alongside feature work, so new user-visible strings silently fall back to
 * English until someone adds them. This gate fails when a gettext/ngettext
 * string in src has no catalog entry (msgid or msgid_plural), or when a
 * user-visible JSX literal bypasses gettext outside the documented
 * exceptions.
 *
 * Maintenance duty this gate enforces: a PR adding a user-visible string
 * extends djangojs.po in the same PR (empty msgstr = honest
 * pending-translation; never ship a translation you cannot verify — the
 * 2026-10-18 backfill added 50+ entries that way). Strings landing via
 * still-open PRs must extend the catalog before merge.
 *
 * Known exception: components/Toolbar/Toolbar.tsx is vestigial (never
 * mounted — InnerEditor renders its own header), so its hardcoded title is
 * not a live gap. If that file is ever mounted again, remove it from
 * UNMOUNTED and tag its strings.
 *
 * Source-conformance gate (Node, no framework).
 *
 *   node --experimental-strip-types \
 *     src/figrecipe/_django/frontend/tests/i18nCoverage.test.ts
 */

import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const FRONTEND = join(here, "..");
const SRC = join(FRONTEND, "src");

let failures = 0;
function check(name: string, cond: boolean) {
  if (cond) console.log(`  ok   ${name}`);
  else {
    failures++;
    console.error(`  FAIL ${name}`);
  }
}

function srcFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((e: string) => {
    const p = join(dir, e);
    if (statSync(p).isDirectory()) return srcFiles(p);
    return p.endsWith(".tsx") || p.endsWith(".ts") ? [p] : [];
  });
}

// gettext('…') / gettext("…") / ngettext('a','b') — first string may sit on
// the next line, so allow whitespace (never content) between ( and quote.
const STR = `(?:"((?:[^"\\\\]|\\\\.)*)"|'((?:[^'\\\\]|\\\\.)*)')`;
const CALL = new RegExp(
  `(?:^|[^\\w])ngettext\\(\\s*${STR}\\s*,\\s*${STR}|(?:^|[^\\w])(?<!n)gettext\\(\\s*${STR}`,
  "g",
);

const calls = new Map<string, string>();
for (const f of srcFiles(SRC)) {
  if (f.includes("/tests/")) continue;
  const text = readFileSync(f, "utf8");
  for (const m of text.matchAll(CALL)) {
    const rel = f.slice(SRC.length + 1);
    const groups = m.slice(1).filter((g) => g !== undefined);
    for (const g of groups) {
      if (!calls.has(g)) calls.set(g, rel);
    }
  }
}

// Catalog msgids (+ plurals), joining wrapped lines.
const po = readFileSync(
  join(
    FRONTEND,
    "..",
    "locale",
    "ja",
    "LC_MESSAGES",
    "djangojs.po",
  ),
  "utf8",
);
const msgids = new Set<string>();
const plurals = new Set<string>();
{
  let buf: string[] = [];
  let inId = false;
  const flush = () => {};
  for (const line of po.split("\n")) {
    let m = line.match(/^msgid "(.*)"$/);
    if (m) {
      buf = [m[1]];
      inId = true;
      continue;
    }
    m = line.match(/^msgid_plural "(.*)"$/);
    if (m) {
      plurals.add(m[1]);
      inId = false;
      continue;
    }
    m = line.match(/^"(.*)"$/);
    if (m && inId) {
      buf.push(m[1]);
      continue;
    }
    if (line.startsWith("msgstr")) {
      if (buf.length > 0) msgids.add(buf.join(""));
      buf = [];
      inId = false;
    }
  }
  void flush;
}

console.log("i18nCoverage:");
const missing = [...calls].filter(
  ([s]) => !msgids.has(s) && !plurals.has(s),
);
check(
  "every gettext string has a catalog entry",
  missing.length === 0,
);
for (const [s, f] of missing.slice(0, 20)) {
  console.error(`  missing ${JSON.stringify(s)} (${f})`);
}

// Untagged user-visible literals: JSX text children and display attributes
// on lines without gettext. Only .tsx files can carry JSX (the same scan on
// .ts files false-positives on type annotations like `=> Promise<void>`).
// Vestigial files are documented, not fixed.
const UNMOUNTED = new Set(["components/Toolbar/Toolbar.tsx"]);
const untagged: string[] = [];
for (const f of srcFiles(SRC)) {
  if (f.includes("/tests/") || !f.endsWith(".tsx")) continue;
  const rel = f.slice(SRC.length + 1);
  if (UNMOUNTED.has(rel)) continue;
  const lines = readFileSync(f, "utf8").split("\n");
  lines.forEach((line, i) => {
    const s = line.trim();
    if (
      line.includes("gettext") ||
      line.includes("interpolate") ||
      s.startsWith("//") ||
      s.startsWith("*") ||
      s.startsWith("{/*")
    )
      return;
    for (const m of line.matchAll(/>([^<>{}]{4,})</g)) {
      const t = m[1].trim();
      if (/^[A-Z].*[a-z]$/.test(t) && !/^[{}()\d\W]+$/.test(t)) {
        untagged.push(`${rel}:${i + 1}: ${t.slice(0, 60)}`);
      }
    }
    for (const m of line.matchAll(
      /(?:title|placeholder|aria-label)="([A-Z][^"]{3,})"/g,
    )) {
      untagged.push(`${rel}:${i + 1} [attr]: ${m[1].slice(0, 60)}`);
    }
  });
}
check("no untagged user-visible literals outside vestigial files", untagged.length === 0);
for (const u of untagged.slice(0, 20)) console.error(`  untagged ${u}`);

if (failures > 0) {
  console.error(`\n${failures} check(s) FAILED`);
  process.exit(1);
}
console.log("\nAll i18n-coverage checks passed.");
