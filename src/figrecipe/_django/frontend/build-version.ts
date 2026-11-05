import { readFileSync } from "fs";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";

const __here = dirname(fileURLToPath(import.meta.url));

/**
 * Derive figrecipe's version from pyproject.toml (the package source of
 * truth) at BUILD time, baked into the bundle as __FIGRECIPE_VERSION__.
 * Reproducible (no timestamp), works on BOTH the standalone #root path and
 * the Hub #app-mount host path (the host doesn't stamp a version), and is
 * derived rather than hardcoded. A host that wants a different value can
 * still override via the FigrecipeEditor appVersion prop or #root
 * [data-version].
 */
function deriveFigrecipeVersion(): string {
  try {
    const pyproject = resolve(__here, "../../../../pyproject.toml");
    const text = readFileSync(pyproject, "utf8");
    const m = text.match(/^version\s*=\s*["']([^"']+)["']/m);
    if (m) return m[1];
  } catch {
    // fall through
  }
  return "0.0.0+local";
}

export const FIGRECIPE_VERSION = deriveFigrecipeVersion();
