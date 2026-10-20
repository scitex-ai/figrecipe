#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-01-10 (ywatanabe)"
"""Core graph visualization module for FigRecipe.

Provides publication-quality graph/network visualizations compatible with
scitex styling (40mm width, 6pt fonts) and interactive HTML export.
"""

from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np
from matplotlib.axes import Axes

from .._utils._optional import missing_extra

LAYOUTS = {
    "spring": "spring_layout",
    "circular": "circular_layout",
    "kamada_kawai": "kamada_kawai_layout",
    "shell": "shell_layout",
    "spectral": "spectral_layout",
    "random": "random_layout",
    "planar": "planar_layout",
    "spiral": "spiral_layout",
}


def _get_layout(
    G, layout: str, pos: Optional[Dict] = None, seed: int = 42, **layout_kwargs
):
    """Compute node positions using specified layout algorithm.

    Parameters
    ----------
    G : networkx.Graph
        The graph to layout.
    layout : str
        Layout algorithm name: 'spring', 'circular', 'kamada_kawai', 'shell',
        'spectral', 'random', 'planar', 'spiral', or 'hierarchical'.
    pos : dict, optional
        Pre-computed positions {node: (x, y)}. If provided, returned as-is.
    seed : int
        Random seed for reproducibility.
    **layout_kwargs
        Additional kwargs passed to the layout function.

    Returns
    -------
    dict
        Node positions {node: (x, y)}.
    """
    try:
        import networkx as nx
    except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
        raise missing_extra(exc) from exc

    if pos is not None:
        return pos

    if layout == "hierarchical":
        # For DAGs, use multipartite layout based on topological order
        if nx.is_directed_acyclic_graph(G):
            try:
                for layer, node in enumerate(nx.topological_sort(G)):
                    G.nodes[node]["subset"] = layer
                return nx.multipartite_layout(G, **layout_kwargs)
            except nx.NetworkXError:
                pass
        # Fallback to spring for non-DAGs
        return nx.spring_layout(G, seed=seed, **layout_kwargs)

    layout_func_name = LAYOUTS.get(layout, "spring_layout")
    layout_func = getattr(nx, layout_func_name)

    # Handle layouts that support seed parameter
    if layout in ("spring", "random"):
        layout_kwargs.setdefault("seed", seed)

    try:
        return layout_func(G, **layout_kwargs)
    except Exception:
        # Fallback to spring layout
        return nx.spring_layout(G, seed=seed)


def _resolve_node_attr(G, attr: Union[str, Callable, Any], default: Any = None) -> List:
    """Resolve node attribute values from name, callable, or scalar.

    Parameters
    ----------
    G : networkx.Graph
        The graph.
    attr : str, callable, or scalar
        - str: Node attribute name to look up
        - callable: Function (node, data) -> value
        - scalar: Single value for all nodes
    default : any
        Default value if attribute not found.

    Returns
    -------
    list
        List of values for each node in G.nodes() order.
    """
    if attr is None:
        return [default] * len(G.nodes())

    if callable(attr):
        return [attr(n, G.nodes[n]) for n in G.nodes()]

    if isinstance(attr, str):
        return [G.nodes[n].get(attr, default) for n in G.nodes()]

    # List/array pass-through (used for replay with pre-computed values)
    if isinstance(attr, (list, tuple, np.ndarray)):
        return list(attr)

    # Scalar value
    return [attr] * len(G.nodes())


def _resolve_edge_attr(G, attr: Union[str, Callable, Any], default: Any = None) -> List:
    """Resolve edge attribute values from name, callable, or scalar.

    Parameters
    ----------
    G : networkx.Graph
        The graph.
    attr : str, callable, or scalar
        - str: Edge attribute name to look up
        - callable: Function (u, v, data) -> value
        - scalar: Single value for all edges
    default : any
        Default value if attribute not found.

    Returns
    -------
    list
        List of values for each edge in G.edges() order.
    """
    if attr is None:
        return [default] * len(G.edges())

    if callable(attr):
        return [attr(u, v, G.edges[u, v]) for u, v in G.edges()]

    if isinstance(attr, str):
        return [G.edges[u, v].get(attr, default) for u, v in G.edges()]

    # List/array pass-through (used for replay with pre-computed values)
    if isinstance(attr, (list, tuple, np.ndarray)):
        return list(attr)

    # Scalar value
    return [attr] * len(G.edges())


def _validate_graph(G):
    """Validate graph type and node IDs for serialization compatibility.

    Raises
    ------
    TypeError
        If the graph type is not supported or node IDs are not serializable.
    """
    try:
        import networkx as nx
    except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
        raise missing_extra(exc) from exc

    # Check for MultiGraph/MultiDiGraph
    if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
        raise TypeError(
            "MultiGraph and MultiDiGraph are not currently supported. "
            "Use Graph or DiGraph instead, or convert with: "
            "nx.Graph(G) or nx.DiGraph(G)"
        )

    # Check node ID types for serialization
    for node in G.nodes():
        if not isinstance(node, (str, int, float)):
            raise TypeError(
                f"Node ID {node!r} (type: {type(node).__name__}) is not serializable. "
                "Node IDs must be str, int, or float for recipe serialization. "
                "Consider converting node IDs to strings."
            )


