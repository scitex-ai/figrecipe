#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Panel label utilities for multi-panel figures."""

import string
from typing import TYPE_CHECKING, Any, List, Optional, Tuple

if TYPE_CHECKING:
    from ._axes import RecordingAxes


def add_panel_labels(
    all_axes: List["RecordingAxes"],
    labels: Optional[List[str]],
    loc: str,
    offset: Tuple[float, float],
    fontsize: float,
    fontweight: str,
    text_color: str,
    record_callback: Any,
    **kwargs,
) -> List[Any]:
    """Add panel labels (A, B, C, D, etc.) to axes.

    Parameters
    ----------
    all_axes : list of RecordingAxes
        Flattened list of all axes.
    labels : list of str or None
        Custom labels. If None, uses uppercase letters.
    loc : str
        Location hint: 'upper left', 'upper right', 'lower left', 'lower right'.
    offset : tuple of float
        (x, y) offset in axes coordinates.
    fontsize : float
        Font size in points.
    fontweight : str
        Font weight.
    text_color : str
        Text color.
    record_callback : callable
        Callback to record panel labels info.
    **kwargs
        Additional arguments passed to ax.text().

    Returns
    -------
    list of Text
        The matplotlib Text objects created.
    """
    n_axes = len(all_axes)

    # Generate default labels if not provided
    if labels is None:
        labels = list(string.ascii_uppercase[:n_axes])
    elif len(labels) < n_axes:
        # Extend with letters if not enough labels provided
        labels = list(labels) + list(string.ascii_uppercase[len(labels) : n_axes])

    # Calculate position based on loc
    x, y, ha, va = _calculate_position(loc, offset)

    # Record panel labels
    record_callback(
        {
            "labels": labels[:n_axes],
            "loc": loc,
            "offset": offset,
            "fontsize": fontsize,
            "fontweight": fontweight,
            "color": text_color,
            "kwargs": kwargs,
        }
    )

    # Add labels to each axes
    text_objects = []
    for ax, label in zip(all_axes, labels[:n_axes]):
        text = ax.ax.text(
            x,
            y,
            label,
            transform=ax.ax.transAxes,
            fontsize=fontsize,
            fontweight=fontweight,
            color=text_color,
            ha=ha,
            va=va,
            **kwargs,
        )
        text_objects.append(text)

    return text_objects


def _calculate_position(
    loc: str, offset: Tuple[float, float]
) -> Tuple[float, float, str, str]:
    """Calculate text position and alignment based on location.

    Returns
    -------
    tuple
        (x, y, ha, va) where ha/va are horizontal/vertical alignment.
    """
    if loc == "upper left":
        x, y = offset
        ha, va = "right", "bottom"
    elif loc == "upper right":
        x, y = offset
        ha, va = "left", "bottom"
    elif loc == "lower left":
        x, y = offset[0], -offset[1] + 1.0
        ha, va = "right", "top"
    elif loc == "lower right":
        x, y = offset
        ha, va = "left", "top"
    else:
        x, y = offset
        ha, va = "right", "bottom"

    return x, y, ha, va


__all__ = ["add_panel_labels", "panel_label"]


def panel_label(
    ax: Any,
    label: str,
    loc: str = "upper left",
    offset: Tuple[float, float] = (-0.1, 1.05),
    fontsize: float = 10,
    fontweight: str = "bold",
    text_color: str = "black",
    **kwargs,
) -> Any:
    """Place a single panel label (A, B, C, etc.) on one axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to annotate.
    label : str
        The panel label text (e.g. 'A', 'B', '(1)').
    loc : str
        Location hint: 'upper left' (default), 'upper right',
        'lower left', 'lower right'.
    offset : tuple of float
        (x, y) offset in axes coordinates. Default (-0.1, 1.05).
    fontsize : float
        Font size in points (default 10).
    fontweight : str
        Font weight (default 'bold').
    text_color : str
        Text color (default 'black').
    **kwargs
        Additional arguments passed to ``ax.text()``.

    Returns
    -------
    matplotlib.text.Text
        The created text annotation.
    """
    x, y, ha, va = _calculate_position(loc, offset)
    return ax.ax.text(
        x,
        y,
        label,
        transform=ax.ax.transAxes,
        fontsize=fontsize,
        fontweight=fontweight,
        color=text_color,
        ha=ha,
        va=va,
        **kwargs,
    )

# EOF
