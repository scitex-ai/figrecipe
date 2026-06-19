#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Legend-overlap detection with loud warning + auto-fallback.

When a user calls ``ax.legend()`` with the default ``loc='best'``,
matplotlib picks the corner of the axes with the least data. That
heuristic is good but not perfect — on dense plots the chosen corner
still overlaps a line or scatter point. figrecipe's contract is "no
silent overlap", so we:

1. Compute the legend's axes-relative bounding box.
2. Compute the bounding box of every data artist (lines, collections,
   patches) on the same axes.
3. If the legend bbox intersects any data artist bbox, log a LOUD
   :class:`UserWarning` that NAMES the overlapping artist (using its
   recorder ``id=`` when available, falling back to its label).
4. Auto-fallback: re-place the legend at ``outer right`` (the
   figrecipe convention) by re-invoking ``ax.legend`` with
   ``bbox_to_anchor=(1.02, 0.5)`` and ``loc='center left'``.
5. Record the final position on the ``FigureRecord`` for
   reproducibility.

If ``policy='strict'`` we raise :class:`OverlapError` instead of
falling back.
"""

from __future__ import annotations

import warnings
from typing import List, Optional, Tuple

from ._errors import OverlapError
from ._report import LegendOverlapReport

FALLBACK_LOC = "center left"
FALLBACK_BBOX = (1.02, 0.5)


def _legend_bbox_in_axes(legend, ax) -> Optional[Tuple[float, float, float, float]]:
    """Return ``(x0, y0, x1, y1)`` in *axes coords* (0..1 ranges)."""
    try:
        fig = ax.get_figure()
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bbox_disp = legend.get_window_extent(renderer)
        ax_bbox = ax.get_window_extent(renderer)
        if ax_bbox.width == 0 or ax_bbox.height == 0:
            return None
        x0 = (bbox_disp.x0 - ax_bbox.x0) / ax_bbox.width
        y0 = (bbox_disp.y0 - ax_bbox.y0) / ax_bbox.height
        x1 = (bbox_disp.x1 - ax_bbox.x0) / ax_bbox.width
        y1 = (bbox_disp.y1 - ax_bbox.y0) / ax_bbox.height
        return float(x0), float(y0), float(x1), float(y1)
    except Exception:
        return None


def _artist_bbox_in_axes(artist, ax) -> Optional[Tuple[float, float, float, float]]:
    try:
        fig = ax.get_figure()
        renderer = fig.canvas.get_renderer()
        bbox_disp = artist.get_window_extent(renderer)
        ax_bbox = ax.get_window_extent(renderer)
        if ax_bbox.width == 0 or ax_bbox.height == 0:
            return None
        return (
            float((bbox_disp.x0 - ax_bbox.x0) / ax_bbox.width),
            float((bbox_disp.y0 - ax_bbox.y0) / ax_bbox.height),
            float((bbox_disp.x1 - ax_bbox.x0) / ax_bbox.width),
            float((bbox_disp.y1 - ax_bbox.y0) / ax_bbox.height),
        )
    except Exception:
        return None


def _bbox_overlap(
    a: Tuple[float, float, float, float],
    b: Tuple[float, float, float, float],
) -> bool:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return not (ax1 < bx0 or bx1 < ax0 or ay1 < by0 or by1 < ay0)


def _data_artists(ax) -> List:
    """Return user-facing data artists (lines + collections + patches +
    images) — skipping the legend handles themselves."""
    out: List = []
    out.extend(ax.get_lines())
    out.extend(ax.collections)
    # Skip Rectangle patches that are part of the legend frame.
    for p in ax.patches:
        out.append(p)
    out.extend(ax.images)
    return out


def _artist_label(artist) -> str:
    label = ""
    try:
        label = artist.get_label() or ""
    except Exception:
        pass
    if label.startswith("_"):
        # Matplotlib hides labels starting with "_". Fall back to type.
        label = ""
    if not label:
        label = type(artist).__name__
    return label


def check_legend_overlap(
    ax,
    *,
    fig=None,
    policy: str = "warn",
) -> Optional[LegendOverlapReport]:
    """Audit ``ax``'s legend for collision with data.

    Returns ``None`` when there is no legend or no collision; otherwise a
    :class:`LegendOverlapReport` is returned (after fallback has been
    applied in non-strict mode).
    """
    legend = ax.get_legend()
    if legend is None:
        return None
    if policy == "off":
        return None

    leg_bbox = _legend_bbox_in_axes(legend, ax)
    if leg_bbox is None:
        return None

    colliding = []
    for artist in _data_artists(ax):
        bbox = _artist_bbox_in_axes(artist, ax)
        if bbox is None:
            continue
        if _bbox_overlap(leg_bbox, bbox):
            colliding.append((artist, bbox))

    if not colliding:
        return None

    names = [_artist_label(a) for a, _ in colliding]
    axes_key = _axes_key_for(ax, fig)

    if policy == "strict":
        raise OverlapError(
            f"Legend overlaps data element(s) {names} on panel {axes_key}",
            elements=names,
            axes_key=axes_key,
            kind="legend",
        )

    # warn + fallback
    warnings.warn(
        f"figrecipe: legend overlaps data element(s) {names} on panel "
        f"{axes_key}; moving legend to outside-right (figrecipe convention). "
        "Pass overlap_policy='strict' to raise instead, or "
        "overlap_policy='off' to silence.",
        UserWarning,
        stacklevel=3,
    )

    # Re-place the legend outside the axes.
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        # Older legend constructed manually; reuse texts.
        labels = [t.get_text() for t in legend.get_texts()]
        handles = list(legend.legend_handles)
    legend.remove()
    new_legend = ax.legend(
        handles,
        labels,
        loc=FALLBACK_LOC,
        bbox_to_anchor=FALLBACK_BBOX,
        borderaxespad=0.0,
    )

    return LegendOverlapReport(
        element_a="legend",
        element_b=",".join(names) if names else "data",
        axes_key=axes_key,
        severity="warn",
        legend_bbox_axes=leg_bbox,
        fallback_applied=True,
        final_loc=FALLBACK_LOC,
        final_bbox_to_anchor=FALLBACK_BBOX,
    )


def _axes_key_for(ax, fig) -> Optional[str]:
    """Best-effort axes-key resolution (matches recorder convention)."""
    if fig is None:
        return None
    mpl_fig = getattr(fig, "_fig", fig)
    try:
        axes_list = mpl_fig.get_axes()
        idx = axes_list.index(ax)
        return f"ax_{idx}"
    except (ValueError, AttributeError):
        return None


def record_legend_position(fig, report: LegendOverlapReport) -> None:
    """Stash the (possibly-fallback) legend position on the FigureRecord."""
    record = getattr(fig, "record", None) or getattr(fig, "_record", None)
    if record is None:
        return
    if not hasattr(record, "_legend_positions"):
        record._legend_positions = []
    record._legend_positions.append(
        {
            "axes_key": report.axes_key,
            "loc": report.final_loc,
            "bbox_to_anchor": report.final_bbox_to_anchor,
            "fallback_applied": report.fallback_applied,
        }
    )


__all__ = [
    "check_legend_overlap",
    "record_legend_position",
    "FALLBACK_LOC",
    "FALLBACK_BBOX",
]
