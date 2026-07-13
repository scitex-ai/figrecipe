#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Thousands-separator (comma) tick-label formatting for matplotlib axes.

Mirrors the ``OOMFormatter`` / ``sci_note`` pattern in ``_sci_note.py``: a
small ``matplotlib.ticker.Formatter`` subclass plus a public helper that
wires it onto an axis via ``set_major_formatter``. Added per a downstream
(neurovista) request that hand-rolled ``f"{n:,}"`` for tick labels and
sample-size annotation numbers -- this gives both a single, reusable
formatter to hook into instead.
"""

__all__ = ["CommaFormatter", "comma_format"]

from typing import Any

import matplotlib.ticker

from ._base import get_axis_from_wrapper, validate_axis


class CommaFormatter(matplotlib.ticker.Formatter):
    """Format tick values with thousands-separator commas (e.g. ``12,000``).

    Parameters
    ----------
    fformat : str, optional
        A ``str.format``-style spec applied to each tick value. Default is
        ``"{:,.0f}"`` (integer, comma-grouped). Use e.g. ``"{:,.2f}"`` for
        two decimal places.

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> from figrecipe.styles import CommaFormatter
    >>> fig, ax = plt.subplots()
    >>> ax.plot([0, 12000, 24000], [0, 1, 2])
    >>> ax.xaxis.set_major_formatter(CommaFormatter())
    """

    def __init__(self, fformat: str = "{:,.0f}"):
        self.fformat = fformat

    def __call__(self, x: float, pos: Any = None) -> str:
        return self.fformat.format(x)


def comma_format(
    ax: Any,
    x: bool = False,
    y: bool = False,
    fformat: str = "{:,.0f}",
) -> Any:
    """Apply thousands-separator comma formatting to tick labels.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The Axes object to modify (a figrecipe ``RecordingAxes`` wrapper is
        also accepted -- the underlying axes is unwrapped automatically).
    x : bool
        Whether to comma-format the x-axis. Default: False.
    y : bool
        Whether to comma-format the y-axis. Default: False.
    fformat : str
        ``str.format``-style spec per tick value. Default: ``"{:,.0f}"``.

    Returns
    -------
    Axes
        The modified Axes object.

    Examples
    --------
    >>> import figrecipe as fr
    >>> fig, ax = fr.subplots()
    >>> ax.plot([0, 12000, 24000], [0, 1, 2])
    >>> fr.styles.comma_format(ax, x=True)  # "0", "12,000", "24,000"
    >>> # Or via the RecordingAxes wrapper method:
    >>> ax.comma_format(x=True)
    """
    validate_axis(ax)
    ax = get_axis_from_wrapper(ax)

    if x:
        ax.xaxis.set_major_formatter(CommaFormatter(fformat))
    if y:
        ax.yaxis.set_major_formatter(CommaFormatter(fformat))

    return ax


# EOF