def _normalize_sizes(sizes: List, min_size: float = 20, max_size: float = 300) -> List:
    """Normalize sizes to a reasonable range."""
    sizes = np.array(sizes, dtype=float)

    # Handle NaN/None
    valid_mask = ~np.isnan(sizes)
    if not valid_mask.any():
        return [min_size] * len(sizes)

    sizes_valid = sizes[valid_mask]
    if sizes_valid.min() == sizes_valid.max():
        return [min_size + (max_size - min_size) / 2] * len(sizes)

    # Normalize to [min_size, max_size]
    normalized = min_size + (sizes - sizes_valid.min()) / (
        sizes_valid.max() - sizes_valid.min()
    ) * (max_size - min_size)
    normalized = np.nan_to_num(normalized, nan=min_size)
    return normalized.tolist()


def draw_graph(
    ax: Axes,
    G,
    *,
    layout: str = "spring",
    pos: Optional[Dict] = None,
    seed: int = 42,
    # Node styling
    node_size: Union[str, Callable, float] = 100,
    node_color: Union[str, Callable, Any] = "#3498db",
    node_alpha: float = 0.8,
    node_shape: str = "o",
    node_edgecolors: str = "white",
    node_linewidths: float = 0.34,  # 0.12mm
    # Edge styling (0.34pt = 0.12mm for SCITEX compatibility)
    edge_width: Union[str, Callable, float] = 0.34,
    edge_color: Union[str, Callable, Any] = "gray",
    edge_alpha: float = 0.5,
    edge_style: str = "solid",
    arrows: Optional[bool] = None,
    arrowsize: float = 10,
    arrowstyle: str = "-|>",
    connectionstyle: str = "arc3,rad=0.0",
    # Labels
    labels: Union[bool, Dict, str] = False,
    font_size: float = 6,
    font_color: str = "black",
    font_weight: str = "normal",
    font_family: str = "sans-serif",
    # Colormap for node_color when numeric
    colormap: str = "viridis",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    # Layout kwargs
    **layout_kwargs,
) -> Dict[str, Any]:
    """Draw a NetworkX graph on matplotlib axes.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to draw on.
    G : networkx.Graph
        The graph to draw.
    layout : str
        Layout algorithm: 'spring', 'circular', 'kamada_kawai', 'shell',
        'spectral', 'random', 'planar', 'spiral', 'hierarchical'.
    pos : dict, optional
        Pre-computed node positions {node: (x, y)}.
    seed : int
        Random seed for layout reproducibility.
    node_size : str, callable, or float
        Node sizes. Can be attribute name, callable (node, data) -> size, or scalar.
    node_color : str, callable, or any
        Node colors. Can be attribute name, callable, color name, or array.
    node_alpha : float
        Node transparency.
    node_shape : str
        Node marker shape.
    edge_width : str, callable, or float
        Edge widths. Can be attribute name, callable (u, v, data) -> width, or scalar.
    edge_color : str, callable, or any
        Edge colors.
    edge_alpha : float
        Edge transparency.
    arrows : bool, optional
        Draw arrows for directed graphs. Auto-detected if None.
    arrowsize : float
        Arrow head size for directed edges.
    labels : bool, dict, or str
        Node labels. True for node IDs, dict for custom labels, str for attribute name.
    font_size : float
        Label font size (default 6pt for scitex).
    colormap : str
        Matplotlib colormap for numeric node colors.
    **layout_kwargs
        Additional kwargs passed to layout algorithm.

    Returns
    -------
    dict
        Dictionary with 'pos', 'node_collection', 'edge_collection'.
    """
    try:
        import networkx as nx
    except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
        raise missing_extra(exc) from exc

    # Validate graph type
    _validate_graph(G)

    # Auto-detect arrows for directed graphs
    if arrows is None:
        arrows = G.is_directed()

    # Compute layout
    positions = _get_layout(G, layout, pos, seed, **layout_kwargs)

    # Resolve node sizes
    sizes = _resolve_node_attr(G, node_size, default=100)
    if isinstance(node_size, str) or callable(node_size):
        sizes = _normalize_sizes(sizes)

    # Resolve node colors
    colors = _resolve_node_attr(G, node_color, default="#3498db")

    # Check if colors are numeric (need colormap)
    color_array = None
    try:
        color_array = np.array(colors, dtype=float)
        if not np.isnan(color_array).all():
            # Numeric colors - will use colormap
            pass
        else:
            color_array = None
    except (ValueError, TypeError):
        color_array = None

    # Resolve edge widths
    widths = _resolve_edge_attr(G, edge_width, default=1.0)
    if isinstance(edge_width, str) or callable(edge_width):
        widths = _normalize_sizes(widths, min_size=0.5, max_size=3.0)

    # Resolve edge colors
    edge_colors = _resolve_edge_attr(G, edge_color, default="gray")

    # Draw edges first (so nodes appear on top)
    edge_collection = None
    if G.number_of_edges() > 0:
        edge_kwargs = {
            "width": widths,
            "edge_color": edge_colors,
            "alpha": edge_alpha,
            "style": edge_style,
            "arrows": arrows,
            "ax": ax,
        }
        # Only add arrow-specific kwargs when arrows are enabled
        # (avoids UserWarning when using LineCollection for undirected graphs)
        if arrows:
            edge_kwargs["arrowsize"] = arrowsize
            edge_kwargs["arrowstyle"] = arrowstyle
            edge_kwargs["connectionstyle"] = connectionstyle

        edge_collection = nx.draw_networkx_edges(G, positions, **edge_kwargs)

    # Draw nodes
    if color_array is not None:
        node_collection = nx.draw_networkx_nodes(
            G,
            positions,
            node_size=sizes,
            node_color=color_array,
            alpha=node_alpha,
            node_shape=node_shape,
            edgecolors=node_edgecolors,
            linewidths=node_linewidths,
            cmap=colormap,
            vmin=vmin,
            vmax=vmax,
            ax=ax,
        )
    else:
        node_collection = nx.draw_networkx_nodes(
            G,
            positions,
            node_size=sizes,
            node_color=colors,
            alpha=node_alpha,
            node_shape=node_shape,
            edgecolors=node_edgecolors,
            linewidths=node_linewidths,
            ax=ax,
        )

    # Draw labels
    label_collection = None
    if labels:
        if labels is True:
            # Use node IDs as labels
            label_dict = {n: str(n) for n in G.nodes()}
        elif isinstance(labels, str):
            # Use node attribute as labels
            label_dict = {n: str(G.nodes[n].get(labels, n)) for n in G.nodes()}
        elif isinstance(labels, dict):
            label_dict = labels
        else:
            label_dict = {n: str(n) for n in G.nodes()}

        label_collection = nx.draw_networkx_labels(
            G,
            positions,
            labels=label_dict,
            font_size=font_size,
            font_color=font_color,
            font_weight=font_weight,
            font_family=font_family,
            ax=ax,
        )

    # Remove axes frame for cleaner look
    ax.axis("off")

    return {
        "pos": positions,
        "node_collection": node_collection,
        "edge_collection": edge_collection,
        "label_collection": label_collection,
    }


