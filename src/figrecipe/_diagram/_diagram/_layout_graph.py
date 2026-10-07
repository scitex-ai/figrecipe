#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Graph-based layout algorithms (spring, circular) for diagrams."""

from typing import Dict, List, Tuple

from ..._utils._optional import missing_extra

try:
    import scitex_logging as slogging
except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
    raise missing_extra(exc) from exc


def _spring_layout(
    box_ids: List[str],
    edges: List[Tuple[str, str]],
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> Dict[str, Tuple[float, float]]:
    """Compute spring (force-directed) layout using networkx."""
    try:
        import networkx as nx

        G = nx.DiGraph()
        G.add_nodes_from(box_ids)
        G.add_edges_from(edges)

        # Use kamada-kawai for better results
        try:
            pos = nx.kamada_kawai_layout(G)
        except Exception:
            pos = nx.spring_layout(G, seed=42)

        # Scale to bounds
        return _scale_positions(pos, x_min, x_max, y_min, y_max)

    except ImportError:
        # Fallback to flow layout
        from ._layout import _flow_layout

        try:
            from scitex_logging import getLogger

            _logger = getLogger(__name__)
        except ImportError:

            _logger = slogging.getLogger(__name__)
        _logger.warning("networkx not available, falling back to flow layout")
        return _flow_layout(box_ids, edges, "lr", x_min, x_max, y_min, y_max)


def _circular_layout(
    box_ids: List[str],
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> Dict[str, Tuple[float, float]]:
    """Compute circular layout.

    Delegates the unit-circle trigonometry to
    ``figrecipe._composition._radial.radial_positions`` (the tested p5js
    port, card figrecipe-bioinformatics-figure-beauty-20261006) so the two
    circular implementations cannot drift; the bounds mapping here
    (center + min-span radius) is this function's own contract, pinned by
    TestCircularLayoutContract.
    """
    from ..._composition._radial import radial_positions

    n = len(box_ids)
    cx = (x_min + x_max) / 2
    cy = (y_min + y_max) / 2
    radius = min(x_max - x_min, y_max - y_min) / 2 * 0.8

    unit = radial_positions(n, radius=1.0)
    positions = {}
    for i, bid in enumerate(box_ids):
        x = cx + radius * float(unit[i, 0])
        y = cy + radius * float(unit[i, 1])
        positions[bid] = (x, y)

    return positions


def _scale_positions(
    pos: Dict[str, Tuple[float, float]],
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> Dict[str, Tuple[float, float]]:
    """Scale positions to fit within bounds."""
    if not pos:
        return {}

    # Get current bounds
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    cur_x_min, cur_x_max = min(xs), max(xs)
    cur_y_min, cur_y_max = min(ys), max(ys)

    # Scale factors
    x_scale = (x_max - x_min) / (cur_x_max - cur_x_min) if cur_x_max != cur_x_min else 1
    y_scale = (y_max - y_min) / (cur_y_max - cur_y_min) if cur_y_max != cur_y_min else 1

    # Apply scaling
    scaled = {}
    for bid, (x, y) in pos.items():
        new_x = (
            x_min + (x - cur_x_min) * x_scale
            if cur_x_max != cur_x_min
            else (x_min + x_max) / 2
        )
        new_y = (
            y_min + (y - cur_y_min) * y_scale
            if cur_y_max != cur_y_min
            else (y_min + y_max) / 2
        )
        scaled[bid] = (new_x, new_y)

    return scaled
