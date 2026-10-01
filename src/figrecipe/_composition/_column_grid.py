#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The mm column grid: the small set of panel widths a page actually has room for.

Operator's figure design system (via neurovista, 2026-06-28): panel widths snap
to 0.5 / 1 / 1.5 / 2 columns, where 2 columns is the full content width (~180mm),
and wide panels are allowed as deliberate exceptions.

WHY A GRID RATHER THAN FREE WIDTHS. Panels sized ad hoc do not line up across
rows, and the mismatch is invisible at thumbnail size and glaring in print. Worse,
a panel sized past the content width forces the page to rescale the whole figure
— shrinking its TEXT along with it, which is what ``_compose_width`` warns about.
A grid makes the legal widths countable, so "does this fit?" has an answer before
anything is rendered.

THIS MODULE ONLY COMPUTES AND SNAPS. It does not resize anything and is not
wired into ``compose``: the author chooses a width and passes it to
``fr.subplots(axes_width_mm=...)``. Enforcing the grid inside compose would mean
silently moving panels the author placed, which is the opposite of the no-rescale
rule this grid exists to serve.

    >>> column_grid_mm()
    {0.5: 43.5, 1.0: 89.0, 1.5: 134.5, 2.0: 180.0}
    >>> snap_to_column_grid(95)
    89.0
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

#: Full content width of a two-column page, in mm. Matches
#: ``_quality._compose_width.COMPOSE_MAX_WIDTH_MM`` — the widest a composite can
#: be before the page has to rescale it.
CONTENT_WIDTH_MM = 180.0

#: Default gutter between adjacent columns, in mm.
DEFAULT_GAP_MM = 2.0

#: The column counts a panel may occupy. 2.0 is the full content width.
COLUMN_STEPS: Tuple[float, ...] = (0.5, 1.0, 1.5, 2.0)


def column_grid_mm(
    content_width_mm: float = CONTENT_WIDTH_MM,
    gap_mm: float = DEFAULT_GAP_MM,
) -> Dict[float, float]:
    """The legal panel widths, in mm, keyed by how many columns they span.

    A 1-column panel is half the content width MINUS one gutter, because two of
    them plus the gutter between them must total the content width. Fractional
    steps interpolate on that basis, and 2.0 is the content width exactly — a
    full-width panel has no neighbour, so it gives up no gutter.
    """
    one_col = (content_width_mm - gap_mm) / 2.0
    grid: Dict[float, float] = {}
    for step in COLUMN_STEPS:
        if step == 2.0:
            grid[step] = float(content_width_mm)
        else:
            # n columns spans n single columns plus the (n-1) gutters between.
            grid[step] = round(one_col * step + gap_mm * (step - 1) * 0.5 * 2, 1)
    return grid


def snap_to_column_grid(
    width_mm: float,
    content_width_mm: float = CONTENT_WIDTH_MM,
    gap_mm: float = DEFAULT_GAP_MM,
    allow_wider: bool = False,
) -> float:
    """The nearest legal column width to ``width_mm``.

    Never returns wider than the content width unless ``allow_wider`` — a panel
    past the content width is the case the page silently rescales, so widening
    is opt-in rather than something a snap does quietly.
    """
    grid = column_grid_mm(content_width_mm, gap_mm)
    widths = sorted(grid.values())
    if width_mm > widths[-1] and allow_wider:
        return float(width_mm)
    return min(widths, key=lambda w: (abs(w - width_mm), w))


def columns_for_width(
    width_mm: float,
    content_width_mm: float = CONTENT_WIDTH_MM,
    gap_mm: float = DEFAULT_GAP_MM,
    tolerance_mm: float = 0.6,
) -> Optional[float]:
    """How many columns ``width_mm`` occupies, or None if it is off-grid.

    None is the useful answer for a width that matches no step: it says "this
    panel is not on the grid" rather than rounding it onto one and implying it
    was. ``tolerance_mm`` absorbs the rounding in ``column_grid_mm``.
    """
    for step, w in column_grid_mm(content_width_mm, gap_mm).items():
        if abs(w - width_mm) <= tolerance_mm:
            return step
    return None


__all__ = [
    "COLUMN_STEPS",
    "CONTENT_WIDTH_MM",
    "DEFAULT_GAP_MM",
    "column_grid_mm",
    "columns_for_width",
    "snap_to_column_grid",
]

# EOF
