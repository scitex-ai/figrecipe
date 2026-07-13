---
description: |
  [TOPIC] Figure Prep Playbook (ecosystem-wide)
  [DETAILS] Canonical playbook for preparing publication-quality figures across the SciTeX ecosystem — real-data-only rule, NaN handling, common-scale-across-panels, representative-example selection criteria, config-as-single-source-of-truth, the figrecipe-dogfood principle (use figrecipe in figrecipe's own examples), and the L-shaped scale-bar convention for signal-trace panels. Every paper / poster / report figure produced anywhere in the ecosystem should pass this checklist before it lands.
tags: [figrecipe-figure-prep-playbook, figrecipe]
---


# Figure Prep Playbook

Canonical figrecipe leaf for the figure-preparation checklist used
across the SciTeX ecosystem. Pairs with `05_styles.md` (presets),
`17_composition.md` (multi-panel layout), and the scitex-dev scientific
leaves `01_figures_01_standards.md` and
`01_figures_03_no-synthetic-data-policy.md`.

## When to use this leaf

Load when rendering a figure bound for a paper / poster / talk / grant,
building a representative example for a manuscript, writing a publication-
quality `examples/<NN>_*.py`, or reviewing such a script before merge.

Skip for throwaway exploratory plots (`ax.plot` and move on) and unit-test
fixtures that merely exercise the figrecipe API surface.

## The eight rules

### 1. Real data only

Paper / representative / publication figures MUST be backed by real
experimental or observational data. If the real data is absent at
render time, **fail loud** — raise, exit non-zero, refuse to write
the output file. Never silently substitute `np.random.*` or column
means.

Synthetic data is acceptable only in clearly-marked test fixtures
(`tests/fixtures/synthetic_*`, `examples/synthetic_demo_*.py`).

See `23_no-synthetic-data-policy.md` for the figrecipe-side rendering
guard, and the scitex-dev ecosystem-policy authority leaf
(`scitex-dev/_skills/scientific/01_figures_03_no-synthetic-data-policy.md`).

### 2. NaN handling, decided once

Every figure script MUST declare its NaN policy explicitly:

- **Convert sentinel values to `np.nan` at load time**, never at plot
  time. (Domain sentinels like `-32768`, `-999`, `9999` come from the
  storage layer and must be normalised on read; see
  `22_nan-sentinel-on-read.md`.)
- **Decide on render**: drop, interpolate, or visualise the gap.
  Whichever you pick, do it once and document the choice in the figure
  caption ("gaps shown as white" / "missing samples interpolated
  linearly" / "missing trials excluded from the mean").
- Never let `np.nan` reach a `vmin` / `vmax` calculation without
  `np.nanmin` / `np.nanmax`.
- Heatmaps: use a `cmap` with a distinct "bad" color
  (`cmap.set_bad("white")`) so missing pixels are visually distinct
  from any real value.

### 3. Common scale across compared panels

When two or more panels are intended to be compared visually
(treatment vs control, pre vs post, condition A vs B):

- **One shared `vmin` / `vmax`** across all compared panels —
  compute the global min/max before drawing.
- **Aligned axes** — same x and y ranges; remove redundant inner
  tick labels.
- **One shared colorbar** for the comparison group, not one per
  panel.
- **Same aspect ratio** for each panel of a comparison group.

If the panels are NOT meant to be compared (e.g., two unrelated
metrics side-by-side), say so in the caption and let each panel
have its own scale — but still align axes that share units.

See `scitex-dev/_skills/scientific/01_figures_01_standards.md` for the
universal-rule rationale.

### 4. Representative-example selection criteria

When picking a single trial / subject / sample to represent a result
("representative seizure", "representative cell"):

- **Document the criterion in code**, not in your head. Use a config
  key like `CONFIG.REPRESENTATIVE.SUBJECT_ID` and write the selection
  rule in a comment: `# closest-to-median effect size across cohort`.
- **The picked example must NOT be cherry-picked for visual appeal**
  — the criterion must be something you would defend to a reviewer
  (median, mode, nearest-to-mean, first-passing-quality-check).
- **Show the cohort distribution alongside the representative** when
  space allows (inset histogram / strip plot with the chosen sample
  highlighted). The representative is then a pointer into a real
  distribution, not a poster child.
- **Re-derive on every render** — if the cohort changes, the
  representative must change too, deterministically. Hard-coding
  `SUBJECT_ID = 7` because "subject 7 looks good" violates this.

### 5. Config = Single Source of Truth (SSoT)

Every figure-rendering decision that a reviewer might question MUST
come from a config file, not a hard-coded literal in the script.
That includes:

- Subject/trial IDs (representative-example selection).
- Channel / electrode / region selections.
- Color choices (use `CONFIG.COLORS.<KEY>` from `config/COLORS.yaml`).
- Time windows, frequency bands, thresholds.
- Style preset name (`SCITEX` / `SCITEX_DARK` / `MATPLOTLIB`).
- Output paths (use `CONFIG.PATH.<KEY>` from `config/PATH.yaml`).

Rationale: when a co-author asks "why this subject?" or "why this
band?", the answer is `config/PARAMS.yaml`. Diff-the-config to know
what changed between revisions. See
`scitex-dev/_skills/scientific/02_research-project_07_config-and-parameters.md`.

### 6. figrecipe dogfood

figrecipe's own `examples/`, `docs/`, and per-skill code blocks MUST
use the figrecipe API, never raw `plt.savefig(...)`. The package's
own examples are the most-read figrecipe reference; if they bypass
the library's affordances, every downstream user copies the bypass.

DO:

```python
import figrecipe as fr
fig, ax = fr.subplots(w_mm=85, h_mm=60, style="SCITEX")
ax.plot(x, y)
fr.save(fig, "output.png")
```

DON'T (even in examples):

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(3.3, 2.4))
ax.plot(x, y)
fig.savefig("output.png", dpi=300)
```

The same rule applies to any docstring example: if you would teach
a user to call `fr.subplots`, your own docstring must call
`fr.subplots`.

### 7. L-shaped scale bar on signal-trace panels

For **representative / paper figures showing signal traces** (EEG,
ECoG, LFP, spike, ECG, audio, kinematics), do **not** draw full
ticked x and y axes on the trace panel. Instead:

- Hide the surrounding axes (`ax.set_axis_off()` or remove spines /
  ticks).
- Draw a small **L-shaped scale bar** in the lower-left of the
  panel: one short horizontal bar (time scale, e.g. `100 ms`) and
  one short vertical bar (amplitude scale, e.g. `50 μV`), sharing a
  corner. The L-bar **is** the scale legend.
- Pick **round, reader-expectation magnitudes** — powers of 10 for
  time, biology-relevant rounds for amplitude (e.g. `50 μV` EEG,
  `100 μV` LFP, `1 mV` ECG). Drive the magnitudes from `CONFIG.*`
  (rule 5) so the bar label and the data agree when the data is
  rescaled.

Applies to: representative traces in paper / poster / talk figures.
Does **not** apply to stats plots (bar / line / scatter where ticked
axes carry quantitative claims), schematics, or multi-panel
comparison grids where readers must cross-read absolute values
between panels (use shared ticked axes per rule 3).

Don't keep full ticked axes AND add an L-bar — pick one. Don't
silently rescale the data and forget to update the bar label.

See `24_l-shaped-scale-bar.md` for the worked-example leaf with the
matplotlib pattern and a longer DO/DON'T list.

### 8. Six-stat annotation doctrine + heatmap colorbar

Any statistical annotation on a figure (a p-value / effect-size label
next to a comparison) MUST carry all six of **n, CI, method, p, effect,
statistic** — never a bare p-value or star. Render statistical symbols
(`p`, `t`, `F`, `r`, ...) in *italic*, and keep **N** (subjects) distinct
from **n** (windows/trials/samples) when both are relevant.

Separately: any 2D heatmap (`imshow`-style plot of a 2D array) MUST ship
a colorbar with tick labels, an axis label, and units on that label.

Both are operator-issued doctrine (2026-07-05) and both have a soft lint
check (`STX-FM017`, `STX-FM018`) in figrecipe's linter plugin. See
`27_six-stat-annotation-doctrine.md` for the full rule text, the italic
and N-vs-n conventions, and compliant/non-compliant examples.

## Pre-render checklist & anti-patterns

The merge-gate checklist (one line per rule above) and the catalogue of
anti-patterns that violate these rules live in the companion leaf
`25_figure-prep-checklist.md`. Load it alongside this playbook when
authoring or reviewing a publication-bound figure script.

## Cross-references

- `22_nan-sentinel-on-read.md` — concrete NaN-sentinel handling
  (e.g. `-32768` → `np.nan` on read) at the figure layer.
- `23_no-synthetic-data-policy.md` — figrecipe rendering-side guard
  for the no-synthetic-data policy.
- `24_l-shaped-scale-bar.md` — L-shaped scale-bar convention for
  signal-trace panels (rule 7 worked example).
- `25_figure-prep-checklist.md` — pre-render merge-gate checklist and
  anti-patterns companion to this playbook.
- `27_six-stat-annotation-doctrine.md` — six-stat annotation doctrine +
  heatmap colorbar requirement (rule 8 worked example).
- `05_styles.md` — `SCITEX` and dark-variant presets.
- `17_composition.md` — multi-panel mm-precision composition.
- `scitex-dev/_skills/scientific/01_figures_01_standards.md` — universal scientific-figure standards (color, layout, typography).
- `scitex-dev/_skills/scientific/01_figures_03_no-synthetic-data-policy.md` — canonical ecosystem-policy home for the real-data-only rule.
- `scitex-dev/_skills/scientific/02_research-project_07_config-and-parameters.md` — config-as-SSoT mechanics (`@stx.session`, `CONFIG.*`).
