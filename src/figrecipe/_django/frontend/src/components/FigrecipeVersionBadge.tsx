interface FigrecipeVersionBadgeProps {
  /** Explicit version supplied by a host mount. */
  appVersion?: string;
}

/**
 * Render FigRecipe's own version, independent of the host application's
 * version. Host metadata wins; standalone root/build metadata remain fallbacks.
 */
export function FigrecipeVersionBadge({
  appVersion,
}: FigrecipeVersionBadgeProps) {
  const resolvedVersion = (() => {
    if (appVersion) return appVersion;

    try {
      const stamped = document
        .getElementById("root")
        ?.getAttribute("data-version");
      if (stamped) return stamped;
    } catch {
      /* #root is absent in a host mount. */
    }

    try {
      return typeof __FIGRECIPE_VERSION__ !== "undefined"
        ? __FIGRECIPE_VERSION__
        : "";
    } catch {
      return "";
    }
  })();

  if (!resolvedVersion) return null;

  return <span className="stx-app-header__version">v{resolvedVersion}</span>;
}