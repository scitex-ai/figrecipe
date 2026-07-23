#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-01-10 (ywatanabe)"
# File: /home/ywatanabe/proj/.claude-worktree/figrecipe-feature-graph-support/src/figrecipe/_graph_presets.py

"""Graph visualization presets for common use cases.

Presets provide sensible defaults for common graph visualization scenarios.
Users can override any preset value with explicit arguments.
"""

from typing import Any, Dict

# Registry of built-in presets
_PRESETS: Dict[str, Dict[str, Any]] = {
    "default": {
        "layout": "spring",
        "node_size": 100,
        "node_color": "#3498db",
        "node_alpha": 0.8,
        "edge_width": 1.0,
        "edge_color": "gray",
        "edge_alpha": 0.4,
        "labels": False,
        "font_size": 6,
    },
    "minimal": {
        "layout": "spring",
        "node_size": 50,
        "node_color": "#2c3e50",
        "node_alpha": 0.9,
        "edge_width": 0.5,
        "edge_color": "#bdc3c7",
        "edge_alpha": 0.3,
        "labels": False,
        "font_size": 5,
    },
    "citation": {
        "layout": "spring",
        "node_size": "citations",  # Use 'citations' node attribute
        "node_color": "year",  # Use 'year' node attribute
        "node_alpha": 0.8,
        "edge_width": 0.8,
        "edge_color": "gray",
        "edge_alpha": 0.3,
        "arrows": True,
        "labels": "short_title",  # Use 'short_title' attribute
        "font_size": 5,
        "colormap": "viridis",
    },
    "dependency": {
        "layout": "hierarchical",
        "node_size": 80,
        "node_color": "#27ae60",
        "node_alpha": 0.9,
        "edge_width": 1.0,
        "edge_color": "#7f8c8d",
        "edge_alpha": 0.5,
        "arrows": True,
        "arrowsize": 12,
        "labels": True,
        "font_size": 6,
    },
    "social": {
        "layout": "spring",
        "node_size": "degree",  # Size by node degree
        "node_color": "community",  # Color by community attribute
        "node_alpha": 0.8,
        "edge_width": 0.5,
        "edge_color": "#95a5a6",
        "edge_alpha": 0.2,
        "labels": False,
        "colormap": "tab10",
    },
    "biological": {
        "layout": "kamada_kawai",
        "node_size": 60,
        "node_color": "type",  # Color by node type (protein, gene, etc.)
        "node_alpha": 0.9,
        "edge_width": "weight",
        "edge_color": "#34495e",
        "edge_alpha": 0.4,
        "labels": "name",
        "font_size": 5,
        "colormap": "Set2",
    },
    "knowledge": {
        "layout": "spring",
        "node_size": "importance",
        "node_color": "category",
        "node_alpha": 0.85,
        "edge_width": "strength",
        "edge_color": "#7f8c8d",
        "edge_alpha": 0.4,
        "labels": "label",
        "font_size": 6,
        "colormap": "tab20",
    },
}

# User-defined presets
_user_presets: Dict[str, Dict[str, Any]] = {}


def get_preset(name: str) -> Dict[str, Any]:
    """Get a preset by name.

    Parameters
    ----------
    name : str
        Preset name. Built-in presets: 'default', 'minimal', 'citation',
        'dependency', 'social', 'biological', 'knowledge'.

    Returns
    -------
    dict
        Preset configuration dictionary.

    Raises
    ------
    ValueError
        If preset name is not found.
    """
    # Check user presets first (allows overriding built-ins)
    if name in _user_presets:
        return _user_presets[name].copy()

    if name in _PRESETS:
        return _PRESETS[name].copy()

    available = list(_PRESETS.keys()) + list(_user_presets.keys())
    raise ValueError(
        f"Unknown preset '{name}'. Available presets: {', '.join(available)}"
    )


def register_preset(name: str, config: Dict[str, Any], override: bool = False) -> None:
    """Register a custom graph preset.

    Parameters
    ----------
    name : str
        Name for the new preset.
    config : dict
        Preset configuration. Keys should match graph() parameters.
    override : bool
        If True, allow overriding existing presets.

    Raises
    ------
    ValueError
        If preset already exists and override is False.

    Examples
    --------
    >>> from figrecipe._graph_presets import register_preset
    >>> register_preset('my_style', {
    ...     'layout': 'circular',
    ...     'node_color': '#e74c3c',
    ...     'node_size': 'degree',
    ...     'labels': True,
    ... })
    """
    if name in _PRESETS and not override:
        raise ValueError(
            f"Preset '{name}' is a built-in preset. Use override=True to replace."
        )
    if name in _user_presets and not override:
        raise ValueError(
            f"Preset '{name}' already exists. Use override=True to replace."
        )

    _user_presets[name] = config.copy()


def list_presets() -> Dict[str, str]:
    """List all available presets with descriptions.

    Returns
    -------
    dict
        Dictionary mapping preset names to brief descriptions.
    """
    descriptions = {
        "default": "Basic styling suitable for most graphs",
        "minimal": "Clean, minimal styling with thin edges",
        "citation": "Citation networks with year-based coloring",
        "dependency": "Hierarchical layout for DAGs and dependencies",
        "social": "Social networks with community detection",
        "biological": "Biological networks (protein interactions, etc.)",
        "knowledge": "Knowledge graphs with importance-based sizing",
    }

    result = {}
    for name in _PRESETS:
        result[name] = descriptions.get(name, "Built-in preset")

    for name in _user_presets:
        if name not in result:
            result[name] = "User-defined preset"

    return result


def unregister_preset(name: str) -> None:
    """Remove a user-defined preset.

    Parameters
    ----------
    name : str
        Name of the preset to remove.

    Raises
    ------
    ValueError
        If preset is a built-in or doesn't exist.
    """
    if name in _PRESETS:
        raise ValueError(
            f"Cannot unregister built-in preset '{name}'. Built-ins cannot be "
            f"removed; use register_preset(name, config, override=True) to "
            f"replace one."
        )

    if name not in _user_presets:
        removable = list(_user_presets.keys())
        detail = (
            f"Registered user presets: {', '.join(removable)}"
            if removable
            else "No user presets are registered."
        )
        raise ValueError(f"Preset '{name}' does not exist. {detail}")

    del _user_presets[name]


# EOF
