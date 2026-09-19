/** Vite config for library build (consumed by scitex-cloud). */

import react from "@vitejs/plugin-react";
import { resolve } from "path";
import { defineConfig } from "vite";
import { scitexUiAlias } from "./vite.scitexUiAlias";

export default defineConfig({
  plugins: [react()],
  resolve: {
    // The same owner resolution the app build uses (vite.scitexUiAlias.ts).
    // Without it, `@scitex/ui/src/…/<directory>` imports are resolved through
    // the owner's `exports` map, which only accepts FILE targets — so directory
    // modules (react/app/data-table, react/app/selector-nav, ts/shell,
    // ts/app/panes, …) failed to resolve and the library build could not run.
    alias: scitexUiAlias(),
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
