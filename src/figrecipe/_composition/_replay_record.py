#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replay a recorded source panel onto a composed axes (grid + mm paths).

Extracted from ``_compose.py`` to keep that orchestrator under the per-file
line budget. Both helpers replay a source panel's recorded ``calls`` +
``decorations`` onto a target matplotlib axes, register the axes record on the
composed figure's record, then apply the SAME imshow tick/spine finalization the
reproduce path applies -- so a LIVE composed figure and its reproduction agree
pixel-for-pixel.

Why the finalize call lives here (not only on reproduce): compose replays the
recorded calls as raw matplotlib, bypassing the live ``ax.imshow`` wrapper
(``_wrappers/_axes_plots.imshow_plot``) that hides imshow ticks/spines. Without
re-applying it, a *labelled* imshow (e.g. a comodulogram with ``set_xyt``) keeps
its auto ticks in the live composed figure but loses them on reproduce -- a
tile-gutter pixel divergence (NeuroVista fig02 composite). ``finalize_imshow_axes``
honours explicit ``set_xticks`` decorations, so deliberately-labelled Hz-band
ticks survive composition both ways.
"""

from typing import Any, Dict

from .._recorder import FigureRecord
from .._utils._grid import grid_id
from .._wrappers import RecordingAxes


def _replay_axes_record_mm(
    mpl_ax,
    ax_record,
    fig_record: FigureRecord,
    idx: int,
    spec: Dict[str, Any],
) -> None:
    """Replay axes record for mm-based composition."""
    from .._reproducer._core import _replay_call

    result_cache: Dict[str, Any] = {}

    for call in ax_record.calls:
        result = _replay_call(mpl_ax, call, result_cache)
        if result is not None:
            result_cache[call.id] = result

    for call in ax_record.decorations:
        result = _replay_call(mpl_ax, call, result_cache)
        if result is not None:
            result_cache[call.id] = result

    # Match the reproduce path's imshow finalization (see module docstring).
    from .._reproducer._replay_axes import finalize_imshow_axes

    finalize_imshow_axes(mpl_ax, ax_record, fig_record.style)

    ax_key = f"ax_mm_{idx}"
    ax_record_copy = ax_record
    ax_record_copy.mm_position = spec
    fig_record.axes[ax_key] = ax_record_copy


def _replay_axes_record(
    target_ax: RecordingAxes,
    ax_record,
    fig_record: FigureRecord,
    row: int,
    col: int,
) -> None:
    """Replay all calls from ax_record onto target axes."""
    from .._reproducer._core import _replay_call

    mpl_ax = target_ax._ax if hasattr(target_ax, "_ax") else target_ax
    result_cache: Dict[str, Any] = {}

    for call in ax_record.calls:
        result = _replay_call(mpl_ax, call, result_cache)
        if result is not None:
            result_cache[call.id] = result

    for call in ax_record.decorations:
        result = _replay_call(mpl_ax, call, result_cache)
        if result is not None:
            result_cache[call.id] = result

    # Match the reproduce path's imshow finalization (see module docstring).
    from .._reproducer._replay_axes import finalize_imshow_axes

    finalize_imshow_axes(mpl_ax, ax_record, fig_record.style)

    ax_key = grid_id(row, col)
    fig_record.axes[ax_key] = ax_record


__all__ = ["_replay_axes_record", "_replay_axes_record_mm"]

# EOF
