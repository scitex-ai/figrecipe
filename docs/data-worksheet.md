# Entering data in the editor

The Data page starts with an editable worksheet when no table is loaded.
Double-click a cell to enter a value, or paste cells copied from a spreadsheet.
The initial columns are `x` and `y`; the shared grid also supports renaming
headers and pasting a wider range.

Choose **Create table** to import the entries into the current editor. Opening
or typing in the worksheet does not write project data. Unused trailing rows
and columns are excluded; interior blank cells and numeric zero are preserved.
The draft stays available if creation fails. Leaving the workspace before
creating the table discards this unsaved draft.

Creation uses the same import path as CSV uploads. If no recipe is open, that
path creates a new blank figure before importing the table. Once created, the
normal table editing, column assignment, and Plot controls are available.

Manual entries do not record clew provenance. Existing figure-recorded tables
retain their read-only state until the user takes ownership. If loading stored
tables fails, the page shows the load error and Retry instead of a blank draft.

Import CSV, Paste data, Load sample data, and Load from project remain available
below the worksheet.

The trimming and CSV persistence contract is checked by
`src/figrecipe/_django/frontend/tests/draftTable.test.ts`:

```sh
node --experimental-strip-types src/figrecipe/_django/frontend/tests/draftTable.test.ts
```
