/// <reference types="vite/client" />

/**
 * figrecipe's own version, derived from pyproject.toml at build time and
 * injected by vite.config.ts `define`. Referenced as the header version
 * badge's fallback so it works on the Hub #app-mount host path (where no
 * #root[data-version] is stamped). A host can still override via the
 * FigrecipeEditor `appVersion` prop.
 */
declare const __FIGRECIPE_VERSION__: string;
