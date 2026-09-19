import { readFileSync } from "fs";
import { dirname, resolve } from "path";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "url";
import { defineConfig } from "vite";
import { scitexUiAlias } from "./vite.scitexUiAlias";

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

const FIGRECIPE_VERSION = deriveFigrecipeVersion();

/** `@scitex/ui` -> the owner repo root, shared with vite.config.lib.ts
 *  (see vite.scitexUiAlias.ts for the contract and the discovery order). */
export default defineConfig({
  plugins: [react()],
  base: "/static/figrecipe/",
  resolve: {
    alias: scitexUiAlias(),
  },
  // figrecipe's own version, derived from pyproject.toml at build time.
  // Referenced from the frontend as __FIGRECIPE_VERSION__ (the header's
  // version-badge fallback, so it works on the Hub #app-mount path too, where
  // no #root[data-version] is stamped). Reproducible; a host can still
  // override via the FigrecipeEditor appVersion prop.
  define: {
    __FIGRECIPE_VERSION__: JSON.stringify(FIGRECIPE_VERSION),
  },
  build: {
    outDir: "../static/figrecipe",
    emptyOutDir: true,
    sourcemap: true,
    manifest: true,
    rollupOptions: {
      // mermaid and graphviz are optional lazy-loaded viewers — not bundled
      external: ["mermaid", "@hpcc-js/wasm-graphviz"],
      output: {
        entryFileNames: "assets/index.js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name][extname]",
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      // Proxy API calls to Django backend during development
      "/preview": "http://127.0.0.1:8050",
      "/update": "http://127.0.0.1:8050",
      "/hitmap": "http://127.0.0.1:8050",
      "/ping": "http://127.0.0.1:8050",
      "/style": "http://127.0.0.1:8050",
      "/overrides": "http://127.0.0.1:8050",
      "/theme": "http://127.0.0.1:8050",
      "/list_themes": "http://127.0.0.1:8050",
      "/switch_theme": "http://127.0.0.1:8050",
      "/save": "http://127.0.0.1:8050",
      "/restore": "http://127.0.0.1:8050",
      "/diff": "http://127.0.0.1:8050",
      "/get_labels": "http://127.0.0.1:8050",
      "/update_label": "http://127.0.0.1:8050",
      "/update_axis_type": "http://127.0.0.1:8050",
      "/get_axis_info": "http://127.0.0.1:8050",
      "/get_legend_info": "http://127.0.0.1:8050",
      "/update_legend_position": "http://127.0.0.1:8050",
      "/get_axes_positions": "http://127.0.0.1:8050",
      "/update_axes_position": "http://127.0.0.1:8050",
      "/calls": "http://127.0.0.1:8050",
      "/call": "http://127.0.0.1:8050",
      "/update_call": "http://127.0.0.1:8050",
      "/update_annotation_position": "http://127.0.0.1:8050",
      "/get_captions": "http://127.0.0.1:8050",
      "/update_caption": "http://127.0.0.1:8050",
      "/datatable": "http://127.0.0.1:8050",
      "/download": "http://127.0.0.1:8050",
      "/add_image_panel": "http://127.0.0.1:8050",
      "/load_recipe": "http://127.0.0.1:8050",
      "/api": "http://127.0.0.1:8050",
    },
  },
});
