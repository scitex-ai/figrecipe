---
description: |
  [TOPIC] Figure Prep Playbook (ecosystem-wide)
  [DETAILS] Canonical playbook for preparing publication-quality figures across the SciTeX ecosystem — real-data-only rule, NaN handling, common-scale-across-panels, representative-example selection criteria, config-as-single-source-of-truth, and the figrecipe-dogfood principle (use figrecipe in figrecipe's own examples). Every paper / poster / report figure produced anywhere in the ecosystem should pass this checklist before it lands.
tags: [figrecipe-figure-prep-playbook, figrecipe]
---


# Figure Prep Playbook

Canonical figrecipe leaf for the figure-preparation checklist used
across the SciTeX ecosystem. Loaded by any agent or human prepping a
publication-bound figure. Pairs with `05_styles.md` (visual presets),
`17_composition.md` (multi-panel layout), and the scitex-dev
scientific leaves `01_figures_01_standards.md` (universal rules) and
`01_figures_03_no-synthetic-data-policy.md` (ecosystem policy).

## When to use this leaf

Load this skill when you are about to:

- Render a figure that will end up in a paper / poster / talk / grant.
- Build a representative example for a manuscript figure.
- Write `examples/<NN>_*.py` that figrecipe (or any ecosystem package)
  ships as a publication-quality demonstration.
- Review an existing figure script before merging it into a publication
  pipeline.

Do **not** load this skill for:

- Quick exploratory plots during analysis (where the figure is
  throwaway — just `ax.plot` and move on).
- Unit-test fixtures that exercise the figrecipe API surface.

## The six rules

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

## Pre-render checklist

Before a figure script is allowed into a publication pipeline:

- [ ] Backed by real data; FileNotFoundError raises on missing input.
- [ ] NaN sentinel conversion happens at load, not plot.
- [ ] Compared panels share `vmin`/`vmax`, axes, and colorbar.
- [ ] Representative example is config-driven and documented.
- [ ] No `np.random.*` / `random.*` import in the script.
- [ ] All tunable params come from `CONFIG.*`, not literals.
- [ ] Style preset applied via `fr.load_style(...)` or
      `figrecipe.subplots(style=...)` — no manual `rcParams` overrides
      that bypass figrecipe.
- [ ] Output saved via `fr.save(fig, ...)` (not `fig.savefig`).
- [ ] Caption / docstring explicitly names the data source and the
      NaN-handling choice.

## Anti-patterns

- A `make_representative_figure()` helper that silently picks
  `subject_ids[0]` "for the example" — encodes cherry-pick into the
  pipeline.
- A heatmap comparison where one panel uses `vmax=data1.max()` and
  the other `vmax=data2.max()` — defeats the comparison even if
  every other rule is followed.
- A figure script that imports `matplotlib.pyplot` directly and calls
  `plt.savefig`, even inside a project that has figrecipe installed.
- "I'll fix the NaN sentinel handling in the figure" — no, you fix it
  in the loader. The figure layer assumes clean `np.nan`.

## Cross-references

- `22_nan-sentinel-on-read.md` — concrete NaN-sentinel handling
  (e.g. `-32768` → `np.nan` on read) at the figure layer.
- `23_no-synthetic-data-policy.md` — figrecipe rendering-side guard
  for the no-synthetic-data policy.
- `05_styles.md` — `SCITEX` and dark-variant presets.
- `17_composition.md` — multi-panel mm-precision composition.
- `scitex-dev/_skills/scientific/01_figures_01_standards.md` —
  universal scientific-figure standards (color, layout, typography).
- `scitex-dev/_skills/scientific/01_figures_03_no-synthetic-data-policy.md`
  — canonical ecosystem-policy home for the real-data-only rule.
- `scitex-dev/_skills/scientific/02_research-project_07_config-and-parameters.md`
  — config-as-SSoT mechanics (`@stx.session`, `CONFIG.*`).
