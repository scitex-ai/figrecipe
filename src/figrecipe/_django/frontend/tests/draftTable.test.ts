/** Data entered into the blank worksheet must survive CSV persistence. */
import assert from "node:assert/strict";
import { draftCsv } from "../src/components/DataTablePane/draftTable.ts";

assert.equal(draftCsv(null), null);
assert.equal(
  draftCsv({ columns: ["1", "2"], rows: [{ "1": "", "2": " " }] }),
  null,
);
assert.equal(
  draftCsv({
    columns: ["1", "2", "3"],
    rows: [
      { "1": 0, "2": 2, "3": "" },
      { "1": "", "2": "", "3": "" },
      { "1": 4, "2": 6, "3": "" },
      { "1": "", "2": "", "3": "" },
    ],
  }),
  "1,2\n0,2\n,\n4,6\n",
);
assert.equal(
  draftCsv({ columns: ["1", "2"], rows: [{ "1": 'say "hi", now', "2": "" }] }),
  '1\n"say ""hi"", now"\n',
);
console.log("4 draft worksheet persistence cases passed");
