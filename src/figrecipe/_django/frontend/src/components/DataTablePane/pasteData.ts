/** Parse what the user pastes from a spreadsheet into an import payload.
 *
 * The Data page empty state offers Paste beside Import: clipboard text from
 * Excel/Sheets arrives as TSV, from a text editor as CSV. This sniffs the
 * delimiter and validates the shape before anything is POSTed, so a stray
 * single cell cannot create a one-column table that reads as broken.
 *
 * Pure and dependency-free (no React, no DOM, no @scitex/ui), so it runs
 * under `node --experimental-strip-types` like the other decision modules
 * here.
 */

export interface PastedTable {
  /** The clipboard text, normalised to \n line endings for the importer. */
  content: string;
  /** Which delimiter the importer should split on. */
  format: "csv" | "tsv";
  rows: number;
  columns: number;
}

/** Parse pasted text, or null when it cannot be a table (empty, or a header
 *  with no data rows). A single data column IS a table — one series plots. */
export function parsePastedTable(text: string): PastedTable | null {
  const lines = text
    .replace(/\r\n?/g, "\n")
    .split("\n")
    .filter((line) => line.trim().length > 0);
  // Header plus at least one data row; anything less is a stray fragment.
  if (lines.length < 2) return null;
  const tsv = lines.some((line) => line.includes("\t"));
  const delimiter = tsv ? "\t" : ",";
  const widths = lines.map((line) => line.split(delimiter).length);
  const columns = Math.max(...widths);
  if (columns < 1) return null;
  return {
    content: lines.join("\n"),
    format: tsv ? "tsv" : "csv",
    rows: lines.length - 1,
    columns,
  };
}
