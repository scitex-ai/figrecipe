#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Node shape definitions using matplotlib FancyBboxPatch."""

from typing import Dict, Optional, Tuple

from matplotlib.patches import FancyBboxPatch

from ._styles_native import get_emphasis_style, resolve_font_config

# Shape configurations - boxstyle strings for FancyBboxPatch
# Note: pad and rounding_size are in axes fraction, keep them small
SHAPE_STYLES = {
    "box": "square,pad=0.003",
    "rounded": "round,pad=0.003,rounding_size=0.008",
    "stadium": "round,pad=0.003,rounding_size=0.02",  # Pill-like but controlled
    "diamond": "square,pad=0.003",
    "circle": "circle,pad=0.003",
    "codeblock": "square,pad=0.003",  # Code block (sharp corners like a terminal)
}

# Default node dimensions in axes coordinates (0-1 range)
# These are base sizes - actual size adapts to label length
NODE_WIDTH = 0.08  # Base width
NODE_HEIGHT = 0.04  # Base height
MAX_NODE_WIDTH = 0.15  # Maximum width cap


def get_shape_style(shape: str) -> str:
    """Get boxstyle string for a shape type."""
    return SHAPE_STYLES.get(shape, SHAPE_STYLES["box"])


def create_node_patch(
    x: float,
    y: float,
    label: str,
    shape: str = "box",
    emphasis: str = "normal",
    width: Optional[float] = None,
    height: Optional[float] = None,
    linewidth: float = 1.5,
) -> Tuple[FancyBboxPatch, Dict]:
    """Create a FancyBboxPatch for a diagram node.

    Parameters
    ----------
    x, y : float
        Center position in axes coordinates (0-1).
    label : str
        Node label text.
    shape : str
        Shape type: box, rounded, stadium, diamond, circle
    emphasis : str
        Emphasis level: normal, primary, success, warning, muted
    width, height : float, optional
        Override dimensions. If None, uses adaptive sizing.
    linewidth : float
        Border line width.

    Returns
    -------
    tuple
        (FancyBboxPatch, text_kwargs) where text_kwargs has position and style.
    """
    colors = get_emphasis_style(emphasis)
    boxstyle = get_shape_style(shape)
    font = resolve_font_config()

    # Use provided dimensions or compute adaptive size
    if width is not None:
        w = width
    else:
        # Adaptive width based on label length
        # Base width + character scaling
        w = max(NODE_WIDTH, len(label) * 0.008 + 0.03)
        w = min(w, MAX_NODE_WIDTH)  # Cap at max

    h = height if height is not None else NODE_HEIGHT

    # Create patch centered at (x, y)
    patch = FancyBboxPatch(
        (x - w / 2, y - h / 2),
        w,
        h,
        boxstyle=boxstyle,
        facecolor=colors["fill"],
        edgecolor=colors["stroke"],
        linewidth=linewidth,
        zorder=2,
    )

    # Text kwargs for label
    text_kwargs = {
        "x": x,
        "y": y,
        "s": label,
        "ha": "center",
        "va": "center",
        "fontsize": font["node_size"],
        "fontfamily": font["family"],
        "fontweight": font["weight"],
        "color": colors["text"],
        "zorder": 3,
    }

    return patch, text_kwargs


def estimate_node_bounds(
    label: str,
    shape: str = "box",
    width: Optional[float] = None,
    height: Optional[float] = None,
) -> Tuple[float, float]:
    """Estimate node dimensions for layout calculations.

    Parameters
    ----------
    label : str
        Node label text.
    shape : str
        Shape type.
    width, height : float, optional
        Override dimensions.

    Returns
    -------
    tuple
        (width, height) in axes coordinates.
    """
    if width is not None:
        w = width
    else:
        w = max(NODE_WIDTH, len(label) * 0.008 + 0.03)
        w = min(w, MAX_NODE_WIDTH)

    h = height if height is not None else NODE_HEIGHT

    return w, h


__all__ = [
    "SHAPE_STYLES",
    "NODE_WIDTH",
    "NODE_HEIGHT",
    "MAX_NODE_WIDTH",
    "get_shape_style",
    "create_node_patch",
    "estimate_node_bounds",
]
