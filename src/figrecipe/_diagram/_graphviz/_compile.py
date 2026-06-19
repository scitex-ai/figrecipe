#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Graphviz compilation from DiagramSpec."""

from typing import Optional

from .._shared._compile_utils import _sanitize_id
from .._shared._presets import DiagramPreset, get_preset
from .._shared._schema import DiagramSpec, PaperMode


def compile_to_graphviz(
    spec: DiagramSpec, preset: Optional[DiagramPreset] = None
) -> str:
    """
    Compile DiagramSpec to Graphviz DOT format.

    Parameters
    ----------
    spec : DiagramSpec
        The semantic diagram specification.
    preset : DiagramPreset, optional
        Override preset.

    Returns
    -------
    str
        Graphviz DOT source code.
    """
    if preset is None:
        preset = get_preset(spec.type.value)

    is_publication = spec.paper.mode == PaperMode.PUBLICATION
    lines = []

    # Determine direction
    rankdir = preset.graphviz_rankdir
    if spec.paper.reading_direction == "top_to_bottom":
        rankdir = "TB"
    elif spec.paper.column == "double":
        rankdir = "TB"

    # Get spacing - publication mode uses tight spacing
    if is_publication:
        spacing = preset.spacing_map.get("tight", {})
    else:
        spacing = preset.spacing_map.get(spec.layout.layer_gap.value, {})
    ranksep = spacing.get("ranksep", preset.graphviz_ranksep)
    nodesep = spacing.get("nodesep", preset.graphviz_nodesep)

    lines.append("digraph G {")
    lines.append(f"    rankdir={rankdir};")
    lines.append(f"    ranksep={ranksep};")
    lines.append(f"    nodesep={nodesep};")
    lines.append("    splines=ortho;")  # Orthogonal edges for cleaner look
    lines.append('    node [fontname="Arial", fontsize=10];')
    lines.append('    edge [fontname="Arial", fontsize=9];')
    lines.append("")

    # Node map
    node_map = {n.id: n for n in spec.nodes}

    # Build return edges set for publication mode
    return_edge_set = set()
    for e in spec.paper.return_edges:
        if len(e) >= 2:
            return_edge_set.add((e[0], e[1]))

    # Generate subgraphs (without clusters for tighter layout in publication)
    if is_publication and spec.layout.layers:
        # In publication mode with layers, skip clusters - use rank=same instead
        for node in spec.nodes:
            lines.append(f"    {_graphviz_node(node, preset, spec.paper.emphasize)}")
    else:
        # Draft mode: use clusters for visual grouping
        cluster_idx = 0
        for group_name, group_nodes in spec.layout.groups.items():
            lines.append(f"    subgraph cluster_{cluster_idx} {{")
            lines.append(f'        label="{group_name}";')
            for node_id in group_nodes:
                if node_id in node_map:
                    node = node_map[node_id]
                    lines.append(
                        f"        {_graphviz_node(node, preset, spec.paper.emphasize)}"
                    )
            lines.append("    }")
            cluster_idx += 1

        # Standalone nodes
        grouped_nodes = set()
        for group_nodes in spec.layout.groups.values():
            grouped_nodes.update(group_nodes)

        for node in spec.nodes:
            if node.id not in grouped_nodes:
                lines.append(
                    f"    {_graphviz_node(node, preset, spec.paper.emphasize)}"
                )

    lines.append("")

    # Rank constraints from layers (CRITICAL for minimizing whitespace)
    for layer in spec.layout.layers:
        if layer:
            node_ids = "; ".join(_sanitize_id(n) for n in layer)
            lines.append(f"    {{ rank=same; {node_ids}; }}")

    lines.append("")

    # Edges - handle return edges in publication mode
    for edge in spec.edges:
        edge_key = (edge.source, edge.target)
        if is_publication and edge_key in return_edge_set:
            # Make return edges invisible in publication mode
            lines.append(f"    {_graphviz_edge_with_style(edge, invisible=True)}")
        else:
            lines.append(f"    {_graphviz_edge(edge)}")

    lines.append("}")

    return "\n".join(lines)


def _graphviz_node(node, preset: DiagramPreset, emphasize: list) -> str:
    """Generate Graphviz node definition."""
    shape = preset.graphviz_shapes.get(node.shape, "box")

    # Get emphasis style
    emphasis_key = "primary" if node.id in emphasize else node.emphasis
    style = preset.emphasis_styles.get(emphasis_key, {})

    attrs = [f'label="{node.label}"', f"shape={shape}"]

    # Collect style values (filled, rounded, etc.) - combine with comma
    styles = []
    if style.get("fill"):
        attrs.append(f'fillcolor="{style["fill"]}"')
        styles.append("filled")
    if style.get("stroke"):
        attrs.append(f'color="{style["stroke"]}"')
    if node.shape == "rounded":
        styles.append("rounded")

    # Output style once with comma-separated values
    if styles:
        attrs.append(f'style="{",".join(styles)}"')

    return f"{_sanitize_id(node.id)} [{', '.join(attrs)}];"


def _graphviz_edge(edge) -> str:
    """Generate Graphviz edge definition."""
    src = _sanitize_id(edge.source)
    tgt = _sanitize_id(edge.target)

    attrs = []
    if edge.label:
        attrs.append(f'label="{edge.label}"')
    if edge.style == "dashed":
        attrs.append("style=dashed")
    elif edge.style == "dotted":
        attrs.append("style=dotted")
    if edge.arrow == "none":
        attrs.append("arrowhead=none")

    if attrs:
        return f"{src} -> {tgt} [{', '.join(attrs)}];"
    return f"{src} -> {tgt};"


def _graphviz_edge_with_style(edge, invisible: bool = False) -> str:
    """Generate Graphviz edge with optional invisible style."""
    src = _sanitize_id(edge.source)
    tgt = _sanitize_id(edge.target)

    attrs = []
    if invisible:
        attrs.append("style=invis")
        # Invisible edges still constrain layout
        attrs.append("constraint=true")
    else:
        if edge.label:
            attrs.append(f'label="{edge.label}"')
        if edge.style == "dashed":
            attrs.append("style=dashed")
        elif edge.style == "dotted":
            attrs.append("style=dotted")
        if edge.arrow == "none":
            attrs.append("arrowhead=none")

    if attrs:
        return f"{src} -> {tgt} [{', '.join(attrs)}];"
    return f"{src} -> {tgt};"


__all__ = ["compile_to_graphviz"]
