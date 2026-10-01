/** Execute the real API client against stubbed browser/fetch objects. */
import assert from "node:assert/strict";
import { build } from "esbuild";
import { fileURLToPath } from "node:url";

const result = await build({
  entryPoints: [fileURLToPath(new URL("../src/api/client.ts", import.meta.url))],
  bundle: true, write: false, format: "esm", platform: "node",
  define: { "import.meta.env.VITE_API_BASE": '""' },
});
globalThis.document = { cookie: "csrftoken=fixture-token" };
globalThis.window = { location: { search: "?project=alpha&recipe=figure.yaml" } };
const calls = [];
globalThis.fetch = async (url, options = {}) => {
  calls.push({ url, options });
  return { ok: true, json: async () => ({ success: true }), blob: async () => new Blob(["fixture"]) };
};
const { api, apiUrl, setApiBase, setWorkingDir } = await import(
  `data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString("base64")}`
);
for (const mount of ["", "/apps/figrecipe", "/legacy/figrecipe"]) {
  setApiBase(`${mount}/`);
  setWorkingDir("/fixture/alpha");
  const url = new URL(apiUrl("api/file-content/data.txt?raw=true"), "https://fixture.invalid");
  assert.equal(url.pathname, `${mount}/api/file-content/data.txt`);
  assert.equal(url.searchParams.get("project"), "alpha");
  assert.equal(url.searchParams.get("recipe"), "figure.yaml");
  assert.equal(url.searchParams.get("working_dir"), "/fixture/alpha");
  assert.equal(url.searchParams.get("raw"), "true");
  await api.get("ping");
  await api.post("api/compose", { filename: "composed" });
  await api.postBlob("api/compose/export/png", { figures: [] });
  for (const call of calls.splice(0)) {
    assert.ok(call.url.startsWith(`${mount}/`));
    if (call.options.method === "POST") {
      assert.equal(call.options.headers["X-CSRFToken"], "fixture-token");
    }
  }
}
console.log("pluginRouting: standalone, generic and legacy mounts preserve project, paths and CSRF");
