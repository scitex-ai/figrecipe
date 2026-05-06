#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug overlay for diagram element inspection.

Renders the diagram with element IDs and key parameters overlaid,
saved as ``*_debug.png`` to help users identify and adjust elements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from scitex_logging import getLogger

    logger = getLogger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from ._core import Diagram

# Visual style for debug annotations
_DEBUG_COLOR = "#CC0066"
_DEBUG_FONTSIZE = 6
_DEBUG_ZORDER = 10
_DEBUG_BBOX = dict(facecolor="white", edgecolor="none", pad=0.5, alpha=0.7)


def _label(ax: Axes, x: float, y: float, text: str, **kwargs) -> None:
    """Place a debug annotation label."""
    defaults = dict(
        ha="left",
        va="top",
        fontsize=_DEBUG_FONTSIZE,
        fontfamily="monospace",
        color=_DEBUG_COLOR,
        zorder=_DEBUG_ZORDER,
        bbox=_DEBUG_BBOX,
    )
    defaults.update(kwargs)
    ax.text(x, y, text, **defaults)


def _annotate_containers(diagram: "Diagram", ax: Axes) -> None:
    """Annotate containers with ID and dimensions."""
    for cid in diagram._containers:
        if cid not in diagram._positions:
            continue
        pos = diagram._positions[cid]
        x = pos.x_mm - pos.width_mm / 2
        y = pos.y_mm + pos.height_mm / 2

        lines = [cid]
        lines.append(
            f"({pos.x_mm:.0f},{pos.y_mm:.0f}) {pos.width_mm:.0f}x{pos.height_mm:.0f}"
        )
        _label(ax, x, y + 2, "\n".join(lines))


def _annotate_boxes(diagram: "Diagram", ax: Axes) -> None:
    """Annotate boxes with ID and key parameters."""
    for bid, box in diagram._boxes.items():
        if bid not in diagram._positions:
            continue
        pos = diagram._positions[bid]
        x = pos.x_mm - pos.width_mm / 2
        y = pos.y_mm + pos.height_mm / 2

        lines = [bid]
        params = []
        if box.shape != "rounded":
            params.append(f"shape={box.shape}")
        if box.emphasis != "normal":
            params.append(f"emphasis={box.emphasis}")
        if box.node_class:
            params.append(f"class={box.node_class}")
        if box.state:
            params.append(f"state={box.state}")
        if params:
            lines.append(" ".join(params))
        lines.append(
            f"({pos.x_mm:.0f},{pos.y_mm:.0f}) {pos.width_mm:.0f}x{pos.height_mm:.0f}"
        )
        _label(ax, x, y + 2, "\n".join(lines))


def _annotate_arrows(diagram: "Diagram", ax: Axes) -> None:
    """Annotate arrows with ID and key parameters."""
    from ._validate import compute_arrow_label_position

    for arrow in diagram._arrows:
        src_pos = diagram._positions.get(arrow.source)
        tgt_pos = diagram._positions.get(arrow.target)
        if not src_pos or not tgt_pos:
            continue

        if arrow.source_anchor == "auto" or arrow.target_anchor == "auto":
            sa, ta = diagram._auto_anchor(src_pos, tgt_pos)
        else:
            sa, ta = arrow.source_anchor, arrow.target_anchor

        start = diagram._get_anchor(src_pos, sa)
        end = diagram._get_anchor(tgt_pos, ta)
        lx, ly = compute_arrow_label_position(start, end, arrow.curve)

        aid = arrow.id or f"{arrow.source}->{arrow.target}"
        lines = [aid]
        params = []
        if arrow.style != "solid":
            params.append(f"style={arrow.style}")
        if arrow.curve:
            params.append(f"curve={arrow.curve}")
        if params:
            lines.append(" ".join(params))
        _label(ax, lx, ly + 2, "\n".join(lines), ha="center")


def _annotate_icons(diagram: "Diagram", ax: Axes) -> None:
    """Annotate icons with ID."""
    for iid in diagram._icons:
        if iid not in diagram._positions:
            continue
        pos = diagram._positions[iid]
        x = pos.x_mm - pos.width_mm / 2
        y = pos.y_mm + pos.height_mm / 2
        _label(ax, x, y + 2, iid)


def generate_debug_image(
    diagram: "Diagram",
    dpi: int = 200,
) -> "Figure":
    """Render diagram with debug overlay showing element IDs and parameters.

    Parameters
    ----------
    diagram : Diagram
        A finalized diagram (positions resolved).
    dpi : int
        Resolution for the debug image.

    Returns
    -------
    fig : matplotlib.figure.Figure
        Figure with diagram + debug annotations.
    """
    import logging

    # Suppress duplicate warnings from second render (main render already logged them)
    prev_level = logging.getLogger(diagram.__class__.__module__).level
    logging.getLogger(diagram.__class__.__module__).setLevel(logging.ERROR)
    try:
        fig, ax = diagram.render()
    finally:
        logging.getLogger(diagram.__class__.__module__).setLevel(prev_level)

    _annotate_containers(diagram, ax)
    _annotate_boxes(diagram, ax)
    _annotate_arrows(diagram, ax)
    _annotate_icons(diagram, ax)

    return fig


__all__ = ["generate_debug_image"]
