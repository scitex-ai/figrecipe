---
description: |
  [TOPIC] Six-stat annotation doctrine + heatmap colorbar requirement
  [DETAILS] Operator-issued reporting doctrine (2026-07-05): every statistical annotation on a figure must carry all six of n / 95% CI / method / p-value / effect size / test statistic, statistical symbols render in italic, and N (subjects) is kept distinct from n (windows/trials/samples). Pairs with the separate heatmap-colorbar requirement — every 2D imshow-style plot must ship a colorbar with tick labels, an axis label, and units. Both are checked (soft, warning-level) by STX-FM017 / STX-FM018 in figrecipe's lint plugin.
tags: [figrecipe-six-stat-doctrine, figrecipe-stat-annotation, figrecipe-colorbar, figrecipe]
---


# Six-stat Annotation Doctrine + Heatmap Colorbar Requirement

Figure-annotation half of the operator-issued "Statistics Completeness
Doctrine" (2026-07-05, relayed via NeuroVista, adopted fleet-wide). The
manuscript/caption/table-authoring half of this doctrine lives in
`scitex-dev/_skills/scientific/03_reporting_02_statistics-completeness.md`
(scitex-ai/scitex-dev#290) — read that leaf for the full Results-section /
stats-table guidance. This leaf covers the figure-annotation surface:
`ax.add_stat_annotation(...)` (see `_wrappers/_stat_annotation.py`) and any
`ax.text(...)` / `ax.annotate(...)` used to label a comparison directly on
a panel, plus the separate heatmap-colorbar requirement.

## Rule 1 — the six required fields

A statistical annotation on a figure (a p-value or effect-size label next
to a comparison) is **incomplete** unless all six of the following appear
somewhere the reader can find them — inline in the annotation, in the
caption, or in an accompanying stats table:

1. **n** — sample size / number of observations in the comparison.
2. **CI** — confidence interval (typically 95%) around the estimate.
3. **method** — which statistical test/method was used (e.g. "Welch's
   t-test", "Wilcoxon signed-rank", "Pearson correlation").
4. **p** — the p-value (exact value, or `p < 0.001` below display
   precision) — never a bare significance star with no number behind it.
5. **effect** — the effect size (Cohen's d, r, eta-squared, odds ratio,
   ... whichever is conventional for the test used).
6. **statistic** — the test statistic itself (`t(df)=`, `F(df1,df2)=`,
   `U=`, `chi2(df)=`, ...).

A p-value alone, or a p-value plus effect size but no CI or no n, is not
sufficient. If the panel is too crowded for all six inline, push the rest
to the caption (pairs with `21_figure-prep-playbook.md`) — but they must
land somewhere in the figure's own text, not only in a separate results
paragraph the reader has to cross-reference.

### Italic statistical symbols

Statistical symbols (`p`, `t`, `F`, `r`, `U`, `d`, ...) render in **italic**
in figure text — matplotlib mathtext via `$\it{p}$` (or the `r"$\it{...}$"`
raw-string form) does this correctly; a plain `"p="` string does not.
`draw_stat_annotation`'s built-in `style="p_value"` / `style="both"` modes
already do this (see `_wrappers/_stat_annotation.py::draw_stat_annotation`,
which emits `$\it{p}$ < 0.001` / `$\it{p}$ = 0.003`) — prefer those modes
over hand-rolled text so the italic convention is automatic.

### N vs n

Distinguish **N** (number of subjects / patients — capital N) from **n**
(number of windows / samples / trials *within* a subject — lowercase n)
as separate, explicitly-subscripted quantities whenever both are
relevant:

```
N = 12 patients, n = 340 windows
```

Collapsing these into a single `n=` when both a subject count and a
within-subject sample count exist hides the actual unit of statistical
independence from the reader — a common and serious inferential error in
per-window / per-trial neuroscience and physiology figures.

### Compliant example

```python
ax.add_stat_annotation(
    x1=0, x2=1,
    text=(
        r"$N$=12, $n$=340, $r$=0.42, 95% CI [0.21, 0.60], "
        r"$t$(338)=5.1, $p$<0.001 (Pearson correlation)"
    ),
)
```

All six fields are present (n, CI, method, p, effect, statistic), N and n
are distinguished, and every statistical symbol is wrapped for italic
rendering. Compare to the incomplete, lint-flagged form:

```python
ax.add_stat_annotation(x1=0, x2=1, text="p=0.03")  # STX-FM017: missing n, CI, method, effect, statistic
```

## Rule 2 — heatmap colorbar requirement

Any 2D heatmap (an `imshow`-style plot of a 2D array — `imshow`, `matshow`,
`pcolormesh`, ...) MUST have:

- a colorbar,
- tick labels on that colorbar,
- an axis label on the colorbar, and
- units on that axis label.

This is non-negotiable — the same tier as figrecipe's existing axis-label
and unit requirements elsewhere in this lint plugin. A heatmap with no
colorbar leaves the reader unable to read any absolute value off the
image; a colorbar with no label/units leaves them unable to interpret
what they *can* read.

### Compliant example

```python
fig, ax = fr.subplots()
im = ax.imshow(power_2d, cmap="viridis", vmin=0, vmax=1)
fig.colorbar(im, ax=ax, label="power [a.u.]")  # tick labels on by default
```

figrecipe's imperative `ax.imshow(...)` does **not** auto-add a colorbar
(only the declarative YAML/dict plot-spec path does, via
`_api/_plot_helpers._maybe_add_colorbar`) — a script using the direct
Python API must add its own `fig.colorbar(...)` call.

## Lint enforcement

Both rules have a soft (warning-level) static check in figrecipe's lint
plugin (`src/figrecipe/_quality/_linter_plugin.py`), `category="figure"`
so they auto-promote to error under `project-type: research`:

- **STX-FM017** (`_stat_annotation_fields_checker.py`) — flags a literal
  annotation string that looks like a stats annotation (contains a
  p-value marker) but is clearly missing several of the six fields.
  Heuristic and conservative by design: plain captions with no p-value
  marker are never flagged, and only literal string constants are
  inspected (f-strings are skipped, not guessed at).
- **STX-FM018** (`_heatmap_colorbar_checker.py`) — flags an `imshow(...)`
  call with no `colorbar(...)` call anywhere in the same function/module
  scope. It cannot statically verify tick labels / axis label / units —
  that half of Rule 2 is enforced by review, matching the "doc-only where
  a linter can't reach" acknowledgement in the sister scitex-dev doctrine.

Opt out per call site with `# stx-allow: STX-FM017` / `# stx-allow:
STX-FM018` when a partial annotation or colorbar-less heatmap is
intentional (e.g. significance stars only, with the full stats reported
in a table elsewhere).

## Cross-references

- `scitex-dev/_skills/scientific/03_reporting_02_statistics-completeness.md`
  — the manuscript/caption/stats-table half of the six-field doctrine
  (scitex-ai/scitex-dev#290).
- `21_figure-prep-playbook.md` — where caption content (including
  overflow stats) belongs relative to the rest of the figure-prep rules.
- `_wrappers/_stat_annotation.py` — `draw_stat_annotation` /
  `ax.add_stat_annotation(...)`, the dedicated annotation helper this
  doctrine targets.
- `05_styles.md` — SCITEX style font sizes (annotation text follows the
  `stat_annotation.fontsize_pt` style key, not a hardcoded `fontsize=`).
