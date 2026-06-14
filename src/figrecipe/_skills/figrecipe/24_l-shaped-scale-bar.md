---
description: |
  [TOPIC] L-shaped scale bar for signal-trace figures
  [DETAILS] Convention for representative / paper figures showing signal traces (EEG, ECoG, LFP, spike, ECG, audio, kinematic): draw a small L-shaped scale legend in the lower-left of the panel (one horizontal bar = time scale, one vertical bar = amplitude scale) and HIDE the surrounding axes. The L-bar IS the scale legend; full ticked axes on a representative trace are redundant, visually noisy, and waste panel area. Applies to publication / paper / poster figures of signal traces. Does NOT apply to stats plots (bar / line / scatter with quantitative axes), schematics, or comparison grids where axes carry meaning.
tags: [figrecipe-l-shaped-scale-bar, figrecipe]
---


# L-shaped scale bar for signal traces

A standard neuroscience convention for representative trace figures:
instead of drawing ticked x and y axes, draw two short bars joined at
a corner (the "L") — one horizontal (time) and one vertical
(amplitude) — and hide the surrounding axes. The L-bar **is** the
scale legend.

Pairs with `21_figure-prep-playbook.md` (rule 7: signal-trace scale
bars) as the worked-example leaf.

## When to use

Use an L-shaped scale bar when the figure is:

- A **representative** trace (single trial, single channel, single
  cell) in a paper / poster / talk.
- A **signal trace** with a continuous time axis: EEG, ECoG, LFP,
  spike voltage, ECG, audio waveform, kinematics, optical recording.
- A figure where the **shape of the trace** is what the reader is
  supposed to evaluate — not its absolute coordinates.

Do **not** use an L-bar when the figure is:

- A **stats plot** — bar / line / scatter / box where each axis tick
  is a quantitative claim. Keep ticked axes.
- A **schematic** or **cartoon** with no real scale.
- A **multi-panel comparison grid** where readers must cross-read
  values between panels. Use shared ticked axes (see playbook rule 3,
  common scale across compared panels).
- A trace whose **absolute time** matters (e.g. event-aligned plots
  where t=0 must be labelled). Keep the x-axis; drop only the y-axis
  to a vertical scale bar if appropriate.

## The rule

For a representative signal-trace panel:

1. Draw the trace at the data's native units.
2. Hide the surrounding axes (`ax.set_axis_off()` or
   `for s in ax.spines.values(): s.set_visible(False)`; remove
   ticks).
3. Add two short bars joined at the **lower-left** corner of the
   panel:
   - Horizontal bar: time scale (e.g. `100 ms`, `1 s`).
   - Vertical bar: amplitude scale (e.g. `50 μV`, `100 pA`).
4. Label each bar with its magnitude **and unit**, placed adjacent
   to the bar (time label below, amplitude label to the left).
5. Pick **round, reader-expectation magnitudes** — powers of 10 for
   time (`10 ms`, `100 ms`, `1 s`), and biology-relevant rounds for
   amplitude (`50 μV` for EEG, `100 μV` for LFP, `1 mV` for ECG,
   `100 pA` for patch-clamp current).

## Minimal matplotlib pattern

Pseudocode showing the *shape* of the call sequence — adapt to your
own data and figure-size conventions. (A first-class
`fr.scale_bar_l(...)` helper would belong in figrecipe; until it
ships, inline this pattern in your figure script and keep the
magnitudes in `CONFIG.*`.)

```python
import figrecipe as fr

fig, ax = fr.subplots(w_mm=85, h_mm=30, style="SCITEX")
ax.plot(t, v, color="k", lw=0.6)

# Magnitudes from config (playbook rule 5)
t_bar_s   = CONFIG.SCALE_BAR.TIME_S       # e.g. 0.1   (100 ms)
v_bar_uV  = CONFIG.SCALE_BAR.AMP_UV       # e.g. 50

# Anchor the L-corner in the lower-left of the data window
x0 = t.min()
y0 = v.min()

# Horizontal bar = time
ax.plot([x0, x0 + t_bar_s], [y0, y0], color="k", lw=1.5,
        solid_capstyle="butt")
# Vertical bar = amplitude
ax.plot([x0, x0], [y0, y0 + v_bar_uV], color="k", lw=1.5,
        solid_capstyle="butt")

# Labels
ax.text(x0 + t_bar_s / 2, y0, f"{int(t_bar_s * 1000)} ms",
        ha="center", va="top")
ax.text(x0, y0 + v_bar_uV / 2, f"{v_bar_uV} μV",
        ha="right", va="center", rotation=90)

# Hide the axis frame — the L-bar IS the scale legend
ax.set_axis_off()

fr.save(fig, "fig_representative_trace.png")
```

