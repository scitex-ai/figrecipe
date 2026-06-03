#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tick-friendly axis-limit helper (issue #140).

Provides :func:`nice_lim` — snap an axis limit to a "round" boundary above
(and optionally below) the data extent, so the right (or top) spine doesn't
get its own tick label and the axis range remains tick-friendly.

Recurring need across scientific figures (timelines, count histograms,
day-since-baseline x-axes, etc.). Sits alongside the existing
:func:`figrecipe._utils._calc_nice_ticks.calc_nice_ticks` — the two solve
adjacent problems (tick locations vs. axis limits) using the same "snap to
order-of-magnitude" heuristic.

Examples
--------
Day-since-start x-axis where ``data.max() == 367``::

    >>> from figrecipe import nice_lim
    >>> nice_lim([0, 367], round_to=10)
    (0.0, 370.0)
    >>> nice_lim([0, 367])                   # auto round step
    (0.0, 400.0)

Count histogram ``y`` axis where the tallest bar must not touch the top
spine::

    >>> nice_lim([0, 0, 1, 4, 19], round_to=5)
    (0.0, 20.0)

Negative data with ``lower=None`` rounds both edges outward::

    >>> nice_lim([-3, 27], lower=None, round_to=10)
    (-10.0, 30.0)
"""

from __future__ import annotations

import math
from typing import Any, Optional, Tuple


def nice_lim(
    data: Any,
    lower: Optional[float] = 0.0,
    round_to: Optional[float] = None,
) -> Tuple[float, float]:
    """Return ``(lo, hi)`` axis limits snapped to tick-friendly boundaries.

    Parameters
    ----------
    data : array-like
        Data values to enclose. ``numpy`` arrays, lists, tuples, and any
        iterable of floats are accepted. ``NaN`` is ignored. Empty input
        returns ``(lower or 0, lower or 0 + round_to_or_1)`` instead of
        crashing.
    lower : float or None, optional
        Lower bound. ``0.0`` (default) is the common case for time-since-start
        / count axes — leaves the left edge anchored at zero. ``None`` snaps
        the left edge *down* to the nearest multiple of ``round_to`` below
        ``data.min()``.
    round_to : float or None, optional
        Snap step. ``None`` (default) picks an auto step equal to
        ``10 ** floor(log10(max(|data|, 1)))`` — i.e. the order of magnitude
        of the data range. Pass an explicit value (e.g. ``5``, ``10``) to
        control tick spacing.

    Returns
    -------
    (lo, hi) : tuple of float
        Where ``lo <= data.min()`` and ``hi >= data.max() + epsilon`` and
        both endpoints are exact multiples of ``round_to`` (when ``round_to``
        is set explicitly or auto-chosen). If ``data.max()`` already sits on
        a round boundary, ``hi`` is bumped by one ``round_to`` so the value
        doesn't sit directly on the right spine.

    Notes
    -----
    This helper is intentionally separate from
    :func:`figrecipe._utils._calc_nice_ticks.calc_nice_ticks` — that one
    returns tick *locations* given a fixed range, this one returns the
    *range* given the data extent. Pair them by calling ``nice_lim`` first
    and feeding the result into ``ax.set_xlim`` / ``ax.set_ylim`` (or any
    locator that wants a sensible upper bound).
    """
    try:
        import numpy as _np

        arr = _np.asarray(list(data), dtype=float).ravel()
        if arr.size == 0:
            return _empty_lim(lower, round_to)
        mask = ~_np.isnan(arr)
        if not mask.any():
            return _empty_lim(lower, round_to)
        dmin = float(arr[mask].min())
        dmax = float(arr[mask].max())
    except (ImportError, ValueError, TypeError):
        # Fallback for non-array iterables (no numpy available).
        seq = [float(v) for v in data if v == v]  # skip NaN via self-equality
        if not seq:
            return _empty_lim(lower, round_to)
        dmin, dmax = min(seq), max(seq)

    if round_to is None:
        span = max(abs(dmax), abs(dmin), 1.0)
        step = 10 ** math.floor(math.log10(span)) if span > 0 else 1.0
    else:
        step = float(round_to)
    if step <= 0:
        raise ValueError(f"round_to must be positive, got {round_to!r}")

    hi = math.ceil(dmax / step) * step
    if hi <= dmax:
        # data already sits on a round boundary; push one step so the value
        # isn't pinned to the right spine.
        hi += step

    if lower is None:
        lo = math.floor(dmin / step) * step
        if lo >= dmin:
            lo -= step
    else:
        lo = float(lower)

    return (lo, hi)


def _empty_lim(
    lower: Optional[float],
    round_to: Optional[float],
) -> Tuple[float, float]:
    """Sane fallback for empty / all-NaN data."""
    lo = 0.0 if lower is None else float(lower)
    step = 1.0 if round_to is None else float(round_to)
    return (lo, lo + step)
