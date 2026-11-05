/** The first-run worksheet uses the same editable SDK grid as saved tables. */
import { useState } from "react";
import { DataTable } from "@scitex/sdk/ui/react/app/data-table/DataTable.tsx";
import { gettext } from "@scitex/sdk/ui/ts/_base/gettext.ts";
import type { TableDataset } from "./dataTableEdit";
import { draftCsv, type DraftImport } from "./draftTable";

const EMPTY_WORKSHEET: TableDataset = {
  columns: ["x", "y"],
  rows: Array.from({ length: 12 }, () => ({ x: "", y: "" })),
};

export function DraftDataGrid({ onImport }: { onImport: DraftImport }) {
  const [draft, setDraft] = useState<TableDataset | null>(null);
  const [saving, setSaving] = useState(false);
  const csv = draftCsv(draft);
  const save = async () => {
    if (!csv || saving) return;
    setSaving(true);
    try {
      await onImport(csv, "csv");
    } catch {
      // The import path reports the failure; retain this worksheet for retry.
    } finally {
      setSaving(false);
    }
  };
  return (
    <div className="datatable-draft" aria-label={gettext("New data worksheet")}>
      <DataTable
        data={EMPTY_WORKSHEET}
        onDataChange={setDraft}
        readOnly={saving}
        style={{ flex: 1, height: "auto", minHeight: 0 }}
      />
      <div className="datatable-draft-footer">
        <span>
          {gettext(
            "Double-click a cell to enter data, or paste spreadsheet cells. Create the table when ready.",
          )}
        </span>
        <button
          type="button"
          className="data-pane__btn"
          disabled={!csv || saving}
          onClick={() => void save()}
        >
          {saving ? gettext("Creating table…") : gettext("Create table")}
        </button>
      </div>
      <div className="datatable-empty-note">
        {gettext(
          "Manual input is for plotting in the UI; clew provenance is not recorded for these entries.",
        )}
      </div>
    </div>
  );
}
