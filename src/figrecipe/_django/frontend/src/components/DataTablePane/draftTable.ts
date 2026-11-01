/** Keep an unsaved worksheet local until the user chooses to create a table. */
import {
  serializeTableToCsv,
  tableFromDataset,
  type TableDataset,
} from "./dataTableEdit.ts";

/** Trim unused grid edges while preserving interior blanks, zero and text. */
export function draftCsv(data: TableDataset | null): string | null {
  if (!data) return null;
  const present = (value: unknown) =>
    value !== undefined && value !== null && String(value).trim() !== "";
  let lastRow = -1;
  let lastColumn = -1;
  data.rows.forEach((row, ri) =>
    data.columns.forEach((column, ci) => {
      if (present(row[column])) {
        lastRow = Math.max(lastRow, ri);
        lastColumn = Math.max(lastColumn, ci);
      }
    }),
  );
  if (lastRow < 0) return null;
  return serializeTableToCsv(
    tableFromDataset(
      {
        columns: data.columns.slice(0, lastColumn + 1),
        rows: data.rows.slice(0, lastRow + 1),
      },
      null,
    ),
  );
}

export type DraftImport = (content: string, format: string) => Promise<void>;
