#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The figrecipe lint rule catalogue.

Pure data: the ``Rule`` literals for every rule figrecipe contributes, split by
family. Extracted from ``_linter_plugin.py``, which had grown past the file-size
limit because the catalogue (which gets a new entry every time a rule is added)
sat in the same file as the plugin wiring. The plugin now imports these and stays
an orchestrator.

Each factory takes the ``Rule`` class rather than importing it: ``Rule`` lives in
scitex-linter, and figrecipe must remain installable WITHOUT scitex-linter, so the
import has to stay deferred to the caller (see ``_linter_plugin.get_plugin``).

Families:
- ``make_fm_rules``   - FM001-FM019, figure/millimetre and figure-doctrine rules.
- ``make_fig_rules``  - FIG001, scientific-figure hygiene.
- ``make_plot_rules`` - P001-P009, bare-matplotlib and style-override rules.
"""

from __future__ import annotations

from typing import Any, Dict

__all__ = ["make_fm_rules", "make_fig_rules", "make_plot_rules"]


def make_fm_rules(Rule: Any) -> Dict[str, Any]:
    """FM001-FM019 - figure / millimetre layout and figure-doctrine rules."""
    # ------------------------------------------------------------------
    # FM: Figure / Millimeter rules (FM001-FM009)
    # ------------------------------------------------------------------
    FM001 = Rule(
        id="STX-FM001",
        severity="warning",
        category="figure",
        message="`figsize=` detected — inch-based figure sizing is imprecise for publications",
        suggestion=(
            "Use mm-based sizing: `stx.plt.subplots(axes_width_mm=40, axes_height_mm=28)` "
            "or `fig, ax = fr.subplots(axes_width_mm=40, axes_height_mm=28)` for precise control."
        ),
        requires="figrecipe",
    )

    FM002 = Rule(
        id="STX-FM002",
        severity="warning",
        category="figure",
        message="`tight_layout()` detected — layout is unpredictable across plot types",
        suggestion=(
            "Use mm-based margins: `stx.plt.subplots(margin_left_mm=15, margin_bottom_mm=12)` "
            "for deterministic layout control."
        ),
        requires="figrecipe",
    )

    FM003 = Rule(
        id="STX-FM003",
        severity="warning",
        category="figure",
        message='`bbox_inches="tight"` detected — can crop important elements unpredictably',
        suggestion=(
            "Use `fr.save(fig, './plot.png')` or `stx.io.save(fig, './plot.png')` "
            "which handle cropping intelligently."
        ),
        requires="figrecipe",
    )

    FM004 = Rule(
        id="STX-FM004",
        severity="info",
        category="figure",
        message="`constrained_layout=True` detected — conflicts with mm-based layout control",
        suggestion="Use mm-based layout from `stx.plt.subplots()` instead of constrained_layout.",
        requires="figrecipe",
    )

    FM005 = Rule(
        id="STX-FM005",
        severity="info",
        category="figure",
        message="`subplots_adjust()` with hardcoded fractions — fragile across figure sizes",
        suggestion=(
            "Use mm-based spacing: `stx.plt.subplots(space_w_mm=8, space_h_mm=10)` "
            "for size-independent layout."
        ),
        requires="figrecipe",
    )

    FM006 = Rule(
        id="STX-FM006",
        severity="info",
        category="figure",
        message="`plt.savefig()` detected — no provenance tracking",
        suggestion=(
            "Use `fr.save(fig, './plot.png')` or `stx.io.save(fig, './plot.png')` "
            "for recipe tracking and provenance."
        ),
        requires="figrecipe",
    )

    FM007 = Rule(
        id="STX-FM007",
        severity="info",
        category="figure",
        message="`rcParams` direct modification detected — hard to maintain across figures",
        suggestion="Use figrecipe style presets: `fr.load_style('SCITEX')` for consistent styling.",
        requires="figrecipe",
    )

    FM008 = Rule(
        id="STX-FM008",
        severity="warning",
        category="figure",
        message="`set_size_inches()` detected — bypasses mm-based layout control",
        suggestion=(
            "Use mm-based sizing: `fr.subplots(axes_width_mm=40, axes_height_mm=28)` "
            "or `stx.plt.subplots(axes_width_mm=40, axes_height_mm=28)` for precise control."
        ),
        requires="figrecipe",
    )

    FM009 = Rule(
        id="STX-FM009",
        severity="warning",
        category="figure",
        message="`ax.set_position()` detected — conflicts with mm-based layout control",
        suggestion=(
            "Use mm-based margins: `fr.subplots(margin_left_mm=15, margin_bottom_mm=12)` "
            "or `stx.plt.subplots(margin_left_mm=15, margin_bottom_mm=12)` for deterministic layout."
        ),
        requires="figrecipe",
    )

    # FM010 — figrecipe axes wrapper provides `set_xyt(x, y, t)` which
    # sets xlabel/ylabel/title in one call and records the metadata in
    # the recipe (used by `figrecipe.save()` provenance). Separate
    # set_xlabel/set_ylabel/set_title calls do not flow through the
    # recipe wrapper. Per neurovista 2026-06-14 — gated `requires="scitex"`.
    FM010 = Rule(
        id="STX-FM010",
        severity="warning",
        category="figure",
        message=(
            "`set_xlabel`/`set_ylabel`/`set_title` detected — figrecipe's "
            "`ax.set_xyt(x, y, t)` records the labels in the recipe in one call"
        ),
        suggestion=(
            "Replace `ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_title('T')` "
            "with `ax.set_xyt('X', 'Y', 'T')` so the labels are tracked by the "
            "recipe and stay consistent with figrecipe's panel-metadata model."
        ),
        requires="scitex",
    )

    # FM011 — direct `ax.spines[...].set_visible(False)` defeats the
    # figrecipe spine helper which also handles tick/label cleanup and
    # respects the global style. Per neurovista 2026-06-14.
    FM011 = Rule(
        id="STX-FM011",
        severity="warning",
        category="figure",
        message=(
            "`ax.spines[...].set_visible(False)` detected — figrecipe's "
            "`ax.hide_spines(top=True, right=True, ...)` is the canonical helper"
        ),
        suggestion=(
            "Replace `ax.spines['top'].set_visible(False); "
            "ax.spines['right'].set_visible(False)` with "
            "`ax.hide_spines(top=True, right=True)` — the wrapper also handles "
            "tick/label cleanup and stays consistent with the SciTeX style."
        ),
        requires="scitex",
    )

    # FM016 — raw matplotlib figure creation (`plt.subplots`/`plt.figure`/
    # `matplotlib.pyplot.*`/bare `subplots` from matplotlib.pyplot) bypasses
    # figrecipe entirely: the figure and every draw on it are un-recorded, so
    # there is no recipe and no clew provenance. Equivalence-gated — fires only
    # because the tracked equivalent (`fr.subplots`/`stx.plt.subplots`) exists.
    # category="figure" ⇒ auto-promoted to ERROR in project-type:research.
    # Per operator 2026-07-08 ("raw mpl バイパス検出大事") + neurovista fixture.
    FM016 = Rule(
        id="STX-FM016",
        severity="warning",
        category="figure",
        message=(
            "raw matplotlib figure creation (`plt.subplots`/`plt.figure`) detected "
            "— the figure and everything drawn on it bypass figrecipe recording "
            "(no recipe, no clew provenance)"
        ),
        suggestion=(
            "Create the figure with `fr.subplots(...)` (or `stx.plt.subplots(...)`) "
            "so all draws are recorded and the figure round-trips + becomes a clew "
            "claim. If raw matplotlib is genuinely required here, annotate the line "
            "with `# stx-allow: STX-FM016` (add the reason in an adjacent comment)."
        ),
        requires="figrecipe",
    )

    # FM017 — six-stat-annotation-completeness doctrine (companion to the
    # scitex-dev "Statistics Completeness Doctrine",
    # scitex_dev/_skills/scientific/03_reporting_02_statistics-completeness.md,
    # scitex-ai/scitex-dev#290, operator 2026-07-05): a reported statistic
    # must carry all six of n / 95% CI / method / p / effect size / test
    # statistic. Heuristic on literal annotation strings — only strings that
    # already look like a p-value annotation are considered, and only a
    # clear multi-field miss fires. category="figure" ⇒ auto-promoted to
    # ERROR in project-type:research.
    FM017 = Rule(
        id="STX-FM017",
        severity="warning",
        category="figure",
        message=(
            "statistical annotation string looks incomplete — missing "
            "several of the six required fields (n, CI, method, p, "
            "effect size, statistic)"
        ),
        suggestion=(
            "Every reported statistic needs all six: n=<count>, a 95% CI, "
            "the method/test name, the p-value, an effect size, and the "
            "test statistic (e.g. `t(df)=`). Add the missing fields to the "
            "annotation text (or move them to the caption / a stats table) — "
            "see 27_six-stat-annotation-doctrine.md for a compliant example. "
            "If this string is intentionally partial (e.g. significance "
            "stars only, full stats reported elsewhere), annotate the line "
            "with `# stx-allow: STX-FM017`."
        ),
    )

    # FM018 — heatmap-colorbar requirement: any 2D heatmap (imshow) must
    # ship a colorbar (with tick labels, axis label, and units — the
    # content half is documented, not statically checkable). Flags an
    # `imshow(...)` call with no `colorbar(...)` call anywhere in the same
    # function/module scope. category="figure" ⇒ auto-promoted to ERROR in
    # project-type:research.
    FM018 = Rule(
        id="STX-FM018",
        severity="warning",
        category="figure",
        message=(
            "`imshow(...)` detected with no `colorbar(...)` call in the "
            "same scope — 2D heatmaps require a colorbar with tick labels, "
            "an axis label, and units"
        ),
        suggestion=(
            "Add `fig.colorbar(im, ax=ax, label='<quantity> [<units>]')` "
            "(or `stx.plt.colorbar(...)`) after the `imshow` call, and make "
            "sure the colorbar keeps its tick labels. If this heatmap "
            "intentionally has no colorbar, annotate the line with "
            "`# stx-allow: STX-FM018`."
        ),
    )

    # FM019 - operator-issued (2026-07-12): every scientific figure needs a
    # caption, not just axis labels. Flags a scope that BUILDS a figure and
    # SAVES it with no caption anywhere in that scope. Conservative: a scope
    # that only writes data files is never examined, and a bare `save(...)`
    # only counts when its first arg is named like a figure -- so
    # `stx.io.save(df, "table.csv")` never fires. category="figure" => auto-
    # promoted to ERROR in project-type:research.
    FM019 = Rule(
        id="STX-FM019",
        severity="warning",
        category="figure",
        message=(
            "figure saved with no caption -- the reader must reconstruct what "
            "they are looking at from the axes alone, and a panel with no "
            "caption leaves a hole in the composed figure caption"
        ),
        suggestion=(
            "Pass `caption=...` to `fr.save(fig, path, caption='...')`, or call "
            "`fr.add_figure_caption(fig, '...')` / `fr.add_panel_captions(fig, "
            "[...])`. If this figure intentionally has no caption (a schematic, "
            "a QC plot that never leaves the analysis directory), annotate the "
            "line with `# stx-allow: STX-FM019`."
        ),
        requires="figrecipe",
    )

    return {
        "FM001": FM001,
        "FM002": FM002,
        "FM003": FM003,
        "FM004": FM004,
        "FM005": FM005,
        "FM006": FM006,
        "FM007": FM007,
        "FM008": FM008,
        "FM009": FM009,
        "FM010": FM010,
        "FM011": FM011,
        "FM016": FM016,
        "FM017": FM017,
        "FM018": FM018,
        "FM019": FM019,
    }


def make_fig_rules(Rule: Any) -> Dict[str, Any]:
    """FIG001 - scientific-figure hygiene (axis-range alignment across subplots)."""
    # ------------------------------------------------------------------
    # FIG: Scientific-figure hygiene rules (FIG001+)
    # FIG001 — multiple subplots that declare different literal axis
    # ranges via set_xlim / set_ylim without sharex/sharey will look
    # incomparable to the reader (rule #4 of the scientific-figure
    # standards). Warning, not error: two subplots can legitimately
    # plot different quantities.
    # ------------------------------------------------------------------
    FIG001 = Rule(
        id="STX-FIG001",
        severity="warning",
        category="figure",
        message=(
            "Subplots on the same figure declare different axis ranges via "
            "set_xlim/set_ylim. If these axes plot the same quantity, "
            "mismatched ranges destroy visual comparison (rule #4 of the "
            "scientific-figure standards)."
        ),
        suggestion=(
            "Either align the ranges (e.g., min(all)..max(all)), use "
            "sharex=True/sharey=True when calling plt.subplots, or annotate "
            "the call site with `# stx-allow: STX-FIG001` if the axes "
            "intentionally plot different quantities."
        ),
    )

    return {"FIG001": FIG001}


def make_plot_rules(Rule: Any) -> Dict[str, Any]:
    """P001-P009 - bare-matplotlib call hints and style-override rules."""
    # ------------------------------------------------------------------
    # P: Plot rules (P001-P005)
    # ------------------------------------------------------------------
    P001 = Rule(
        id="STX-P001",
        severity="info",
        category="plot",
        message="`ax.plot()` — consider `ax.stx_line()` for automatic CSV data export",
        suggestion="Replace `ax.plot(x, y)` with `ax.stx_line(x, y)` for tracked plotting.",
        requires="scitex",
    )

    P002 = Rule(
        id="STX-P002",
        severity="info",
        category="plot",
        message="`ax.scatter()` — consider `ax.stx_scatter()` for automatic CSV data export",
        suggestion="Replace `ax.scatter(x, y)` with `ax.stx_scatter(x, y)` for tracked plotting.",
        requires="scitex",
    )

    P003 = Rule(
        id="STX-P003",
        severity="info",
        category="plot",
        message="`ax.bar()` — consider `ax.stx_bar()` for automatic sample size annotation",
        suggestion="Replace `ax.bar(x, y)` with `ax.stx_bar(x, y)` for tracked plotting.",
        requires="scitex",
    )

    P004 = Rule(
        id="STX-P004",
        severity="info",
        category="plot",
        message="`plt.show()` is non-reproducible in batch/CI environments",
        suggestion="Remove `plt.show()` — figures are auto-saved in session output directory.",
    )

    P005 = Rule(
        id="STX-P005",
        severity="info",
        category="plot",
        message="`print()` inside @stx.session — use `logger` for tracked logging",
        suggestion="Replace `print(msg)` with `logger.info(msg)` (injected by @stx.session).",
        requires="scitex",
    )

    # ------------------------------------------------------------------
    # P: Style-override rules (P006-P009) — figrecipe + SciTeX style
    # centralizes marker size, font size, figure size, and line width.
    # Per-call overrides defeat the global style and produce inconsistent
    # figures across a paper.
    # ------------------------------------------------------------------
    P006 = Rule(
        id="STX-P006",
        severity="warning",
        category="plot",
        message="`scatter(..., s=...)` — drop `s=`; SciTeX style sizes markers automatically",
        suggestion=(
            "Remove the `s=` kwarg from scatter() calls. Marker size is tuned by the "
            "SciTeX style and overriding it produces inconsistent figures."
        ),
        requires="figrecipe",
    )

    P007 = Rule(
        id="STX-P007",
        severity="warning",
        category="plot",
        message="`fontsize=` kwarg — drop it; SciTeX style sets font sizes globally",
        suggestion=(
            "Remove `fontsize=` kwargs. Set sizes once via the SciTeX style / "
            "matplotlib rcParams instead of per-call overrides."
        ),
        requires="figrecipe",
    )

    P008 = Rule(
        id="STX-P008",
        severity="warning",
        category="plot",
        message="`figsize=` kwarg — drop it; figrecipe controls layout in mm via `figure_mm()`",
        suggestion=(
            "Remove `figsize=` from `plt.subplots()`/`plt.figure()`. Use "
            "`figrecipe.figure_mm()` (or the SciTeX style defaults) so journal "
            "column widths stay consistent."
        ),
        requires="figrecipe",
    )

    P009 = Rule(
        id="STX-P009",
        severity="warning",
        category="plot",
        message="`linewidth=` kwarg — drop it; SciTeX style sets line widths globally",
        suggestion=(
            "Remove `linewidth=`/`lw=` kwargs. Set widths once via the SciTeX "
            "style / matplotlib rcParams."
        ),
        requires="figrecipe",
    )

    return {
        "P001": P001,
        "P002": P002,
        "P003": P003,
        "P004": P004,
        "P005": P005,
        "P006": P006,
        "P007": P007,
        "P008": P008,
        "P009": P009,
    }


# EOF
