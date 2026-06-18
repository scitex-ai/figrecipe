#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic constrained-layout settling for reproducible ``bbox_inches='tight'`` saves.

``constrained_layout`` solves the axes rectangle iteratively: each ``draw()``
nudges the layout toward a fixed point but does not reach it in one pass. When a
figure is then saved with ``bbox_inches="tight"`` (which re-measures the ink to
crop), the saved pixel SIZE is a function of how many draws preceded the save --
NOT of the figure's content alone.

That makes a recipe unreproducible: the original ``fig`` is drawn many times over
its build + save, while a freshly ``reproduce()``-d figure is drawn only a few
times, so the two land on different layout iterates and their tight crops differ
by a few pixels. The validator then sees a SIZE mismatch (different pixel
dimensions) and reports the figure as not-reproduced, even though every artist is
identical (NeuroVista Fig 02 panel c: bar + log y-axis + legend + 5 text()).

``settle_constrained_layout`` removes that history dependence: it draws the
figure until the axes positions stop moving (within ``tol``), so any figure --
however many times it was drawn before -- converges to the SAME deterministic
layout (and therefore the SAME tight-crop size) before saving. The first draw
still surfaces a ``constrained_layout collapsed to zero`` warning so the existing
collapse fallback in ``save_figure`` keeps working.
"""

import warnings
from typing import Optional

import numpy as np

__all__ = ["settle_constrained_layout"]


def settle_constrained_layout(
    fig,
    max_iter: int = 10,
    tol: float = 1e-4,
) -> bool:
    """Draw ``fig`` until its constrained_layout axes positions converge.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The figure to settle (must have ``constrained_layout`` enabled for the
        iteration to matter; on a fixed layout it converges after one draw).
    max_iter : int
        Maximum number of draw passes (default 10). Layouts here settle in a few
        passes; the cap guards against a non-converging/oscillating layout.
    tol : float
        Convergence tolerance on the max change of any axes' ``(x0, y0, w, h)``
        between consecutive draws, in figure-fraction units (default 1e-4 ~=
        0.1 px on a 1000 px canvas).

    Returns
    -------
    bool
        True if a ``constrained_layout collapsed to zero`` warning was emitted on
        the FIRST draw (so ``save_figure`` can trigger its non-tight fallback);
        False otherwise.

    Notes
    -----
    Only the first draw is watched for the collapse warning -- that is the same
    signal the previous single pre-flight ``draw()`` relied on, and re-checking
    every iteration would spam identical warnings. Convergence is measured on the
    raw matplotlib axes (``fig.axes``); a figure with no axes converges trivially.
    """
    prev: Optional[np.ndarray] = None
    collapse_detected = False

    for i in range(max_iter):
        if i == 0:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                try:
                    fig.canvas.draw()
                except Exception:
                    # Mirror the prior pre-flight behaviour: a draw failure is not
                    # fatal here; the real save below raises and is handled there.
                    return False
                if any("collapsed to zero" in str(w.message) for w in caught):
                    collapse_detected = True
            if collapse_detected:
                # Don't keep iterating a collapsed layout; let the caller fall back.
                return True
        else:
            try:
                fig.canvas.draw()
            except Exception:
                break

        cur = np.array([ax.get_position().bounds for ax in fig.axes], dtype=float)
        if prev is not None and cur.shape == prev.shape:
            if cur.size == 0 or np.max(np.abs(cur - prev)) < tol:
                break
        prev = cur

    return collapse_detected