def graph_to_record(
    G,
    pos: Optional[Dict] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Convert a NetworkX graph to a serializable record.

    Parameters
    ----------
    G : networkx.Graph
        The graph to serialize.
    pos : dict, optional
        Node positions to store.
    **kwargs
        Drawing parameters to store.

    Returns
    -------
    dict
        Serializable record containing graph data and styling.
    """

    # Validate graph type
    _validate_graph(G)

    nodes = []
    for n in G.nodes():
        node_data = dict(G.nodes[n])
        node_data["id"] = n
        if pos and n in pos:
            node_data["x"] = float(pos[n][0])
            node_data["y"] = float(pos[n][1])
        nodes.append(node_data)

    edges = []
    for u, v in G.edges():
        edge_data = dict(G.edges[u, v])
        edge_data["source"] = u
        edge_data["target"] = v
        edges.append(edge_data)

    record = {
        "type": "graph",
        "directed": G.is_directed(),
        "nodes": nodes,
        "edges": edges,
        "style": kwargs,
    }

    return record


def record_to_graph(record: Dict[str, Any]):
    """Reconstruct a NetworkX graph from a serialized record.

    Parameters
    ----------
    record : dict
        Record created by graph_to_record().

    Returns
    -------
    tuple
        (G, pos, style_kwargs) where G is the graph, pos is positions dict,
        and style_kwargs are the drawing parameters.

    Notes
    -----
    This function does not modify the input record.
    """
    try:
        import networkx as nx
    except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
        raise missing_extra(exc) from exc

    if record.get("directed", False):
        G = nx.DiGraph()
    else:
        G = nx.Graph()

    pos = {}
    for node_data in record.get("nodes", []):
        # Copy to avoid mutating input
        node_data = node_data.copy()
        node_id = node_data.pop("id")
        x = node_data.pop("x", None)
        y = node_data.pop("y", None)
        G.add_node(node_id, **node_data)
        if x is not None and y is not None:
            pos[node_id] = (x, y)

    for edge_data in record.get("edges", []):
        # Copy to avoid mutating input
        edge_data = edge_data.copy()
        source = edge_data.pop("source")
        target = edge_data.pop("target")
        G.add_edge(source, target, **edge_data)

    style = record.get("style", {}).copy()

    return G, pos if pos else None, style


# EOF
