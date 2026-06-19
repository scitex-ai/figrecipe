#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Edge rendering using matplotlib FancyArrowPatch."""

from typing import Dict, Optional, Tuple

from matplotlib.patches import FancyArrowPatch

from ._styles_native import get_edge_style, resolve_font_config


def create_edge_arrow(
    start: Tuple[float, float],
    end: Tuple[float, float],
    style: str = "solid",
    label: Optional[str] = None,
    arrow_type: str = "normal",
    linewidth: float = 1.0,
    shrinkA: float = 0.0,
    shrinkB: float = 0.0,
    connectionstyle: str = "arc3,rad=0.0",
) -> Tuple[FancyArrowPatch, Optional[Dict]]:
    """Create a FancyArrowPatch for a diagram edge.

    Parameters
    ----------
    start : tuple
        (x, y) start position in axes coordinates.
    end : tuple
        (x, y) end position in axes coordinates.
    style : str
        Edge style: solid, dashed, dotted
    label : str, optional
        Edge label text.
    arrow_type : str
        Arrow head type: normal, none, open
    linewidth : float
        Line width.
    shrinkA, shrinkB : float
        Shrink distances from start/end nodes (in points).
    connectionstyle : str
        Matplotlib connection style string.

    Returns
    -------
    tuple
        (FancyArrowPatch, label_kwargs) where label_kwargs is None if no label.
    """
    edge_style = get_edge_style(style)

    # Arrow style based on type
    arrow_styles = {
        "normal": "-|>",
        "none": "-",
        "open": "-[",
    }
    arrowstyle = arrow_styles.get(arrow_type, "-|>")

    arrow = FancyArrowPatch(
        posA=start,
        posB=end,
        arrowstyle=arrowstyle,
        color=edge_style["color"],
        linestyle=edge_style["linestyle"],
        linewidth=linewidth,
        shrinkA=shrinkA,
        shrinkB=shrinkB,
        connectionstyle=connectionstyle,
        zorder=1,
        mutation_scale=10,
    )

    # Label kwargs if label provided
    label_kwargs = None
    if label:
        # Position label at midpoint
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2

        # Offset label slightly above the line
        offset_y = 0.015

        font = resolve_font_config()
        label_kwargs = {
            "x": mid_x,
            "y": mid_y + offset_y,
            "s": label,
            "ha": "center",
            "va": "bottom",
            "fontsize": font["edge_label_size"],
            "fontfamily": font["family"],
            "color": edge_style["color"],
            "zorder": 4,
        }

    return arrow, label_kwargs


def compute_connection_points(
    node1_pos: Tuple[float, float],
    node1_size: Tuple[float, float],
    node2_pos: Tuple[float, float],
    node2_size: Tuple[float, float],
    direction: str = "LR",
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """Compute edge connection points on node boundaries.

    Parameters
    ----------
    node1_pos : tuple
        (x, y) center of source node.
    node1_size : tuple
        (width, height) of source node.
    node2_pos : tuple
        (x, y) center of target node.
    node2_size : tuple
        (width, height) of target node.
    direction : str
        Layout direction: LR, TB, RL, BT

    Returns
    -------
    tuple
        (start_point, end_point) on node boundaries.
    """
    x1, y1 = node1_pos
    w1, h1 = node1_size
    x2, y2 = node2_pos
    w2, h2 = node2_size

    # Determine connection side based on relative positions and direction
    dx = x2 - x1
    dy = y2 - y1

    # Small padding to avoid touching the node edge
    pad = 0.005

    if direction in ("LR", "RL"):
        # Horizontal layout - prefer connecting left/right sides
        if abs(dx) > abs(dy) * 0.5:  # Mostly horizontal
            if dx > 0:
                start = (x1 + w1 / 2 + pad, y1)
                end = (x2 - w2 / 2 - pad, y2)
            else:
                start = (x1 - w1 / 2 - pad, y1)
                end = (x2 + w2 / 2 + pad, y2)
        else:  # Mostly vertical - use top/bottom
            if dy > 0:
                start = (x1, y1 + h1 / 2 + pad)
                end = (x2, y2 - h2 / 2 - pad)
            else:
                start = (x1, y1 - h1 / 2 - pad)
                end = (x2, y2 + h2 / 2 + pad)
    else:
        # Vertical layout (TB, BT) - prefer connecting top/bottom
        if abs(dy) > abs(dx) * 0.5:  # Mostly vertical
            if dy > 0:
                start = (x1, y1 + h1 / 2 + pad)
                end = (x2, y2 - h2 / 2 - pad)
            else:
                start = (x1, y1 - h1 / 2 - pad)
                end = (x2, y2 + h2 / 2 + pad)
        else:  # Mostly horizontal - use left/right
            if dx > 0:
                start = (x1 + w1 / 2 + pad, y1)
                end = (x2 - w2 / 2 - pad, y2)
            else:
                start = (x1 - w1 / 2 - pad, y1)
                end = (x2 + w2 / 2 + pad, y2)

    return start, end


def get_curved_connection_style(
    start: Tuple[float, float],
    end: Tuple[float, float],
    is_bidirectional: bool = False,
    index: int = 0,
) -> str:
    """Generate connection style for curved edges.

    Parameters
    ----------
    start, end : tuple
        Edge endpoints.
    is_bidirectional : bool
        Whether this is one of two edges between same nodes.
    index : int
        Edge index for parallel edges (0 or 1).

    Returns
    -------
    str
        Matplotlib connectionstyle string.
    """
    if is_bidirectional:
        # Curve in opposite directions for bidirectional edges
        rad = 0.15 if index == 0 else -0.15
        return f"arc3,rad={rad}"

    # Default: straight line
    return "arc3,rad=0.0"


__all__ = [
    "create_edge_arrow",
    "compute_connection_points",
    "get_curved_connection_style",
]
