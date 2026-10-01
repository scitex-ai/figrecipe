/** newId works without crypto.randomUUID (plain-http, non-secure context).
 *
 *   node --experimental-strip-types src/figrecipe/_django/frontend/tests/newId.test.ts
 */

import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";
import { newId } from "../src/utils/newId.ts";

const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

const insecure = { getRandomValues: (a: Uint8Array) => webcrypto.getRandomValues(a) } as unknown as Crypto;
const ids = new Set(Array.from({ length: 200 }, () => newId(insecure)));
assert.equal(ids.size, 200, "ids are unique without randomUUID");
for (const id of ids) assert.match(id, UUID_V4);

assert.equal(newId({ randomUUID: () => "native" } as unknown as Crypto), "native");
assert.match(newId(undefined as unknown as Crypto), UUID_V4);

console.log("newId: ok");
