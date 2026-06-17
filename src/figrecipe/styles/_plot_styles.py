#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plot-specific style application for figrecipe."""

from typing import Any, Dict

from matplotlib.axes import Axes

from .._utils._units import mm_to_pt
from ._fonts import check_font


def apply_boxplot_style(ax: Axes, style: Dict[str, Any]) -> None:
    """Apply boxplot line width styling to existing boxplot elements.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes containing boxplot elements.
    style : dict
        Style dictionary with boxplot_* keys.
    """
    from matplotlib.lines import Line2D
    from matplotlib.patches import PathPatch

    box_lw = mm_to_pt(style.get("boxplot_line_mm", 0.2))
    whisker_lw = mm_to_pt(style.get("boxplot_whisker_mm", 0.2))
    cap_lw = mm_to_pt(style.get("boxplot_cap_mm", 0.2))
    median_lw = mm_to_pt(style.get("boxplot_median_mm", 0.2))
    median_color = style.get("boxplot_median_color", "black")
    edge_color = style.get("boxplot_edge_color", "black")
    flier_edge_lw = mm_to_pt(style.get("boxplot_flier_edge_mm", 0.2))

    for child in ax.get_children():
        if isinstance(child, PathPatch):
            if child.get_edgecolor() is not None:
                child.set_linewidth(box_lw)
                child.set_edgecolor(edge_color)

        elif isinstance(child, Line2D):
            xdata = child.get_xdata()
            ydata = child.get_ydata()

            marker = child.get_marker()
            linestyle = child.get_linestyle()
            if marker and marker != "None" and linestyle in ("None", "", " "):
                child.set_markeredgewidth(flier_edge_lw)
                child.set_markeredgecolor(edge_color)
            elif len(xdata) == 2 and len(ydata) == 2:
                if ydata[0] == ydata[1]:
                    if linestyle == "-":
                        child.set_linewidth(median_lw)
                        child.set_color(median_color)
                    else:
                        child.set_linewidth(cap_lw)
                        child.set_color(edge_color)
                elif xdata[0] == xdata[1]:
                    child.set_linewidth(whisker_lw)
                    child.set_color(edge_color)


def apply_violinplot_style(ax: Axes, style: Dict[str, Any]) -> None:
    """Apply violinplot line width styling to existing violinplot elements.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes containing violinplot elements.
    style : dict
        Style dictionary with violinplot_* keys.
    """
    from matplotlib.collections import LineCollection, PolyCollection

    body_lw = mm_to_pt(style.get("violinplot_line_mm", 0.2))
    whisker_lw = mm_to_pt(style.get("violinplot_whisker_mm", 0.2))

    for child in ax.get_children():
        if isinstance(child, PolyCollection):
            child.set_linewidth(body_lw)
        elif isinstance(child, LineCollection):
            child.set_linewidth(whisker_lw)


def apply_barplot_style(ax: Axes, style: Dict[str, Any]) -> None:
    """Apply barplot edge styling to existing bar elements.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes containing bar elements.
    style : dict
        Style dictionary with barplot_* keys.
    """
    from matplotlib.patches import Rectangle

    edge_lw = mm_to_pt(style.get("barplot_edge_mm", 0.2))

    for patch in ax.patches:
        if isinstance(patch, Rectangle):
            patch.set_linewidth(edge_lw)
            patch.set_edgecolor("black")


def apply_histogram_style(ax: Axes, style: Dict[str, Any]) -> None:
    """Apply histogram edge styling to existing histogram elements.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes containing histogram elements.
    style : dict
        Style dictionary with histogram_* keys.
    """
    from matplotlib.patches import Rectangle

    edge_lw = mm_to_pt(style.get("histogram_edge_mm", 0.2))

    for patch in ax.patches:
        if isinstance(patch, Rectangle):
            patch.set_linewidth(edge_lw)
            patch.set_edgecolor("black")


def apply_pie_style(ax: Axes, style: Dict[str, Any]) -> None:
    """Apply pie chart styling to existing pie elements.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes containing pie chart elements.
    style : dict
        Style dictionary with pie_* keys.
    """
    from matplotlib.patches import Wedge

    has_pie = any(isinstance(p, Wedge) for p in ax.patches)
    if not has_pie:
        return

    text_pt = style.get("pie_text_pt", 6)
    show_axes = style.get("pie_show_axes", False)
    font_family = check_font(style.get("font_family", "Arial"))

    for text in ax.texts:
        transform = text.get_transform()
        if transform == ax.transAxes:
            x, y = text.get_position()
            if y > 1.0 or y < 0.0:
                continue
        text.set_fontsize(text_pt)
        text.set_fontfamily(font_family)

    if not show_axes:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        for spine in ax.spines.values():
            spine.set_visible(False)


def apply_imshow_axes_visibility(ax: Axes, show_axes: bool, show_labels: bool) -> None:
    """Hide imshow ticks / spines / labels per the imshow style flags.

    This is the SINGLE source of truth for imshow axis-chrome suppression.
    It is called unconditionally for ``imshow`` (by function/call name) from
    BOTH the live wrapper (``imshow_plot``) and the recipe replay handler so
    the saved figure and its reproduction suppress ticks identically. It must
    NOT carry the ``is_specgram`` (has-label) heuristic: the live wrapper
    never had it, so adding it here would desync save vs. reproduce -- exactly
    the bug where a labelled ``imshow`` reproduced with extra numeric ticks.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes containing the imshow image.
    show_axes : bool
        If False, hide ticks, tick labels, and spines.
    show_labels : bool
        If False, clear the x/y axis labels.
    """
    if not show_axes:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    if not show_labels:
        ax.set_xlabel("")
        ax.set_ylabel("")


def apply_matrix_style(ax: Axes, style: Dict[str, Any]) -> None:
    """Apply imshow/matshow/spy styling (hide axes if configured).

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes containing matrix plot elements.
    style : dict
        Style dictionary with imshow_*, matshow_*, spy_* keys.
    """
    from matplotlib.image import AxesImage

    has_image = any(isinstance(c, AxesImage) for c in ax.get_children())
    if not has_image:
        return

    # Check if this is specgram (has xlabel or ylabel)
    # Specgram typically has "Time" and "Frequency" labels
    xlabel = ax.get_xlabel()
    ylabel = ax.get_ylabel()
    is_specgram = bool(xlabel or ylabel)

    # Don't hide axes for specgram - it needs visible ticks
    if is_specgram:
        return

    apply_imshow_axes_visibility(
        ax,
        style.get("imshow_show_axes", True),
        style.get("imshow_show_labels", True),
    )


__all__ = [
    "apply_boxplot_style",
    "apply_violinplot_style",
    "apply_barplot_style",
    "apply_histogram_style",
    "apply_pie_style",
    "apply_matrix_style",
    "apply_imshow_axes_visibility",
]

# EOF
