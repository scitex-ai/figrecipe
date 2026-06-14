---
description: |
  [TOPIC] L-shaped scale bar for axis-off trace / EEG panels
  [DETAILS] ax.stx_scalebar() draws an L-shaped time/amplitude scale bar instead of x/y axes. Use after ax.axis("off") on raw time-series / iEEG plots.
tags: [figrecipe-plot, figrecipe-trace, figrecipe-eeg, figrecipe]
---


# L-shaped scale bar (`ax.stx_scalebar`)

Raw time-series / iEEG plots follow the EEG publication convention of *no*
x/y axes. The reader still needs to know the time scale and the amplitude
scale, so we draw an **L-shaped scale bar** instead: a horizontal arm
encodes time, a vertical arm encodes amplitude, the two arms share a
corner, and the labels sit padded clear of the arms so nothing overlaps.

The helper is shipped as `ax.stx_scalebar(...)` (also reachable on the
figrecipe-branded surface as `ax.fr_scalebar(...)` when the
`scitex_dev._branding` alias registry is installed). The figrecipe-level
shortcut `fr.scale_bar_l()` follows the same call shape.

## Signature

```python
ax.stx_scalebar(
    x_len,                     # horizontal arm length, data units
    y_len,                     # vertical arm length,   data units
    x_label="1 min",           # label below the horizontal arm
    y_label="a.u.",            # label left of the vertical arm
    loc="lower left",          # corner of the L's vertex
    color="black",
    lw=1.5,
    pad_frac=(0.04, 0.06),     # corner inset (axes-fraction)
    label_pad_frac=(0.015, 0.03),  # label offset off the arms
)
```

`x_len` and `y_len` are in data units, so call this **after** plotting
the trace data — the helper reads `ax.get_xlim() / ax.get_ylim()` to
position the bar.

Font sizes follow the active rcParams / SCITEX_STYLE (no hardcoded
`fontsize=`).

## Example: EEG-style raw trace

```python
import figrecipe as fr
import numpy as np

t = np.linspace(0, 60, 60_000)               # 60 s of trace
y = np.random.randn(t.size).cumsum() * 0.01  # placeholder

fig, ax = fr.subplots(figsize=(6, 1.5))
ax.plot(t, y, color="black", lw=0.5)
ax.axis("off")                               # no x/y axes
ax.stx_scalebar(
    x_len=10,           # 10 s
    y_len=0.5,          # 0.5 a.u.
    x_label="10 s",
    y_label="0.5 a.u.",
    loc="lower left",
)
fr.save(fig, "eeg_trace.png")
```

## When to use

- Raw / continuous trace panels (iEEG, LFP, MEG, ECoG snippets) where
  numeric tick labels would clutter the panel.
- Any axis-off plot where the *scale* matters more than absolute values.

## When NOT to use

- Scientific bar / line / scatter plots — those want full axes with
  labelled ticks (use `ax.set_xyt` instead).
- Heatmaps / imshow / colormap plots — use a colorbar, not a scale bar.

## See also

- `ax.set_xyt(x, y, title)` — the standard "set axis text" helper for
  non-axis-off plots. STX-FM010 flags `set_xlabel` / `set_ylabel` /
  `set_title` in favour of it.
- `ax.hide_spines(...)` — finer-grained spine removal when you only
  want to hide *some* axes (STX-FM011 flags the manual
  `ax.spines[...].set_visible(False)` form).
