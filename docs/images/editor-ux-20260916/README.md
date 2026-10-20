# Editor UX evidence — 2026-09-16

Screenshots captured from a real browser against a **standalone Django editor
server serving this branch's own `vite build`** (`figrecipe gui serve`-style
launcher: `python -m django runserver --settings=figrecipe._django.settings`
with `PYTHONPATH` pointed at the worktree, so nothing here comes from the main
checkout or a stale bundle).

| File | Shows |
| --- | --- |
| `start-empty-project-offer.png` | A brand-new, EMPTY project on load: the canvas offers "Open an example figure" and the disclosure "Show 18 examples". Nothing has been written into the project at this point (the directory listing was empty before and after the load). |
| `start-explicit-example-open.png` | The same project after that offer was CLICKED: `demo_first_figure.yaml` + `demo_first_figure_data/` now exist, because the user asked for them. Before this change the seeding happened on load instead. |
| `mobile-390-variant-chooser.png` | 390x844 phone: tapping the rail's **Bar** category opened the variant chooser — "Plot from data columns…", then Bar / Box / Violin with their real gallery thumbnails, plus "See all templates…". |
| `desktop-1440-variant-chooser.png` | 1440x900: the same chooser for **Special** (Pie, Spectrogram, Event, Graph), placed beside the pointed rail item and clamped inside the viewport. |
| `data-pane-1440-xy-highlight.png` | Data pane with the loaded table: the X/Y selection marks matching columns (98 marked cells) and the CRUD toolbar (add/delete row, add/rename/delete column) plus Undo are in the pane header. |
| `canvas-1440-grid-and-pan.png` | Canvas pane: the zoom-aware grid layer on the page. A synthesized 140x80 left-drag moved the view transform from `translate(0px, 0px)` to `translate(140px, 80px)` (the same run recorded `cursor: grab`). |

What these screenshots do **not** cover: the hover/focus reveal of the chooser
(headless Chromium reports `hover: none`, so only the tap gesture could be
exercised in this browser; the hover path is the same component and its reveal
decision is unit-tested in `frontend/tests/variantChooser.test.ts`), and the
hitmap selection itself (it needs a figure placed on the composition canvas and
a hitmap raster; its resolution and selection transitions are covered by
`frontend/tests/hitmapSelect.test.ts`).
| `mobile-390-crud-undo-redo.png` | 390px phone, Data tab: the six-button CRUD toolbar (add/delete row, add/rename/duplicate/delete column) and the assigned-column confirm: "Delete column plot_000_x? It is the X column — that assignment will be cleared." Undo/redo round-tripped the duplicate edit in the same run. |
