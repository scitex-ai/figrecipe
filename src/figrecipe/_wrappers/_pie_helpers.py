#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pie chart helper functions for SCITEX styling."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.axes import Axes


def apply_pie_wedgeprops(kwargs: dict, pie_style: dict) -> dict:
    """Apply wedge properties to pie kwargs."""
    from .._utils._units import mm_to_pt

    edge_color = pie_style.get("edge_color", "black")
    edge_mm = pie_style.get("edge_mm", 0.2)
    edge_lw = mm_to_pt(edge_mm)

    if "wedgeprops" not in kwargs:
        kwargs["wedgeprops"] = {"edgecolor": edge_color, "linewidth": edge_lw}
    elif "edgecolor" not in kwargs.get("wedgeprops", {}):
        kwargs["wedgeprops"]["edgecolor"] = edge_color
        kwargs["wedgeprops"]["linewidth"] = edge_lw

    return kwargs


def apply_pie_autopct(kwargs: dict, pie_style: dict) -> dict:
    """Apply autopct default from style if not specified."""
    if "autopct" not in kwargs:
        autopct = pie_style.get("autopct")
        if autopct:
            kwargs["autopct"] = autopct
    return kwargs


def apply_pie_text_style(ax: "Axes", pie_style: dict, style) -> None:
    """Apply text styling to pie chart."""
    from ..styles._style_applier import check_font

    text_pt = pie_style.get("text_pt", 6)
    font_family = check_font(style.get("fonts", {}).get("family", "Arial"))

    # Get text color from rcParams for dark mode support
    import matplotlib.pyplot as mpl_plt

    text_color = mpl_plt.rcParams.get("text.color", "black")

    for text in ax.texts:
        text.set_fontsize(text_pt)
        text.set_fontfamily(font_family)
        text.set_color(text_color)


def apply_pie_axes_visibility(ax: "Axes", pie_style: dict) -> None:
    """Apply axes visibility settings for pie chart.

    Mirrors ``styles._plot_styles.apply_pie_style``, which suppresses the same
    chrome from the style layer. Keep the two in step: this copy kept blanking
    labels for two releases after that one stopped.
    """
    show_axes = pie_style.get("show_axes", False)
    if not show_axes:
        # set_xticks([]) alone clears ticks AND labels, reversibly. Adding
        # set_xticklabels([]) would pin a NullFormatter on the axis, blanking
        # every tick the author sets afterwards -- through any handle, with no
        # way to undo it.
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)


__all__ = [
    "apply_pie_wedgeprops",
    "apply_pie_autopct",
    "apply_pie_text_style",
    "apply_pie_axes_visibility",
]

# EOF
