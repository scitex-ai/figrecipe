#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hlines: horizontal lines at y positions demo."""

import numpy as np

from figrecipe.styles import load_style


def plot_hlines(plt, rng, ax=None):
    """Horizontal-lines demo with multiple colored groups.

    Demonstrates: ax.hlines() with SCITEX color palette (each group of
    y-positions drawn from x=0 to x=1 in its own color).
    """
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.get_figure() if hasattr(ax, "get_figure") else ax.fig

    # Get SCITEX color palette
    style = load_style()
    palette = style.get("colors", {}).get("palette", [])
    colors = [tuple(v / 255.0 for v in c) for c in palette[:3]]

    groups = [("A", 0.0), ("B", 10.0), ("C", 20.0)]
    for (label, offset), color in zip(groups, colors):
        ys = np.sort(rng.uniform(0, 10, 8)) + offset
        ax.hlines(ys, 0.0, 1.0, colors=color, linewidth=1.2, id=f"hlines_{label}")

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("hlines")
    ax.set_xlim(-0.1, 1.2)
    ax.set_ylim(0, 30)
    return fig, ax


# EOF
