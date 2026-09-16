/// <reference types="vite/client" />

/**
 * figrecipe's own version, derived from pyproject.toml at build time and
 * injected by vite.config.ts `define`. Referenced as the header version
 * badge's standalone fallback. Host builds may not define this constant, so
 * host mounts pass data-app-version through the FigrecipeEditor `appVersion`
 * prop instead.
 */
declare const __FIGRECIPE_VERSION__: string;