The two `ax.plot` calls share the corner `(x0, y0)`, producing the L.
`solid_capstyle="butt"` keeps the corner crisp (no rounded overshoot
that breaks the right angle).

## DO

- **Match magnitudes to typical reader expectations** — powers of 10
  for time, round biology-relevant numbers for amplitude. A `73 ms`
  scale bar is a smell; pick `100 ms`.
- **Place lower-left** as default. Other corners are acceptable if
  the trace itself occupies the lower-left region, but the team /
  paper should pick one and stay consistent across panels.
- **Keep the bars the same color as the trace** (or a deliberate
  contrast color from `config/COLORS.yaml`). Black-on-white at
  `lw=1.5` reads at print size.
- **Drive magnitudes from config** — see playbook rule 5
  (config-as-SSoT). When the data is rescaled (e.g. mV → μV during a
  cleanup pass), the bar magnitude in the config is the single
  source of truth; the label updates automatically from
  `CONFIG.SCALE_BAR.AMP_UV`.
- **Mention the convention in the caption** once per figure: "Scale
  bars: 100 ms, 50 μV." Readers should not have to count pixels.

## DON'T

- **Don't keep full ticked axes AND add an L-bar.** Pick one. Both
  is redundant, visually noisy, and signals to a reviewer that the
  figure was not curated.
- **Don't silently rescale the data and forget to update the bar
  label.** A `100 μV` bar drawn at the new `mV` scale is now wrong
  by a factor of 1000. The bar label and the data must agree by
  construction — drive both from the same `CONFIG.SCALE_BAR.*`
  values.
- **Don't use odd magnitudes** (`73 ms`, `42 μV`). Pick the nearest
  power-of-10 / round number that still leaves the bar visually
  distinguishable from the trace.
- **Don't apply L-bars to stats plots.** A bar chart with hidden
  axes and an L-bar is unreadable. The L-bar is for *traces*.
- **Don't reach for the L-bar before deciding the panel is
  representative.** If the figure is a comparison grid where the
  reader must read absolute values across panels, keep shared
  ticked axes (playbook rule 3).

## Pre-render check

- [ ] Panel is a representative signal trace (not stats, not
      schematic, not a comparison grid).
- [ ] Surrounding axes are hidden (`ax.set_axis_off()` or
      spines/ticks off).
- [ ] Horizontal and vertical scale bars share a corner (lower-left
      by default).
- [ ] Magnitudes are round (powers of 10 for time, biology-relevant
      rounds for amplitude) and come from `CONFIG.SCALE_BAR.*`.
- [ ] Labels include units and are placed adjacent to each bar.
- [ ] Caption mentions the scale-bar magnitudes.
- [ ] If the data was rescaled, the scale-bar magnitudes were
      updated (verified by re-running with the new config).

## Future work

A first-class `fr.scale_bar_l(ax, t=0.1, amp=50, t_unit="ms",
amp_unit="μV", corner="lower-left")` helper would belong in
figrecipe so that the pattern above collapses to a single call and
the magnitudes / units stay in one place. Until then, the inline
pattern above is the convention; keep the magnitudes in
`CONFIG.SCALE_BAR.*` so the per-script copy is just a thin wrapper
around config values.

## Cross-references

- `21_figure-prep-playbook.md` — rule 7 (signal-trace scale bars)
  points here; rule 5 (config-as-SSoT) covers the
  `CONFIG.SCALE_BAR.*` pattern.
- `05_styles.md` — `SCITEX` preset sets the line weights / fonts
  the L-bar pattern assumes.
- `17_composition.md` — when a multi-panel figure mixes a
  representative-trace panel (L-bar) and a stats panel (ticked
  axes), they coexist; do not force a single axis style across
  panels.
- `scitex-dev/_skills/scientific/01_figures_01_standards.md` —
  universal scientific-figure standards (typography, sizing) that
  the L-bar labels follow.
