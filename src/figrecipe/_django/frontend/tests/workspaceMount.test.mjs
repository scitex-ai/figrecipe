/** Execute the public leaf bridge without rendering; host fetch must remain intact. */
import assert from "node:assert/strict";
import { build } from "esbuild";
import { fileURLToPath } from "node:url";
const result = await build({
  entryPoints: [fileURLToPath(new URL("../src/bridge/MountPoint.ts", import.meta.url))],
  bundle: true, write: false, format: "esm", platform: "node",
  define: { "import.meta.env.VITE_API_BASE": '""' },
  plugins: [{ name: "host-fixture", setup(build) {
    build.onResolve({ filter: /react\/app\/bridge$|FigrecipeEditor$|EventBus$|store\/useEditorStore$|hooks\/useUndoRedo$|\.\.\/index$/ }, args => ({ path: args.path, namespace: "fixture" }));
    build.onLoad({ filter: /.*/, namespace: "fixture" }, args => ({ contents:
      args.path.endsWith("/bridge") ? `export const mountReactApp=(container,element)=>globalThis.mounted=element.props; export const unmountReactApp=()=>{}; export const installFetchOverride=()=>globalThis.fetch=()=>{};` :
      args.path.endsWith("FigrecipeEditor") ? `export function FigrecipeEditor(){}` :
      args.path.endsWith("useEditorStore") ? `export const resetEditorWorkspace=()=>{}; export const useEditorStore={getState:()=>({switchFile(){}})};` :
      args.path.endsWith("useUndoRedo") ? `export const initUndoHistory=()=>{};` :
      args.path.endsWith("EventBus") ? `export const emitEvent=()=>{};` : `export const useEditorStore={getState:()=>({loadPreview(){},loadHitmap(){},loadDatatable(){}})};`, loader: "js" }));
  } }],
});
globalThis.window = { location: { search: "", pathname: "/workspace/" }, history: { replaceState() {} } };
globalThis.document = { cookie: "" };
const originalFetch = globalThis.fetch;
const { mountFigrecipeEditor } = await import(`data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString("base64")}`);
const container = mount => ({ getAttribute: name => name === "data-stx-mount" ? mount : null });
for (const mount of ["/custom/plot/", "/apps/figrecipe/figrecipe", ""]) {
  mountFigrecipeEditor({ container: container(mount), initialFile: "sample.yaml" });
  assert.equal(globalThis.mounted.apiBaseUrl, mount.replace(/\/+$/, ""));
  assert.equal(globalThis.mounted.recipe, "sample.yaml");
  assert.equal(globalThis.fetch, originalFetch, "leaf mount must preserve host fetch");
}
mountFigrecipeEditor({ container: container(null), apiBaseUrl: "" });
assert.equal(globalThis.mounted.apiBaseUrl, "");
for (const mount of [null, "https://other.invalid/app", "//other.invalid/app", "/app/../other", "/app?x=1"]) {
  assert.throws(() => mountFigrecipeEditor({ container: container(mount) }));
}
console.log("workspaceMount: declared root/custom/legacy mounts; host fetch intact; absent/invalid mounts rejected");
