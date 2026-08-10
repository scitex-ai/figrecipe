#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The FIG and P rule catalogues, split out of ``_linter_rules.py``.

Extracted 2026-08-09 because the FM family is the one that grows — every new
figure-anti-pattern detection adds a ``Rule`` literal — and the combined
catalogue had reached 476 of its 512-line ceiling, so the next rule could not
be added without a refactor first. These two families are effectively closed
(FIG001 alone; P001-P009 mirroring matplotlib call shapes), so moving them is
what buys FM its headroom.

``Rule`` is passed IN rather than imported: figrecipe is installable without
scitex-linter, so the import has to stay deferred to the caller (see
``_linter_plugin.get_plugin``).

Both makers are re-exported by ``_linter_rules`` so existing imports keep
working unchanged.
"""

from __future__ import annotations

from typing import Any, Dict


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


__all__ = ["make_fig_rules", "make_plot_rules"]

# EOF
