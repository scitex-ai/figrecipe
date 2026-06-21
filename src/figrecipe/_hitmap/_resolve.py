#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Normalize figure inputs for hitmap extraction.

The hitmap routines operate on a raw ``matplotlib.figure.Figure`` whose
``.axes`` is a flat list of ``Axes``. figrecipe's public figure object is a
``RecordingFigure`` wrapper whose ``.axes`` is a 2-D grid (``[[ax, ...], ...]``)
and whose real matplotlib figure lives on ``._fig`` / ``.figure``. Resolving to
the underlying matplotlib figure up front lets every extractor stay simple and
work for both wrapped and raw inputs.
"""


def as_mpl_figure(fig):
    """Return the underlying ``matplotlib.figure.Figure`` for ``fig``.

    Accepts a raw matplotlib figure (returned unchanged) or any wrapper that
    exposes the matplotlib figure via ``._fig`` or ``.figure``.
    """
    try:
        import matplotlib.figure as _mf
    except Exception:
        return fig

    if isinstance(fig, _mf.Figure):
        return fig

    for attr in ("_fig", "figure", "_fig_mpl", "_mpl_fig"):
        candidate = getattr(fig, attr, None)
        if isinstance(candidate, _mf.Figure):
            return candidate

    return fig


# EOF
