#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Panel alignment tools for composition feature.

Provides alignment and distribution functions for multi-panel figures.
"""

from enum import Enum
from typing import List, Optional, Tuple, Union

from matplotlib.transforms import Bbox

from .._utils._grid import parse_grid_id
from .._wrappers import RecordingFigure


class AlignmentMode(Enum):
    """Alignment modes for panel positioning."""

    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    CENTER_H = "center_h"  # Horizontal center
    CENTER_V = "center_v"  # Vertical center
    AXIS_X = "axis_x"  # Align x-axes
    AXIS_Y = "axis_y"  # Align y-axes


def align_panels(
    fig: RecordingFigure,
    panels: List[Tuple[int, int]],
    mode: Union[str, AlignmentMode],
    reference: Optional[Tuple[int, int]] = None,
) -> None:
    """Align multiple panels to a reference panel.

    Parameters
    ----------
    fig : RecordingFigure
        The figure containing the panels.
    panels : list of tuple
        List of (row, col) positions to align.
    mode : str or AlignmentMode
        Alignment mode: 'left', 'right', 'top', 'bottom',
        'center_h', 'center_v', 'axis_x', 'axis_y'.
    reference : tuple, optional
        Reference panel position. If None, uses first panel.

    Examples
    --------
    >>> import figrecipe as fr
    >>> fig, axes = fr.subplots(2, 2)
    >>> # Align left column panels to left edge
    >>> fr.align_panels(fig, [(0, 0), (1, 0)], mode="left")
    """
    mode = AlignmentMode(mode) if isinstance(mode, str) else mode

    if not panels:
        return

    ref_pos = reference or panels[0]
    ref_ax = _get_mpl_axes(fig, ref_pos)
    if ref_ax is None:
        return
    ref_bbox = ref_ax.get_position()

    for pos in panels:
        if pos == ref_pos:
            continue

        ax = _get_mpl_axes(fig, pos)
        if ax is None:
            continue
        bbox = ax.get_position()
        new_bbox = _calculate_aligned_bbox(bbox, ref_bbox, mode)
        ax.set_position(new_bbox)


def distribute_panels(
    fig: RecordingFigure,
    panels: List[Tuple[int, int]],
    direction: str = "horizontal",
    spacing_mm: Optional[float] = None,
) -> None:
    """Distribute panels evenly with optional fixed spacing.

    Parameters
    ----------
    fig : RecordingFigure
        The figure containing the panels.
    panels : list of tuple
        List of (row, col) positions to distribute.
    direction : str
        'horizontal' or 'vertical'.
    spacing_mm : float, optional
        Fixed spacing in mm. If None, distribute evenly within
        current bounds.

    Examples
    --------
    >>> import figrecipe as fr
    >>> fig, axes = fr.subplots(1, 3)
    >>> # Distribute evenly
    >>> fr.distribute_panels(fig, [(0, 0), (0, 1), (0, 2)])
    >>> # With fixed 5mm spacing
    >>> fr.distribute_panels(fig, [(0, 0), (0, 1), (0, 2)], spacing_mm=5)
    """
    if len(panels) < 2:
        return

    # Sort panels by position
    if direction == "horizontal":
        sorted_panels = sorted(panels, key=lambda p: p[1])
    else:
        sorted_panels = sorted(panels, key=lambda p: p[0])

    # Get bounding boxes
    bboxes = []
    valid_panels = []
    for p in sorted_panels:
        ax = _get_mpl_axes(fig, p)
        if ax is not None:
            bboxes.append(ax.get_position())
            valid_panels.append(p)

    if len(valid_panels) < 2:
        return

    # Calculate even distribution
    if direction == "horizontal":
        _distribute_horizontal(fig, valid_panels, bboxes, spacing_mm)
    else:
        _distribute_vertical(fig, valid_panels, bboxes, spacing_mm)


def align_smart(
    fig: RecordingFigure,
    panels: Optional[List[Tuple[int, int]]] = None,
) -> None:
    """Automatically align panels in a compact grid layout.

    Works like human behavior:
    1. Detect grid structure (nrows, ncols)
    2. Place panels from top-left to bottom-right
    3. Calculate minimum rectangle to cover all content in each row/column
    4. Unify row heights and column widths
    5. Use space effectively with theme margins and spacing

    Uses margin and spacing values from the loaded SCITEX theme:
    - margins.left_mm, margins.right_mm, margins.top_mm, margins.bottom_mm
    - spacing.horizontal_mm, spacing.vertical_mm

    Parameters
    ----------
    fig : RecordingFigure
        The figure containing the panels.
    panels : list of tuple, optional
        Specific panels to align. If None, aligns all panels.

    Examples
    --------
    >>> import figrecipe as fr
    >>> fig, axes = fr.subplots(2, 2)
    >>> # ... add plots ...
    >>> fr.align_smart(fig)  # Align all panels using theme settings
    """
    from .._utils._units import mm_to_inch

    if panels is None:
        panels = [parse_grid_id(ax_key) for ax_key in fig.record.axes]
        panels = [p for p in panels if p is not None]

    if not panels:
        return

    # Get matplotlib figure
    mpl_fig = fig.fig if hasattr(fig, "fig") else fig

    # Get style from loaded theme
    try:
        from ..styles._style_loader import _STYLE_CACHE

        style = _STYLE_CACHE
    except (ImportError, AttributeError):
        style = None

    # Extract margin values from theme (with defaults)
    if style and hasattr(style, "margins"):
        margin_left = style.margins.get("left_mm", 6)
        margin_right = style.margins.get("right_mm", 1)
        margin_top = style.margins.get("top_mm", 5)
        margin_bottom = style.margins.get("bottom_mm", 5)
    else:
        margin_left = margin_right = margin_top = margin_bottom = 5

    # Extract spacing values from theme (with defaults)
    if style and hasattr(style, "spacing"):
        spacing_h_mm = style.spacing.get("horizontal_mm", 10)
        spacing_v_mm = style.spacing.get("vertical_mm", 15)
    else:
        spacing_h_mm = 10
        spacing_v_mm = 15

    # Determine grid dimensions
    max_row = max(p[0] for p in panels)
    max_col = max(p[1] for p in panels)
    nrows = max_row + 1
    ncols = max_col + 1

    # Get figure size in inches
    fig_width, fig_height = mpl_fig.get_size_inches()

    # Convert margins/spacing to figure fraction
    margin_left_frac = mm_to_inch(margin_left) / fig_width
    margin_right_frac = mm_to_inch(margin_right) / fig_width
    margin_top_frac = mm_to_inch(margin_top) / fig_height
    margin_bottom_frac = mm_to_inch(margin_bottom) / fig_height
    spacing_frac_w = mm_to_inch(spacing_h_mm) / fig_width
    spacing_frac_h = mm_to_inch(spacing_v_mm) / fig_height

    # Build grid of axes
    grid = {}
    for pos in panels:
        ax = _get_mpl_axes(fig, pos)
        if ax is not None:
            grid[pos] = ax

    # Calculate content-based widths for each column
    col_widths = []
    for c in range(ncols):
        max_width = 0
        for r in range(nrows):
            if (r, c) in grid:
                bbox = grid[(r, c)].get_position()
                max_width = max(max_width, bbox.width)
        col_widths.append(max_width if max_width > 0 else 0.2)

    # Calculate content-based heights for each row
    row_heights = []
    for r in range(nrows):
        max_height = 0
        for c in range(ncols):
            if (r, c) in grid:
                bbox = grid[(r, c)].get_position()
                max_height = max(max_height, bbox.height)
        row_heights.append(max_height if max_height > 0 else 0.15)

    # Calculate total content size
    total_content_w = sum(col_widths) + spacing_frac_w * (ncols - 1)
    total_content_h = sum(row_heights) + spacing_frac_h * (nrows - 1)

    # Available space after asymmetric margins
    avail_w = 1.0 - margin_left_frac - margin_right_frac
    avail_h = 1.0 - margin_top_frac - margin_bottom_frac

    # Scale factor to fit content in available space
    scale_w = avail_w / total_content_w if total_content_w > 0 else 1.0
    scale_h = avail_h / total_content_h if total_content_h > 0 else 1.0
    scale = min(scale_w, scale_h, 1.0)  # Don't enlarge, only shrink if needed

    # Apply scaling
    col_widths = [w * scale for w in col_widths]
    row_heights = [h * scale for h in row_heights]
    spacing_w = spacing_frac_w * scale
    spacing_h = spacing_frac_h * scale

    # Recalculate total after scaling
    total_w = sum(col_widths) + spacing_w * (ncols - 1)
    total_h = sum(row_heights) + spacing_h * (nrows - 1)

    # Position grid: left-aligned with left margin, centered vertically
    start_x = margin_left_frac + (avail_w - total_w) / 2

    # Position panels from top-left to bottom-right
    # Matplotlib y=0 is bottom, so we work from top down
    y = 1.0 - margin_top_frac - (avail_h - total_h) / 2
    for r in range(nrows):
        y -= row_heights[r]
        x = start_x
        for c in range(ncols):
            if (r, c) in grid:
                ax = grid[(r, c)]
                new_bbox = Bbox.from_bounds(x, y, col_widths[c], row_heights[r])
                ax.set_position(new_bbox)
            x += col_widths[c] + spacing_w
        y -= spacing_h


def _get_mpl_axes(fig: RecordingFigure, position: Tuple[int, int]):
    """Get matplotlib axes at position.

    Parameters
    ----------
    fig : RecordingFigure
        The figure.
    position : tuple
        (row, col) position.

    Returns
    -------
    matplotlib.axes.Axes or None
        The matplotlib axes, or None if not found.
    """
    row, col = position
    try:
        axes = fig._axes
        if isinstance(axes, list):
            if isinstance(axes[0], list):
                ax = axes[row][col]
            else:
                # 1D list for single row/column
                ax = axes[max(row, col)]
        else:
            # Numpy array
            ax = axes[row, col]

        return ax._ax if hasattr(ax, "_ax") else ax
    except (IndexError, AttributeError, KeyError, TypeError):
        return None


def _calculate_aligned_bbox(
    bbox: Bbox,
    ref_bbox: Bbox,
    mode: AlignmentMode,
) -> Bbox:
    """Calculate new bbox aligned to reference.

    Parameters
    ----------
    bbox : Bbox
        Current bounding box.
    ref_bbox : Bbox
        Reference bounding box.
    mode : AlignmentMode
        Alignment mode.

    Returns
    -------
    Bbox
        New aligned bounding box.
    """
    x0, y0 = bbox.x0, bbox.y0
    width, height = bbox.width, bbox.height

    if mode == AlignmentMode.LEFT:
        x0 = ref_bbox.x0
    elif mode == AlignmentMode.RIGHT:
        x0 = ref_bbox.x1 - width
    elif mode == AlignmentMode.TOP:
        y0 = ref_bbox.y1 - height
    elif mode == AlignmentMode.BOTTOM:
        y0 = ref_bbox.y0
    elif mode == AlignmentMode.CENTER_H:
        x0 = ref_bbox.x0 + (ref_bbox.width - width) / 2
    elif mode == AlignmentMode.CENTER_V:
        y0 = ref_bbox.y0 + (ref_bbox.height - height) / 2
    elif mode == AlignmentMode.AXIS_X:
        # Align bottom edges (x-axis position)
        y0 = ref_bbox.y0
    elif mode == AlignmentMode.AXIS_Y:
        # Align left edges (y-axis position)
        x0 = ref_bbox.x0

    return Bbox.from_bounds(x0, y0, width, height)


def _distribute_horizontal(
    fig: RecordingFigure,
    panels: List[Tuple[int, int]],
    bboxes: List[Bbox],
    spacing_mm: Optional[float],
) -> None:
    """Distribute panels horizontally.

    Parameters
    ----------
    fig : RecordingFigure
        The figure.
    panels : list of tuple
        Panel positions (sorted).
    bboxes : list of Bbox
        Current bounding boxes.
    spacing_mm : float or None
        Fixed spacing in mm, or None for even distribution.
    """
    if spacing_mm is not None:
        from .._utils._units import mm_to_inch

        fig_width = fig.fig.get_figwidth()
        spacing = mm_to_inch(spacing_mm) / fig_width
    else:
        total_width = sum(b.width for b in bboxes)
        available = bboxes[-1].x1 - bboxes[0].x0
        spacing = (
            (available - total_width) / (len(panels) - 1) if len(panels) > 1 else 0
        )

    x = bboxes[0].x0
    for panel, bbox in zip(panels, bboxes):
        ax = _get_mpl_axes(fig, panel)
        if ax is not None:
            new_bbox = Bbox.from_bounds(x, bbox.y0, bbox.width, bbox.height)
            ax.set_position(new_bbox)
        x += bbox.width + spacing


def _distribute_vertical(
    fig: RecordingFigure,
    panels: List[Tuple[int, int]],
    bboxes: List[Bbox],
    spacing_mm: Optional[float],
) -> None:
    """Distribute panels vertically.

    Parameters
    ----------
    fig : RecordingFigure
        The figure.
    panels : list of tuple
        Panel positions (sorted).
    bboxes : list of Bbox
        Current bounding boxes.
    spacing_mm : float or None
        Fixed spacing in mm, or None for even distribution.
    """
    if spacing_mm is not None:
        from .._utils._units import mm_to_inch

        fig_height = fig.fig.get_figheight()
        spacing = mm_to_inch(spacing_mm) / fig_height
    else:
        total_height = sum(b.height for b in bboxes)
        available = bboxes[-1].y1 - bboxes[0].y0
        spacing = (
            (available - total_height) / (len(panels) - 1) if len(panels) > 1 else 0
        )

    y = bboxes[0].y0
    for panel, bbox in zip(panels, bboxes):
        ax = _get_mpl_axes(fig, panel)
        if ax is not None:
            new_bbox = Bbox.from_bounds(bbox.x0, y, bbox.width, bbox.height)
            ax.set_position(new_bbox)
        y += bbox.height + spacing


__all__ = [
    "AlignmentMode",
    "align_panels",
    "distribute_panels",
    "align_smart",
]
