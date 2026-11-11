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

The Figures, Panels, and Data rows keep all placed items available when another
Figure is selected. Data tabs name their recorded source: inline arrays name the
YAML recipe, linked arrays name the CSV/NPY source, and edited tables name the
project CSV. Related tabs share their Figure's color. Selecting a Data chunk
also selects its panel and restores that table's API recipe/revision. Creating
or switching Figures keeps their cached editor records separate; an empty
Figure shows the draft worksheet instead of inheriting another panel's grid.

The row's × and right-click menu remove items from this composition; they do
not delete recipe or source files. Shift+F10 opens the same menu. Figure removal
removes its panel placements in one Undo step. Data removal never removes a
panel, and recorded data stays locked until explicitly adopted. Canvas Undo
preserves newer table revisions and newly locked data.

Export downloads only the selected Figure's panels. Its suggested filename is
`<project>-FigureN-<UTC timestamp>.<format>`. PNG/PDF exports contain raster
previews; SVG currently wraps that raster image. Fit maximizes the Figure at
the canvas's top-left inset, including panels with negative coordinates.

Source/relationship, navigation, and export checks:

```sh
PYTHONPATH=src .venv/bin/python -m pytest tests/figrecipe/_django/handlers/test_data_chunks.py tests/figrecipe/_django/handlers/test_compose_export.py tests/figrecipe/_django/handlers/test_recipe_cache_identity.py
cd src/figrecipe/_django/frontend
node --experimental-strip-types tests/exportTarget.test.ts
npx vitest run --config vitest.workflow.config.mts
```

Assigned columns show separate localized **X axis**/**Y axis** badges beside
their unchanged names. Column and cell colors still mark the same assignments;
header accessible labels include both the name and role. Sorted column names
keep the normal readable foreground in light and dark themes; the plot-role
badges retain their separate colors. Clearing an assignment
removes its badge and restores the prior accessible label. Sorting, resizing,
selection and editing remain owned by the shared SDK table.

Regression checks include `dataTableDom.test.ts`, `dataTableAxisBadges.spec.ts`
and the local-only `axisBadges.fixture.tsx` with `tests/integration/figrecipe/_django/frontend/axis_badges.py`.
From `src/figrecipe/_django/frontend/` after normal npm installation (and Python
dev dependencies for Playwright), build the fixture into an owned output directory:

```sh
./node_modules/.bin/esbuild tests/axisBadges.fixture.tsx --bundle --format=iife --outfile=/tmp/figrecipe-axis-proof/axis-fixture.js
python ../../../../tests/integration/figrecipe/_django/frontend/axis_badges.py --bundle-root /tmp/figrecipe-axis-proof --chromium /path/to/installed/chromium
```

The harness mounts the actual SDK React table with synthetic fixture rows,
blocks every network request, and checks badges, localization, sorting, resizing,
selection, editing and cleanup. It does not open or modify an application project.
