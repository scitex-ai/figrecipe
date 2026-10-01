#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Warn when a composed figure is wider than the page can take.

A composite wider than the text block does not get rejected downstream — it
gets SILENTLY SHRUNK. LaTeX wraps an over-wide graphic in ``\\resizebox``, which
scales the whole thing including its text, so 8pt labels arrive at the reader
as 6pt and every panel's font size drifts by whatever factor the overflow
happened to be. The figure looks fine in isolation and wrong on the page, and
nothing in the compile says why.

figrecipe is the only party that can catch this cheaply: it holds the composed
canvas width at the moment it is built, before anything downstream has to
guess. The check runs at compose time and WARNS — it does not refuse, because
an over-wide composite is legitimate for a poster, a slide, or a supplementary
figure that will never go through the manuscript's text block.

Threshold: ``COMPOSE_MAX_WIDTH_MM``, 180mm — a typical single-column journal
text width. Override per call, or silence with the standard warnings filter if
a project's page is genuinely wider.
"""

from __future__ import annotations

import warnings
from typing import Any, Optional

#: Widest composite that fits a typical journal text block, in millimetres.
#: 180mm is the common full-text-width figure size; wider than this and the
#: writer has to rescale, which is the failure this module exists to announce.
COMPOSE_MAX_WIDTH_MM = 180.0

MM_PER_INCH = 25.4


def figure_width_mm(fig: Any) -> Optional[float]:
    """The rendered width of ``fig`` in millimetres, or None if unobtainable.

    Accepts either a matplotlib figure or figrecipe's RecordingFigure wrapper
    (which delegates ``get_size_inches``). Returns None rather than raising:
    a quality warning must never be the reason a compose call fails.
    """
    getter = getattr(fig, "get_size_inches", None)
    if getter is None:
        inner = getattr(fig, "_fig", None)
        getter = getattr(inner, "get_size_inches", None)
    if getter is None:
        return None
    try:
        return float(getter()[0]) * MM_PER_INCH
    except Exception:  # pragma: no cover - defensive; never break compose
        return None


def check_compose_width(
    fig: Any,
    max_width_mm: float = COMPOSE_MAX_WIDTH_MM,
    dpi: Optional[int] = None,
) -> Optional[float]:
    """Warn if ``fig`` is wider than ``max_width_mm``. Returns the width in mm.

    Returns None when the width could not be determined, in which case nothing
    is warned — an unknown width is reported as unknown rather than assumed to
    be fine or assumed to be a violation.
    """
    width_mm = figure_width_mm(fig)
    if width_mm is None or width_mm <= max_width_mm:
        return width_mm

    over = width_mm - max_width_mm
    px = f", {round(width_mm / MM_PER_INCH * dpi)}px at {dpi}dpi" if dpi else ""
    warnings.warn(
        f"figrecipe: composed figure is {width_mm:.1f}mm wide{px}, which "
        f"exceeds {max_width_mm:.0f}mm of usable text width by {over:.1f}mm. "
        f"LaTeX will wrap an over-wide graphic in \\resizebox and shrink it — "
        f"including its TEXT — so panel labels will not render at the size the "
        f"style set, and each panel drifts by the same hidden factor. Reduce "
        f"the panel widths or the number of columns so the composite fits, "
        f"rather than letting the page scale it. Intentional for a poster or "
        f"slide? This is a warning, not a refusal.",
        UserWarning,
        stacklevel=3,
    )
    return width_mm


__all__ = [
    "COMPOSE_MAX_WIDTH_MM",
    "check_compose_width",
    "figure_width_mm",
]

# EOF
