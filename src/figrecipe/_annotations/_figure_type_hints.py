#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-figure-type hints: where a comparison line goes, and which tests fit.

A skeleton, deliberately. Four entries, added because a real figure needed each
one. The registry grows an entry at a time as concrete cases turn up -- it is NOT
a pre-populated taxonomy of every plot type, and it should not become one.

Two things this is NOT:

- It does not COMPUTE anything. figrecipe displays statistics; the values come
  from a producer (scitex-stats, scipy, ...) and arrive as a
  :class:`~figrecipe._annotations._stat_result.StatResult`. This module only says
  where to *draw* the comparison and which tests are *conventional* for the shape
  of data a given plot type shows.
- It does not ENFORCE anything. ``methods`` is a list of hints for a human, not a
  whitelist: whether a statistical method suits a figure is a judgement about the
  DATA (paired? normal? how many groups?), which the plot type only hints at. A
  bar chart can legitimately carry a test not listed here. Nothing in figrecipe
  rejects a StatResult because of this table, and nothing should.
"""

from __future__ import annotations

__all__ = ["ComparisonGeometry", "FigureTypeHint", "hints_for", "known_figure_types"]

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ComparisonGeometry(str, Enum):
    """How a comparison between two conditions is drawn on this figure type."""

    BRACKET_ABOVE = "bracket_above"
    """A horizontal bracket spanning the two categories, above the data.

    The default for categorical plots (bar, box, violin): the x positions are
    discrete, so a bracket has two unambiguous endpoints to span.
    """

    INLINE_TEXT = "inline_text"
    """No bracket -- the statistic is written as text in the plot area.

    For plots with no discrete categories to span (a scatter, a correlation): the
    comparison is not *between two x positions*, it is a property of the whole
    cloud, so a bracket would point at nothing.
    """

    COLORBAR_ANNOTATION = "colorbar_annotation"
    """Significance is carried by the image itself (e.g. a mask or contour).

    A heatmap has no free space to run a bracket through, and a cell-by-cell test
    produces one statistic per cell, not one per pair -- so significance is shown
    by marking the cells, with the method and correction named in the caption.
    """


@dataclass(frozen=True)
class FigureTypeHint:
    """Hints for annotating one figure type.

    Parameters
    ----------
    figure_type : str
        The plotting call this describes (``"bar"``, ``"scatter"``, ...).
    geometry : ComparisonGeometry
        How to draw a comparison on this figure type.
    methods : list of str
        Statistical methods CONVENTIONALLY used for the kind of data this plot
        shows. A hint for a human, never a whitelist -- see the module docstring.
    note : str
        One line on the judgement the caller still has to make themselves.
    """

    figure_type: str
    geometry: ComparisonGeometry
    methods: List[str] = field(default_factory=list)
    note: str = ""

    @property
    def draws_bracket(self) -> bool:
        """Whether a comparison on this figure type is drawn as a bracket."""
        return self.geometry is ComparisonGeometry.BRACKET_ABOVE


# Grown one entry at a time, each from a figure that actually needed it.
_HINTS: Dict[str, FigureTypeHint] = {
    "bar": FigureTypeHint(
        figure_type="bar",
        geometry=ComparisonGeometry.BRACKET_ABOVE,
        methods=["Welch's t-test", "Mann-Whitney U", "one-way ANOVA"],
        note=(
            "Which test depends on the data, not the plot: paired or independent, "
            "normal or not, two groups or more. The bar chart cannot tell you."
        ),
    ),
    "box": FigureTypeHint(
        figure_type="box",
        geometry=ComparisonGeometry.BRACKET_ABOVE,
        methods=["Mann-Whitney U", "Wilcoxon signed-rank", "Kruskal-Wallis"],
        note=(
            "A box plot shows a distribution's shape, so it is usually reached for "
            "when a rank-based test is appropriate -- but that is a convention, not "
            "a rule."
        ),
    ),
    "violin": FigureTypeHint(
        figure_type="violin",
        geometry=ComparisonGeometry.BRACKET_ABOVE,
        methods=["Mann-Whitney U", "Kruskal-Wallis"],
        note="As for a box plot: the shape is shown, so the test is usually rank-based.",
    ),
    "scatter": FigureTypeHint(
        figure_type="scatter",
        geometry=ComparisonGeometry.INLINE_TEXT,
        methods=["Pearson correlation", "Spearman correlation", "linear regression"],
        note=(
            "There are no discrete categories to span, so a bracket has nothing to "
            "point at. Write the statistic inline instead."
        ),
    ),
    "imshow": FigureTypeHint(
        figure_type="imshow",
        geometry=ComparisonGeometry.COLORBAR_ANNOTATION,
        methods=["cluster-based permutation", "FDR-corrected mass-univariate"],
        note=(
            "One statistic per cell, not one per pair -- mark the significant cells "
            "and name the multiple-comparison correction in the caption."
        ),
    ),
}

# Plot calls that are the same shape as an entry above.
_ALIASES: Tuple[Tuple[str, str], ...] = (
    ("barh", "bar"),
    ("boxplot", "box"),
    ("violinplot", "violin"),
    ("pcolormesh", "imshow"),
    ("matshow", "imshow"),
)


def known_figure_types() -> List[str]:
    """Figure types the registry has an entry for, aliases included."""
    return sorted(set(_HINTS) | {alias for alias, _ in _ALIASES})


def hints_for(figure_type: str) -> Optional[FigureTypeHint]:
    """Return the hint for ``figure_type``, or None when there is no entry yet.

    None means "the registry has nothing to say", NOT "this figure type is wrong".
    Most plot types have no entry -- the table is a short list of cases that came
    up, not a closed world. Callers must treat None as silence.
    """
    key = figure_type.lower()
    for alias, target in _ALIASES:
        if key == alias:
            key = target
            break
    return _HINTS.get(key)


# EOF
