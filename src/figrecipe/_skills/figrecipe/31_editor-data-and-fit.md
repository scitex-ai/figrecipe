---
description: |
  [TOPIC] Editor data and view
  [DETAILS] Direct worksheet entry, provenance locks, fit geometry, export and table-close semantics.
tags: [figrecipe-editor-data-and-fit, figrecipe]
---

# Data entry, figure view and export

The editor shows the related Figures, Panels and Data navigation rows together.
On an empty Data page, enter values in the shared x/y worksheet by double-clicking
a cell, or paste spreadsheet cells. Choose **Create table** to persist the draft
through the normal import path. Merely opening or typing in the worksheet makes
no project writes; leaving before creation discards the unsaved draft.

CSV upload, clipboard paste, sample data, and project-file loading remain below
the worksheet. After creation, choose X/Y columns and **Plot** to draw the data.
Manual entries do not record clew provenance. Figure-recorded tables stay
read-only until **Edit table** explicitly takes ownership.

On Figures, **Fit** anchors the rendered figure image at the top-left of the current canvas,
with rulers either visible or hidden. It changes view positioning rather than
figure dimensions. **Export** opens the filename/PNG/SVG/PDF dialog; confirm the
download and inspect the exported artifact separately for scientific quality.

The Data dropdown's current Delete action closes its table tab and linked
placement. It does not delete the stored CSV; do not present it as durable data
delete functionality.

Source: `_django/frontend/src/components/DataTablePane` owns worksheet import
and lock handling; `components/Canvas/useZoomPan.ts` and `canvasPan.ts` own Fit;
`components/ExportDialog` owns downloads. Tests `draftTable.test.ts` and
`canvasPan.test.ts` cover CSV persistence and fit geometry. Qualify deployed UI
changes with actual cell entry, recipe reopen, Fit, and a real export download.
