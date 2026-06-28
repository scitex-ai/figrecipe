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
    title_aware: bool = False,
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
    title_aware : bool
        When True (the default-offset upper-position path), each label's y is
        lifted ABOVE its axes title at draw time so the label never renders ON
        the title. The lift is evaluated lazily because ``panel_labels=True``
        adds labels BEFORE the user sets titles (via ``set_xyt``). Has no effect
        for an axes without a title (back-compat). When False (an explicit
        user offset) the offset is honored verbatim.
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
        if title_aware:
            # Tag the label so the save-time finalizer can lift it clear of
            # the axes title. We tag (rather than position now) because
            # ``panel_labels=True`` adds labels BEFORE the user sets titles via
            # ``set_xyt``; the title height is only known at draw/save time.
            text._figrecipe_panel_label_base_y = y
        text_objects.append(text)

    return text_objects


def finalize_panel_labels(mpl_fig: Any) -> None:
    """Lift title-aware panel labels above titles for a whole figure.

    Save-time entry point: draws the figure once (so titles exist and extents
    are measurable), then adjusts every axes' panel labels. Safe to call when
    no title-aware labels are present (it is a no-op then).

    Parameters
    ----------
    mpl_fig : matplotlib.figure.Figure
        The figure whose axes' panel labels to finalize.
    """
    mpl_fig.canvas.draw()
    renderer = mpl_fig.canvas.get_renderer()
    for mpl_ax in mpl_fig.get_axes():
        clear_panel_labels_above_titles(mpl_ax, renderer)


def clear_panel_labels_above_titles(mpl_ax: Any, renderer: Any) -> None:
    """Lift title-aware panel labels above their axes title.

    Called at save/finalize time (when titles exist and a renderer is
    available) for every axes. For each panel label tagged title-aware (see
    ``add_panel_labels``), if the axes has a non-empty title the label's y is
    raised to sit ABOVE the title by the title's height in axes-fraction plus a
    small pad, so it never renders on the title. When the axes has no title the
    label keeps its original base y -- preserving the default placement
    (back-compat). Idempotent: re-running recomputes from the stored base y.

    Parameters
    ----------
    mpl_ax : matplotlib.axes.Axes
        The axes whose panel-label texts to adjust.
    renderer : RendererBase
        An active renderer for measuring title/axes extents.
    """
    pad_fraction = 0.02  # gap between title top and label, in axes-fraction

    fig = mpl_ax.figure
    title = mpl_ax.get_title()

    ax_bbox = mpl_ax.get_window_extent(renderer)
    ax_height_pt = ax_bbox.height * 72.0 / fig.dpi

    for text in list(mpl_ax.texts):
        base_y = getattr(text, "_figrecipe_panel_label_base_y", None)
        if base_y is None:
            continue

        if not title or ax_height_pt <= 0:
            # No title -> restore default placement.
            _set_label_y(text, base_y)
            continue

        title_bbox = mpl_ax.title.get_window_extent(renderer)
        title_height_pt = title_bbox.height * 72.0 / fig.dpi
        title_height_frac = title_height_pt / ax_height_pt

        target_y = max(base_y, 1.0 + title_height_frac + pad_fraction)
        _set_label_y(text, target_y)


def _set_label_y(text: Any, y: float) -> None:
    """Set a Text's y position (axes-fraction) without disturbing its x."""
    x, cur_y = text.get_position()
    if cur_y != y:
        text.set_position((x, y))


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


__all__ = [
    "add_panel_labels",
    "panel_label",
    "clear_panel_labels_above_titles",
    "finalize_panel_labels",
]


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
