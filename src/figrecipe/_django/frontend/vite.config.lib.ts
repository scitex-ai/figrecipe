/** Vite config for library build (consumed by scitex-cloud). */

import react from "@vitejs/plugin-react";
import { resolve } from "path";
import { defineConfig } from "vite";
import { FIGRECIPE_VERSION } from "./build-version";

export default defineConfig({
  plugins: [react()],
  define: { __FIGRECIPE_VERSION__: JSON.stringify(FIGRECIPE_VERSION) },
  resolve: {
    dedupe: ["react", "react-dom"],
  },
  build: {
    lib: {
      entry: resolve(__dirname, "src/index.ts"),
      name: "FigrecipeEditor",
      fileName: "figrecipe-editor",
      formats: ["es"],
    },
    rollupOptions: {
      external: ["react", "react-dom", "react/jsx-runtime"],
      output: {
        globals: {
          react: "React",
          "react-dom": "ReactDOM",
        },
      },
    },
    sourcemap: true,
  },
});
