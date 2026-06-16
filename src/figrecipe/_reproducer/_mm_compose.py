#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproduce mm-based composed figures (axes keyed ``ax_mm_*``).

``plt.compose`` builds a composed figure by placing each panel sub-axes with
``fig.add_axes([l, b, w, h])`` and keys them ``ax_mm_0``, ``ax_mm_1``, … (not the
``r{row}c{col}`` grid keys). The generic grid reproducer derives its grid from
``parse_grid_id``, which returns ``None`` for ``ax_mm_*`` -> every panel collapses
to grid cell (0, 0) and only one survives (the composed figure reproduced as a
single panel, wrong size). This module rebuilds a composed recipe faithfully:
one ``add_axes`` per recorded axes at its recorded ``bbox``, then replay.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np


def is_mm_composed(record) -> bool:
    """True if the recipe is an mm-based composition (``ax_mm_*`` axes keys)."""
    keys = list(record.axes.keys())
    return bool(keys) and all(k.startswith("ax_mm_") for k in keys)


def reproduce_mm_composed(record):
    """Rebuild a composed figure: add_axes per panel at its recorded bbox.

    Returns ``(wrapped_fig, axes_list)`` mirroring ``reproduce_from_record``.
    """
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    from .._recorder import Recorder
    from .._wrappers import RecordingAxes, RecordingFigure
    from ._core import _replay_call

    # Build the figure WITHOUT pyplot: plt.figure() asks matplotlib for a GUI
    # figure manager, which under the GUI editor's Django worker thread tries to
    # load the tkinter backend and crashes ("partially initialized module
    # 'tkinter'" / "GUI outside main thread"). A bare Figure + Agg canvas is
    # headless and thread-safe (matching the render path in _editor/_helpers).
    fig = Figure(figsize=record.figsize, dpi=record.dpi)
    FigureCanvasAgg(fig)

    result_cache: Dict[str, Any] = {}
    mpl_axes: List[Any] = []

    # Sorted by the numeric ax_mm index so panels are added in record order.
    def _idx(key: str) -> int:
        try:
            return int(key.rsplit("_", 1)[1])
        except (ValueError, IndexError):
            return 0

    for ax_key in sorted(record.axes.keys(), key=_idx):
        ax_record = record.axes[ax_key]
        # Prefer ``compose_bbox``: the EXACT add_axes input plt.compose used to
        # place this panel (uncropped fraction, PRE-replay). Rebuilding with
        # add_axes(compose_bbox)+replay is the SAME construction compose ran, so
        # divider plotters (stx_scatter_hist) re-split identically and every
        # panel lands pixel-for-pixel. ``bbox`` is the POST-replay, cropped
        # position -- for a divider panel it is the shrunken main axes, so it
        # would shrink twice and shift inward. Fall back to ``bbox`` for recipes
        # written before compose_bbox existed.
        bbox = getattr(ax_record, "compose_bbox", None) or getattr(
            ax_record, "bbox", None
        )
        if not bbox or len(bbox) != 4:
            # Without a position we cannot place the panel; skip rather than
            # stack it at the default location and silently corrupt the layout.
            continue
        ax = fig.add_axes((bbox[0], bbox[1], bbox[2], bbox[3]))
        mpl_axes.append(ax)

        if record.style is not None:
            from ..styles._internal import apply_style_mm

            apply_style_mm(ax, record.style)

        # Replay exactly as live compose does (_replay_axes_record_mm): calls
        # then decorations, NO extra tick/special finalization. Live compose does
        # not finalize per-panel, so finalizing here shifted date-axis ticks and
        # marginals in composed panels away from the live render -- the residual
        # live-vs-reproduce divergence. Matching the live replay path converges
        # them (panels round-trip pixel-for-pixel).
        for call in ax_record.calls:
            result = _replay_call(ax, call, result_cache)
            if result is not None:
                result_cache[call.id] = result
        for call in ax_record.decorations:
            result = _replay_call(ax, call, result_cache)
            if result is not None:
                result_cache[call.id] = result

        if not getattr(ax_record, "visible", True):
            ax.set_visible(False)

    # Figure-level annotations (suptitle / fig.text panel labels etc.)
    if record.suptitle is not None:
        fig.suptitle(
            record.suptitle.get("text", ""), **record.suptitle.get("kwargs", {})
        )
    for txt in record.figure_texts:
        fig.text(txt["x"], txt["y"], txt.get("s", ""), **txt.get("kwargs", {}))

    recorder = Recorder()
    recorder._figure_record = record
    wrapped_axes = [
        RecordingAxes(a, recorder, position=(0, i)) for i, a in enumerate(mpl_axes)
    ]
    wrapped_fig = RecordingFigure(fig, recorder, wrapped_axes)
    if record.mm_layout is not None:
        wrapped_fig._mm_layout = record.mm_layout

    return wrapped_fig, np.array(wrapped_axes, dtype=object)


__all__ = ["is_mm_composed", "reproduce_mm_composed"]

# EOF
