---
description: |
  [TOPIC] Tight layout & page filling (figure-making skill)
  [DETAILS] Principle-first, accumulated know-how for composing publication
  figures that use the page well — tile-over-grid to avoid empty panel cells,
  never stretch/upscale panels (re-plot each at true 1:1 and let compose place
  them), and the figrecipe layout-introspection APIs (empty_cells / layout_report)
  for agent-driven tight packing. Living doc — distil each new figure request into
  a reusable rule.
tags: [figrecipe-tight-layout-page-filling, figrecipe]
---

# Tight layout & page filling

Accumulated know-how for composing publication figures that use the page well.
Principle-first; figrecipe APIs noted where they help.

## Layout & page usage
- **Use the page tightly — no large empty panel cells.** A partially-filled grid
  wastes space and looks unfinished.
- **Prefer TILED layout over GRID.** figrecipe grid mode (`compose(layout=(nrows,
  ncols), sources={(r,c): ...})`) renders any *unsupplied* `(row, col)` as a blank
  subplot → empty cells. TILED mode (`compose(layout=[["A","B"],["C"]], sources=
  {"A": ...})`, a list-of-rows) is whitespace-free by construction: each row spans
  the full width edge-to-edge, and a row with fewer panels still fills the width.
  Re-express partial grids as tiled row-lists.
- **Never stretch/upscale panels to fill space.** Filling by scaling distorts or
  up-rezzes panels. If there is empty space, **redo from the panels** — re-plot
  each at a size that tiles cleanly at TRUE 1:1 scale; let compose place them
  without scaling.

## Deterministic foundation before fiddling
- **Detect, don't eyeball.** Encode the "no empty space" rule as code:
  - `fr.empty_cells(layout, sources)` → blank `(row, col)` list for GRID composes
    (exact, deterministic). *(figrecipe ≥ 0.29.6)*
  - `fr.layout_report(fig)` → structured layout: `mode`, `canvas_mm`,
    `panels[{x_mm, y_mm, w_mm, h_mm, aspect, ...}]`, `empty_regions[{bbox_mm,
    area_frac, ...}]`, `coverage_frac`. Deterministic geometry from panel boxes,
    no pixels. *(figrecipe ≥ 0.29.6)*
- **Agent image-recognition is a complement, not the basis.** A multimodal agent
  can view composed PNG/JPGs to spot blanks, but that is heuristic; the geometry
  report is the deterministic, codifiable source of truth.
- **Workflow:** run panels → `layout_report` (geometry + empties + target sizes)
  → re-author panels at target sizes → compose 1:1 (no scaling) → image-inspect to
  confirm.

## Before running (pre-flight)
- **Pre-flight, don't run-then-wait.** Before a heavy/long figure build, estimate
  cost (clew run history) and surface "this is a lot — are you sure? maybe do it
  this way" hints. Mirrors the pre-compile pre-check philosophy, on the compute
  side.

## Build mechanics (Spartan / scitex)
- Run builders with the HPC modules + the project venv that has the deps
  (`module load Python/3.10.4 ...; source .venv`). A bare venv python needs the
  Python module for `libpython`.
- Per figure: run the per-panel builders **first**, then the compose-only
  composer (`plot_figNN_composed.py`). Composers consume panel recipes (`.yaml`),
  not rasters.
- Keep scripts consistent with the **current scitex-io save/recipe format** (e.g.
  the "yaml filename as the first key" namespace). Old code against new io breaks;
  update the code, don't revert the intentional io update.

See also: `17_composition.md` (compose modes), `21_figure-prep-playbook.md`,
`24_l-shaped-scale-bar.md`.
