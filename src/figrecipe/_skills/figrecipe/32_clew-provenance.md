---
description: |
  [TOPIC] Clew provenance of saved figures
  [DETAILS] What figrecipe records with scitex-clew during an active session
  (recipe, data CSVs, image as outputs; recipes and their data files as
  inputs) and when a saved figure carries a per-output derived_from
  declaration for clew's level-2 minimal slice: only a figure rebuilt by
  fr.reproduce(recipe) and left unchanged. Never guessed.
tags: [figrecipe-clew-provenance, figrecipe-provenance, figrecipe, scitex-clew]
---

# Clew provenance of saved figures

With scitex-clew installed and a session active (`@stx.session`),
figrecipe records, best-effort and without any call from you:

| Event | Recorded as |
|---|---|
| `fr.save(fig, "f.png")` / `stx.io.save(fig, "f.png")` | outputs: `f.png`, `f.yaml`, `f_data/*.csv` |
| `fr.reproduce("f.yaml")`, `fr.load_recipe`, compose sources | inputs: the recipe, each data file it references, an applied `f.overrides.json` |

## `derived_from` (level-2 minimal slice)

`clew.slice(target, level=2)` keeps, for each output, only the inputs the
writer DECLARED it was computed from. figrecipe declares a figure's inputs
only when it knows them exactly:

```python
fig, ax = fr.reproduce("panel.yaml")       # rebuilt from recipe + its CSVs
stx.io.save(fig, "final.png")              # image, recipe, data CSVs all
                                           # declared derived_from =
                                           # [panel.yaml, panel_data/*.csv]
```

A run that also loaded an unrelated file keeps it at level 1 and drops it
at level 2.

Not declared (clew falls back to every input of the run):

* a figure built from in-memory arrays (`fr.subplots(); ax.plot(arr)`):
  figrecipe cannot tell which file `arr` came from;
* a reproduced figure that was changed afterwards -- any new plot call,
  decoration, label, title or style edit may carry in-memory data
  (`ax.set_title(f"n={len(df)}")`). Saving, re-saving, and the geometry a
  save writes back (size, crop, layout) do not count as changes;
* a recipe reproduced from a ZIP or directory bundle (it is rebuilt from
  a temporary extracted copy).

Drawing through raw matplotlib (`fig.fig.axes[0].plot(...)`) bypasses the
recorder, and therefore both the recipe and this check -- do not do it on
a figure you save (the figrecipe linter flags it).

To declare explicitly, pass `derived_from=[...]` to `stx.io.save` (paths or
objects returned by `stx.io.load`); clew unions it with figrecipe's
declaration for the same bytes.
