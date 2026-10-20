/** Read a declared, instance-local API mount. Empty means standalone root. */
export function resolveApiMount(container: HTMLElement, declared?: string): string {
  const mount = declared ?? container.getAttribute("data-stx-mount");
  if (mount === null) throw new Error("FigRecipe requires a declared app mount");
  if (mount !== "" && (!mount.startsWith("/") || mount.startsWith("//"))) {
    throw new Error("FigRecipe's app mount must be a same-origin path");
  }
  if (/[?#\\]/.test(mount) || mount.split("/").includes("..")) {
    throw new Error("Invalid FigRecipe app mount");
  }
  return mount.replace(/\/+$/, "");
}
