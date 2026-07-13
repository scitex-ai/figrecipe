---
description: |
  [TOPIC] Figure Prep — pre-render checklist & anti-patterns
  [DETAILS] Actionable companion to the Figure Prep Playbook (21): the gate checklist a figure script must pass before entering a publication pipeline, plus the catalogue of anti-patterns that violate the seven rules. Load alongside 21_figure-prep-playbook.md when authoring or reviewing a publication-bound figure script.
tags: [figrecipe-figure-prep-checklist, figrecipe]
---


# Figure Prep — Pre-render Checklist & Anti-patterns

Actionable companion to `21_figure-prep-playbook.md` (the seven rules).
Use this leaf as the merge-gate when authoring or reviewing a figure
script bound for a paper / poster / talk / grant. Each checklist item
maps to a rule in leaf 21.

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
- [ ] Signal-trace panels use an L-shaped scale bar (axes hidden,
      magnitudes from `CONFIG.SCALE_BAR.*`) — see
      `24_l-shaped-scale-bar.md`.
- [ ] Every statistical annotation carries all six of n / CI / method /
      p / effect / statistic, with symbols in italic and N (subjects)
      distinguished from n (windows/trials) — see
      `27_six-stat-annotation-doctrine.md` (STX-FM017).
- [ ] Every 2D heatmap (`imshow`) has a colorbar with tick labels, an
      axis label, and units — see `27_six-stat-annotation-doctrine.md`
      (STX-FM018).

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
- A representative signal-trace panel with full ticked axes *and* an
  L-shaped scale bar — redundant and visually noisy. Pick one (use
  the L-bar for representative traces; see playbook rule 7 and
  `24_l-shaped-scale-bar.md`).
- A stat annotation reading only `p < 0.05` or `*` with no n, CI,
  method, effect size, or test statistic anywhere in the figure —
  flagged by STX-FM017 (see `27_six-stat-annotation-doctrine.md`).
- A heatmap (`ax.imshow(...)`) with no `fig.colorbar(...)` call at
  all — flagged by STX-FM018 (see `27_six-stat-annotation-doctrine.md`).

## Cross-references

- `21_figure-prep-playbook.md` — the eight rules these items gate.
- `22_nan-sentinel-on-read.md` — concrete NaN-sentinel handling.
- `24_l-shaped-scale-bar.md` — L-shaped scale-bar worked example.
- `27_six-stat-annotation-doctrine.md` — six-stat annotation doctrine +
  heatmap colorbar requirement worked example.
