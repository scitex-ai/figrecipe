/** Execute the real client with Django's rendered token and an HttpOnly cookie. */
import assert from "node:assert/strict";
import { build } from "esbuild";
import { CookieJar, JSDOM } from "jsdom";
import { fileURLToPath } from "node:url";

const bundle = await build({
  entryPoints: [fileURLToPath(new URL("../src/api/client.ts", import.meta.url))],
  bundle: true, write: false, format: "esm", platform: "node",
  define: { "import.meta.env.VITE_API_BASE": '""' },
});
const jar = new CookieJar();
jar.setCookieSync("csrftoken=private-cookie; HttpOnly; Path=/", "https://fixture.invalid");
const dom = new JSDOM('<input type="hidden" name="csrfmiddlewaretoken" value="rendered-token">', {
  url: "https://fixture.invalid", cookieJar: jar,
});
globalThis.document = dom.window.document;
globalThis.window = dom.window;
const calls = [];
globalThis.fetch = async (url, options) => {
  calls.push({ url, options });
  return { ok: true, json: async () => ({}), blob: async () => new Blob() };
};
const { api, csrfToken } = await import(
  `data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].text).toString("base64")}`
);
assert.equal(document.cookie, "", "HttpOnly cookie must remain hidden from JavaScript");
assert.equal(csrfToken(), "rendered-token");
await api.post("api/chat/sessions/", { title: "Owned fixture" });
await api.postBlob("download/png", {});
assert.ok(calls.length === 2 && calls.every(call => call.options.headers["X-CSRFToken"] === "rendered-token"));

// A visible, stale cookie must not override Django's current rendered token.
document.cookie = "csrftoken=older-cookie; Path=/";
assert.equal(csrfToken(), "rendered-token");
document.querySelector('input[name="csrfmiddlewaretoken"]').remove();
assert.equal(csrfToken(), "", "HttpOnly cookie cannot be replaced by JavaScript");
dom.window.close();

const standalone = new JSDOM("", { url: "https://standalone.invalid" });
globalThis.document = standalone.window.document;
globalThis.window = standalone.window;
document.cookie = "csrftoken=cookie%2Btoken; Path=/";
assert.equal(csrfToken(), "cookie+token", "Standalone readable cookie fallback is preserved");
document.cookie = "csrftoken=; Max-Age=0; Path=/";
assert.equal(csrfToken(), "");
standalone.window.close();
console.log("csrfHttpOnly: rendered token, hidden cookie, mutation headers and standalone fallback passed");
