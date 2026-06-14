---
description: |
  [TOPIC] NaN-sentinel conversion at the figure layer
  [DETAILS] Many scientific storage layers use a sentinel integer value (e.g. `-32768`, `-999`, `9999`) to mark missing data because the on-disk type is integer and NaN is not representable. At the figure layer, on read, convert these sentinels to `np.nan` BEFORE any min/max/plot operation. Do not "fix" the storage layer — the sentinel is often by design. This leaf gives the conversion idiom plus a concrete domain example (neurovista ecog: `-32768`).
tags: [figrecipe-nan-sentinel-on-read, figrecipe]
---


# NaN sentinels: convert on read at the figure layer

## The pattern

Many scientific datasets store missing samples as a **sentinel integer
value** rather than NaN, because the on-disk dtype is integer (`int16`,
`int32`) and NaN is not representable in integer types. Common
sentinels:

| Value | Common usage |
|---|---|
| `-32768` (= `int16` min) | iEEG/ECoG voltage gaps, raw ADC dropouts |
| `-999` / `-9999` | Sensor dropout, "no value" flag |
| `9999` | Legacy meteorological / oceanographic missing |
| `255` (`uint8` max) | Classified-image background / "outside ROI" |
| `0` (in mask-context only) | Binary mask "absent" |

These values are **valid in the storage layer**. They become invalid
the moment they enter a computation that does not understand them
(a `min`/`max`, a mean, a colormap normalisation, a `ylim`). The
figure layer is the boundary where sentinel must become `np.nan`.

## The rule

**On read, at the figure layer, convert sentinel → `np.nan` before
any plotting or scale computation.** Do not fix it in the storage
layer; the sentinel is usually by design (compactness, integer
arithmetic, downstream-DB contract).

```python
import numpy as np

SENTINEL = -32768  # value contractually used by the upstream store

raw = load_from_store(...)         # int16 array; may contain SENTINEL
data = raw.astype(np.float32)      # promote so NaN is representable
data[raw == SENTINEL] = np.nan     # mark gaps

# Now safe to plot:
ax.imshow(data, vmin=np.nanmin(data), vmax=np.nanmax(data))
```

## Concrete example: neurovista ECoG (`-32768`)

In the neurovista ECoG capsule the raw voltage store uses **`-32768`
as an intentional sentinel** for data gaps. This is a deliberate
choice in the DB layer's design (the on-disk dtype is `int16` and
`-32768` is its natural minimum, leaving the rest of the range for
signal). It is *not* a bug, *not* a quantisation artefact, and *not*
a placeholder waiting for "real" data.

Figure scripts that load this store must convert on read:

```python
NV_ECOG_GAP_SENTINEL = -32768

def load_ecog_for_plotting(channel_id):
    raw = nv_store.load_voltage(channel_id)        # int16
    arr = raw.astype(np.float32)
    arr[raw == NV_ECOG_GAP_SENTINEL] = np.nan
    return arr
```

> This is a domain example, not a general rule. Other domains use
> other sentinels (`-999`, `9999`, etc.) and YOUR project should
> document its own sentinel set. The general rule — *convert at the
> figure layer, do not touch the storage layer* — is what
> generalises.

## DO

- **Convert on read**, immediately after `load_*`. Treat the
  conversion as part of the load API:
  `load_ecog_for_plotting(...)` returns float-with-NaN.
- **Promote the dtype** to a float type (`float32` / `float64`)
  before assigning `np.nan` — integer arrays cannot hold NaN.
- **Use `np.nan*` reductions** (`nanmin`, `nanmax`, `nanmean`)
  whenever a NaN may be present. Pair with `cmap.set_bad("white")`
  for heatmaps so missing pixels are visually distinct.
- **Document the sentinel** in the loader's docstring and the figure
  caption. ("Voltage gaps are stored as -32768 in the source; shown
  as white in this heatmap.")
- **Centralise the conversion** in one helper per data source
  (`load_ecog_for_plotting`, `load_weather_for_plotting`); do not
  scatter `arr[arr == -32768] = np.nan` across N figure scripts.

## DON'T

- **Don't "fix" the storage layer** — the sentinel is by design. A PR
  that rewrites the upstream store to use NaN will break every other
  consumer (integer-typed DBs, fixed-width binary protocols, the
  downstream-DB schema). Convert at YOUR boundary instead.
- **Don't pass raw sentinel values to `vmin`/`vmax`**:
  `vmin=data.min()` on int16 returns `-32768` and crushes the
  meaningful range to a single pixel. Use `np.nanmin(data)` after
  conversion, OR `np.where(data != SENTINEL, data, np.nan).min()`
  before promotion.
- **Don't silently drop NaN rows** at plot time. Decide explicitly
  (drop, interpolate, or display as a gap) and write the choice into
  the figure caption (see `21_figure-prep-playbook.md` rule 2).
- **Don't hard-code the sentinel as a magic number** in every script
  — define it as a named constant in the loader module
  (`NV_ECOG_GAP_SENTINEL = -32768`) and import it.

## Pre-render check

- [ ] Sentinel converted to `np.nan` immediately after load.
- [ ] All reductions in the figure code use `np.nan*` variants.
- [ ] Heatmaps use `cmap.set_bad("<color>")` so missing pixels are
      distinguishable.
- [ ] Caption / docstring names the sentinel and its rendering
      choice.

## Cross-references

- `21_figure-prep-playbook.md` — figure-prep playbook (rule 2 on NaN
  handling).
- `23_no-synthetic-data-policy.md` — never fill NaN with synthetic
  values in publication figures.
- `scitex-dev/_skills/scientific/01_figures_01_standards.md` — color
  scale and comparison rules (which break loudly if NaN leaks
  through).
