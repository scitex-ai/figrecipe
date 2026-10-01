/** Built-in sample table for the Data page empty state.
 *
 * A first-run project has no tables, and an empty grid names nothing the
 * visitor can do. This sample is the third CTA beside Import and Paste: one
 * click POSTs it through the same `datatable/import` path a file takes, so
 * no backend change is needed and what lands is exactly what an import would
 * store.
 *
 * Pure and dependency-free (no React, no DOM, no @scitex/sdk/ui), so it runs
 * under `node --experimental-strip-types` like the other decision modules
 * here.
 */

export const SAMPLE_TABLE_FORMAT = "csv" as const;

/** Six rows, two series — enough to plot the moment it lands. */
export const SAMPLE_TABLE_CSV = [
  "x,y,group",
  "0,0.0,A",
  "1,1.5,A",
  "2,2.9,A",
  "0,0.5,B",
  "1,1.1,B",
  "2,2.2,B",
  "",
].join("\n");
