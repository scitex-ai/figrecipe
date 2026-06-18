#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-axes post-replay finalization passes for figure reproduction.

These passes run after every axes' calls/decorations/insets have been replayed
and after colorbars are reconstructed. They are extracted from ``_core.py`` to
keep that module focused on the top-level reproduce flow (and under the
project's per-file line budget). The ordering here is load-bearing -- see the
inline comments on each pass.
"""

from typing import List, Optional

import numpy as np

from .._recorder import FigureRecord
from .._utils._grid import parse_grid_id


def finalize_reproduced_axes(
    fig,
    axes_2d: np.ndarray,
    record: FigureRecord,
    nrows: int,
    ncols: int,
    calls: Optional[List[str]],
    skip_decorations: bool,
) -> None:
    """Run the per-axes finalization passes in their required order.

    Parameters
    ----------
    fig : matplotlib Figure
        The reproduced figure (kept for signature symmetry / future passes).
    axes_2d : ndarray of Axes
        The 2D grid of raw matplotlib axes.
    record : FigureRecord
        The record being reproduced.
    nrows, ncols : int
        Grid dimensions.
    calls : list of str, optional
        Restrict reproduction to these call ids (mirrors ``reproduce``).
    skip_decorations : bool
        When True, recorded limits live in decorations and are not reapplied.
    """
    from ..styles._style_applier import finalize_special_plots, finalize_ticks

    # Finalize tick configuration and special plot types.
    for row in range(nrows):
        for col in range(ncols):
            finalize_ticks(axes_2d[row, col])
            finalize_special_plots(axes_2d[row, col], record.style or {})

    # Reapply imshow tick/spine suppression after finalize_ticks: it can
    # re-add numeric ticks on an imshow axes, and finalize_special_plots skips
    # a labelled imshow (is_specgram heuristic). Keyed on the recorded call
    # name -- the same discriminator the live imshow wrapper uses -- so save
    # and reproduce hide ticks identically (never touches a real specgram).
    from ._replay_axes import finalize_imshow_axes

    for ax_key, ax_record in record.axes.items():
        parsed = parse_grid_id(ax_key)
        row, col = parsed if parsed else (0, 0)
        finalize_imshow_axes(axes_2d[row, col], ax_record, record.style)

    # Re-apply recorded set_xlim / set_ylim LAST so explicit limits win over any
    # autoscale re-engaged by later decorations (e.g. set_xscale), insets,
    # colorbars, or the tick finalizers (NeuroVista Ask 2). Skipped when the
    # caller asked to skip decorations (the limits live in decorations).
    if not skip_decorations:
        from ._reapply_limits import reapply_recorded_limits

        for ax_key, ax_record in record.axes.items():
            parsed = parse_grid_id(ax_key)
            row, col = parsed if parsed else (0, 0)
            reapply_recorded_limits(axes_2d[row, col], ax_record, calls)


__all__ = ["finalize_reproduced_axes"]
