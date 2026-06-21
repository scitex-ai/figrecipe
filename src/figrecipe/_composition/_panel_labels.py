#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Panel-label helpers for composed figures (A, B, C, ...).

Extracted from ``_compose.py`` to keep that module focused on layout/replay.
``_add_panel_labels_grid`` / ``_add_panel_labels_mm`` are the public entry
points used by ``compose``; the rest are internal (font size, label strings,
grid-axes lookup).
"""

from typing import Dict, List, Tuple, Union

from numpy.typing import NDArray

from .._wrappers import RecordingAxes


def _panel_label_fontsize() -> float:
    """Resolve the panel-label font size from the active SCITEX_STYLE.

    Default: 10pt bold (Nature-style panel labels).  Reads ``fonts.panel_label_pt``
    from SCITEX_STYLE if set; otherwise falls back to 10pt.  ``title_pt`` is
    *not* used as a fallback because panel labels (A, B, C, ...) follow a
    different convention than axis titles.
    """
    try:
        from ..presets._scitex_style import SCITEX_STYLE

        if isinstance(SCITEX_STYLE, dict):
            fonts = SCITEX_STYLE.get("fonts") or {}
            if "panel_label_pt" in fonts:
                return float(fonts["panel_label_pt"])
    except Exception:
        pass
    return 10.0


def _add_panel_labels_grid(axes, nrows: int, ncols: int, style: str) -> None:
    """Add panel labels to grid-based composition."""
    labels = _get_panel_labels(nrows * ncols, style)
    fs = _panel_label_fontsize()
    idx = 0
    for row in range(nrows):
        for col in range(ncols):
            ax = _get_axes_at(axes, row, col, nrows, ncols)
            mpl_ax = ax._ax if hasattr(ax, "_ax") else ax
            mpl_ax.text(
                -0.1,
                1.1,
                labels[idx],
                transform=mpl_ax.transAxes,
                fontsize=fs,
                fontweight="bold",
                va="top",
                ha="right",
            )
            idx += 1


def _add_panel_labels_mm(fig, sources: Dict, canvas_size_mm: Tuple, style: str) -> None:
    """Add panel labels to mm-based composition."""
    labels = _get_panel_labels(len(sources), style)
    fs = _panel_label_fontsize()
    for idx, (_, spec) in enumerate(sources.items()):
        xy_mm = spec["xy_mm"]
        x_frac = xy_mm[0] / canvas_size_mm[0]
        y_frac = 1.0 - xy_mm[1] / canvas_size_mm[1]
        fig.text(
            x_frac - 0.02,
            y_frac + 0.02,
            labels[idx],
            fontsize=fs,
            fontweight="bold",
            va="bottom",
            ha="right",
        )


def _get_panel_labels(n: int, style: str) -> List[str]:
    """Generate panel labels based on style."""
    if style == "uppercase":
        return [chr(ord("A") + i) for i in range(n)]
    elif style == "lowercase":
        return [chr(ord("a") + i) for i in range(n)]
    else:
        return [str(i + 1) for i in range(n)]


def _get_axes_at(
    axes: Union[RecordingAxes, NDArray],
    row: int,
    col: int,
    nrows: int,
    ncols: int,
) -> RecordingAxes:
    """Get axes at position, handling different array shapes."""
    if nrows == 1 and ncols == 1:
        return axes
    elif nrows == 1:
        return axes[col]
    elif ncols == 1:
        return axes[row]
    else:
        return axes[row, col]


__all__ = ["_add_panel_labels_grid", "_add_panel_labels_mm"]

# EOF
