import { dirname, resolve } from "path";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "url";
import { defineConfig } from "vite";
import { FIGRECIPE_VERSION } from "./build-version";

const __here = dirname(fileURLToPath(import.meta.url));

// Resolve canonical SDK exports without source aliases.
export default defineConfig({
  plugins: [react()],
  base: "/static/figrecipe/",
  resolve: {
    dedupe: ["react", "react-dom"],
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
    // Cached entry scripts may still import a previous hashed chunk.
    // Retain those tracked assets when rebuilding the current entry points.
    emptyOutDir: false,
    sourcemap: true,
    manifest: true,
    cssCodeSplit: false,
    rollupOptions: {
      input: { index: resolve(__here, "index.html"), workspace: resolve(__here, "src/workspace.ts") },
      // mermaid and graphviz are optional lazy-loaded viewers — not bundled
      external: ["mermaid", "@hpcc-js/wasm-graphviz"],
      output: {
        // Keep production mappings without duplicating the matching source trees.
        sourcemapExcludeSources: true,
        entryFileNames: "assets/[name].js",
        // Stable entry URLs use app_static; imported chunks need their own
        // content URL so an unchanged parent never reuses stale chunk bytes.
        chunkFileNames: "assets/[name]-[hash].js",
        assetFileNames: (asset) => asset.name === "style.css" ? "assets/index.css" : "assets/[name][extname]",
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
