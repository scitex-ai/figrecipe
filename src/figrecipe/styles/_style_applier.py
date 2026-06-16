#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Style application utilities for figrecipe.

Applies mm-based styling to matplotlib axes for publication-quality figures.
"""

__all__ = [
    "apply_style_mm",
    "apply_theme_colors",
    "check_font",
    "finalize_ticks",
    "finalize_special_plots",
    "list_available_fonts",
]

from typing import Any, Dict

from matplotlib.axes import Axes

from .._utils._units import mm_to_pt
from ._finalize import finalize_special_plots, finalize_ticks
from ._fonts import check_font, list_available_fonts
from ._plot_styles import (
    apply_barplot_style,
    apply_boxplot_style,
    apply_histogram_style,
    apply_matrix_style,
    apply_pie_style,
    apply_violinplot_style,
)
from ._themes import THEME_COLORS, apply_theme_colors


def _normalize_style_keys(style: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize style keys to handle multiple naming conventions.

    Converts YAML-format keys (with behavior_ prefix) to the format expected
    by apply_style_mm. This ensures compatibility with different style sources:
    - YAML recipes: use behavior_hide_top_spine, behavior_hide_right_spine, etc.
    - Programmatic API: use hide_top_spine, hide_right_spine, etc.
    - Style objects: use various formats

    Parameters
    ----------
    style : dict
        Style dictionary with potentially mixed key formats.

    Returns
    -------
    dict
        Normalized style dictionary with consistent key names.
    """
    normalized = style.copy()

    # Map behavior_* keys to their non-prefixed equivalents
    behavior_mappings = {
        "behavior_hide_top_spine": "hide_top_spine",
        "behavior_hide_right_spine": "hide_right_spine",
        "behavior_grid": "grid",
        "behavior_auto_scale_axes": "auto_scale_axes",
        "behavior_constrained_layout": "constrained_layout",
    }

    for old_key, new_key in behavior_mappings.items():
        if old_key in normalized and new_key not in normalized:
            normalized[new_key] = normalized[old_key]

    # Map old mm-based keys to new names if needed
    mm_mappings = {
        "axes_thickness_mm": "axes_thickness_mm",  # Already correct
        "ticks_length_mm": "tick_length_mm",
        "ticks_thickness_mm": "tick_thickness_mm",
        "ticks_direction": "tick_direction",
        "ticks_n_ticks_min": "n_ticks_min",
        "ticks_n_ticks_max": "n_ticks_max",
        "lines_trace_mm": "trace_thickness_mm",
        "markers_size_mm": "marker_size_mm",
        "markers_flier_mm": "markers_flier_mm",  # Already correct
        "fonts_family": "font_family",
        "fonts_axis_label_pt": "axis_font_size_pt",
        "fonts_tick_label_pt": "tick_font_size_pt",
        "fonts_title_pt": "title_font_size_pt",
        "fonts_legend_pt": "legend_font_size_pt",
        "padding_label_pt": "label_pad_pt",
        "padding_tick_pt": "tick_pad_pt",
        "padding_title_pt": "title_pad_pt",
        "theme_mode": "theme",
        # Legend settings
        "legend_frameon": "legend_frameon",
        "legend_fancybox": "legend_fancybox",
        "legend_edgecolor": "legend_edgecolor",
        "legend_edge_mm": "legend_edge_mm",
    }

    for old_key, new_key in mm_mappings.items():
        if old_key in normalized and new_key not in normalized:
            normalized[new_key] = normalized[old_key]

    return normalized


def apply_style_mm(ax: Axes, style: Dict[str, Any]) -> float:
    """Apply publication-quality style using millimeter-based settings.

    This function applies styling to matplotlib axes using millimeter and point
    measurements for precise control over visual elements.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes to apply styling to
    style : dict
        Dictionary containing styling parameters. Supported keys:
        - 'axes_thickness_mm' (float): Spine line width in mm (default: 0.2)
        - 'trace_thickness_mm' (float): Plot line width in mm (default: 0.3)
        - 'tick_length_mm' (float): Tick mark length in mm (default: 1.0)
        - 'tick_thickness_mm' (float): Tick mark width in mm (default: 0.2)
        - 'marker_size_mm' (float): Default marker size in mm (default: 1.0)
        - 'axis_font_size_pt' (float): Axis label font size in points (default: 8)
        - 'tick_font_size_pt' (float): Tick label font size in points (default: 7)
        - 'title_font_size_pt' (float): Title font size in points (default: 9)
        - 'legend_font_size_pt' (float): Legend font size in points (default: 7)
        - 'label_pad_pt' (float): Axis label padding in points (default: 2.0)
        - 'tick_pad_pt' (float): Tick label padding in points (default: 2.0)
        - 'title_pad_pt' (float): Title padding in points (default: 4.0)
        - 'font_family' (str): Font family (default: "Arial")
        - 'n_ticks' (int): Number of ticks on each axis (default: 5)
        - 'theme' (str): Color theme "light" or "dark" (default: "light")
        - 'theme_colors' (dict): Custom theme color overrides
        - 'hide_top_spine' (bool): Hide top spine (default: True)
        - 'hide_right_spine' (bool): Hide right spine (default: True)
        - 'grid' (bool): Show grid (default: False)

    Also supports YAML-format keys (e.g., behavior_hide_top_spine, fonts_family)
    which are automatically normalized to the above formats.

    Returns
    -------
    float
        Trace line width in points, to be used with ax.plot(..., lw=trace_lw)

    Examples
    --------
    >>> fig, ax = plt.subplots()
    >>> style = {
    ...     'axes_thickness_mm': 0.2,
    ...     'trace_thickness_mm': 0.3,
    ...     'tick_length_mm': 1.0,
    ...     'axis_font_size_pt': 8,
    ...     'theme': 'light',
    ... }
    >>> trace_lw = apply_style_mm(ax, style)
    >>> ax.plot(x, y, lw=trace_lw)
    """
    import matplotlib as mpl

    # Normalize style keys to handle different naming conventions
    style = _normalize_style_keys(style)

    # Apply theme colors (dark/light mode)
    theme_section = style.get("theme", {})
    if isinstance(theme_section, dict):
        theme = theme_section.get("mode", "light")
    else:
        theme = str(theme_section) if theme_section else "light"
    theme_colors = style.get("theme_colors", None)
    apply_theme_colors(ax, theme, theme_colors)

    # Convert spine thickness from mm to points
    axes_lw_pt = mm_to_pt(style.get("axes_thickness_mm", 0.2))
    for spine in ax.spines.values():
        spine.set_linewidth(axes_lw_pt)

    # Hide spines if requested
    if style.get("hide_top_spine", True):
        ax.spines["top"].set_visible(False)
    if style.get("hide_right_spine", True):
        ax.spines["right"].set_visible(False)

    # Set matplotlib's default line width from the GENERAL/default line width
    # (lines.linewidth_mm; ~0.8mm). Ordinary lines (KDE curves, single plots)
    # that pass no lw= inherit this. The thin signal/trace width is opt-in via
    # lw="signal". Fall back to trace_thickness_mm on legacy presets.
    general_lw_mm = style.get(
        "lines_linewidth_mm", style.get("trace_thickness_mm", 0.3)
    )
    general_lw_pt = mm_to_pt(general_lw_mm)
    mpl.rcParams["lines.linewidth"] = general_lw_pt
    # Preserve the trace/signal line width for the documented return value
    # (callers use it as ax.plot(..., lw=trace_lw) for dense signal traces).
    trace_lw_pt = mm_to_pt(style.get("trace_thickness_mm", 0.3))

    # Grid line width — update both rcParams (for future gridlines) and
    # existing gridline objects (created at axes init with default linewidth)
    grid_mm = style.get("lines_grid_mm")
    if grid_mm is not None:
        grid_lw_pt = mm_to_pt(grid_mm)
        mpl.rcParams["grid.linewidth"] = grid_lw_pt
        for line in ax.get_xgridlines() + ax.get_ygridlines():
            line.set_linewidth(grid_lw_pt)

    # Convert marker size from mm to points
    marker_size_mm = style.get("marker_size_mm")
    if marker_size_mm is not None:
        marker_size_pt = mm_to_pt(marker_size_mm)
        mpl.rcParams["lines.markersize"] = marker_size_pt

    # Set boxplot flier (outlier) marker size
    flier_mm = style.get("markers_flier_mm", style.get("flier_mm"))
    if flier_mm is not None:
        flier_size_pt = mm_to_pt(flier_mm)
        mpl.rcParams["boxplot.flierprops.markersize"] = flier_size_pt

    # Set boxplot median color
    median_color = style.get("boxplot_median_color")
    if median_color is not None:
        mpl.rcParams["boxplot.medianprops.color"] = median_color

    # Apply plot-specific styles
    apply_boxplot_style(ax, style)
    apply_violinplot_style(ax, style)
    apply_barplot_style(ax, style)
    apply_histogram_style(ax, style)
    apply_pie_style(ax, style)
    apply_matrix_style(ax, style)

    # Configure tick parameters
    tick_pad_pt = style.get("tick_pad_pt", 2.0)
    tick_direction = style.get("tick_direction", "out")
    ax.tick_params(
        direction=tick_direction,
        length=mm_to_pt(style.get("tick_length_mm", 1.0)),
        width=mm_to_pt(style.get("tick_thickness_mm", 0.2)),
        pad=tick_pad_pt,
        top=False,
        right=False,
    )

    # Apply font sizes and family
    axis_fs = style.get("axis_font_size_pt", 8)
    tick_fs = style.get("tick_font_size_pt", 7)
    title_fs = style.get("title_font_size_pt", 9)
    legend_fs = style.get("legend_font_size_pt", 7)
    label_pad_pt = style.get("label_pad_pt", 2.0)
    requested_font = style.get("font_family", "Arial")
    font_family = check_font(requested_font)

    ax.xaxis.label.set_fontsize(axis_fs)
    ax.xaxis.label.set_fontfamily(font_family)
    ax.xaxis.labelpad = label_pad_pt
    ax.yaxis.label.set_fontsize(axis_fs)
    ax.yaxis.label.set_fontfamily(font_family)
    ax.yaxis.labelpad = label_pad_pt

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontsize(tick_fs)
        label.set_fontfamily(font_family)

    # Set title font, size, and padding
    ax.title.set_fontfamily(font_family)
    ax.title.set_fontsize(title_fs)
    title_pad_pt = style.get("title_pad_pt", 4.0)
    ax.set_title(ax.get_title(), pad=title_pad_pt)

    # Push every font size to rcParams so subsequent ax.set_title /
    # ax.set_xlabel / ax.set_yticklabels calls inherit the SCITEX preset.
    # Without this push, calling `ax.set_title('Foo')` AFTER the styler ran
    # creates a fresh Text artist that picks up the matplotlib defaults
    # (axes.titlesize='large' = 12pt) instead of fonts.title_pt = 8 from
    # SCITEX. The legend block below already did this for legend; replicate
    # for title / axis-label / tick-label / figure-title.
    mpl.rcParams["axes.titlesize"] = title_fs
    mpl.rcParams["axes.labelsize"] = axis_fs
    mpl.rcParams["xtick.labelsize"] = tick_fs
    mpl.rcParams["ytick.labelsize"] = tick_fs
    mpl.rcParams["figure.titlesize"] = style.get("suptitle_font_size_pt", title_fs + 1)

    # Push DPI defaults so plain mpl ops outside a fg.subplots() chain
    # also follow the preset. Keys come from to_subplots_kwargs():
    #   "dpi"          = display_dpi (inline, default 100)
    #   "savefig_dpi"  = output_dpi  (saved figures, default 300)
    mpl.rcParams["figure.dpi"] = style.get("dpi", 100)
    mpl.rcParams["savefig.dpi"] = style.get("savefig_dpi", 300)

    # Set legend font size and background via rcParams
    mpl.rcParams["legend.fontsize"] = legend_fs
    mpl.rcParams["legend.title_fontsize"] = legend_fs

    # Set legend colors from theme
    theme_section = style.get("theme", {})
    if isinstance(theme_section, dict):
        theme = theme_section.get("mode", "light")
    else:
        theme = str(theme_section) if theme_section else "light"
    theme_colors = style.get("theme_colors", None)
    if theme_colors:
        legend_bg = theme_colors.get("legend_bg", theme_colors.get("axes_bg", "white"))
        text_color = theme_colors.get("text", "black")
        spine_color = theme_colors.get("spine", "black")
    else:
        theme_dict = THEME_COLORS.get(theme, THEME_COLORS["light"])
        legend_bg = theme_dict.get("legend_bg", "white")
        text_color = theme_dict.get("text", "black")
        spine_color = theme_dict.get("spine", "black")

    # Handle transparent backgrounds
    if str(legend_bg).lower() in ("none", "transparent"):
        mpl.rcParams["legend.facecolor"] = "none"
        mpl.rcParams["legend.framealpha"] = 0
    else:
        mpl.rcParams["legend.facecolor"] = legend_bg
        mpl.rcParams["legend.framealpha"] = 1.0

    # Set legend frame and edge settings
    legend_frameon = style.get("legend_frameon", True)
    legend_fancybox = style.get("legend_fancybox", False)
    legend_edgecolor = style.get("legend_edgecolor", spine_color)
    legend_edge_mm = style.get("legend_edge_mm", 0.2)

    mpl.rcParams["legend.frameon"] = legend_frameon
    mpl.rcParams["legend.fancybox"] = legend_fancybox
    mpl.rcParams["legend.edgecolor"] = (
        legend_edgecolor if legend_edgecolor else spine_color
    )
    mpl.rcParams["legend.labelcolor"] = text_color

    legend = ax.get_legend()
    if legend is not None:
        for text in legend.get_texts():
            text.set_fontsize(legend_fs)
            text.set_fontfamily(font_family)
        # Apply frame linewidth from legend_edge_mm
        if legend_frameon and legend_edge_mm:
            frame = legend.get_frame()
            frame.set_linewidth(legend_edge_mm * 72 / 25.4)  # mm to points

    # Configure grid
    if style.get("grid", False):
        grid_kw = {"alpha": 0.3}
        grid_mm = style.get("lines_grid_mm")
        if grid_mm is not None:
            grid_kw["linewidth"] = mm_to_pt(grid_mm)
        ax.grid(True, **grid_kw)
    else:
        ax.grid(False)

    # Configure number of ticks (deferred to finalize_ticks)
    n_ticks_min = style.get("n_ticks_min")
    n_ticks_max = style.get("n_ticks_max")
    if n_ticks_min is not None or n_ticks_max is not None:
        ax._figrecipe_n_ticks_min = n_ticks_min or 3
        ax._figrecipe_n_ticks_max = n_ticks_max or 4

    # Apply color palette to both rcParams and this specific axes
    color_palette = style.get("color_palette")
    if color_palette is not None:
        normalized_palette = []
        for c in color_palette:
            if isinstance(c, (list, tuple)) and len(c) >= 3:
                if all(v <= 1.0 for v in c):
                    normalized_palette.append(tuple(c))
                else:
                    normalized_palette.append(tuple(v / 255.0 for v in c))
            else:
                normalized_palette.append(c)
        mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=normalized_palette)
        ax.set_prop_cycle(color=normalized_palette)

    # Store style in axes for reference
    if not hasattr(ax, "_figrecipe_style"):
        ax._figrecipe_style = {}
    ax._figrecipe_style.update(style)

    return trace_lw_pt


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import numpy as np

    print("Testing style application...")

    fig, ax = plt.subplots(figsize=(4, 3))

    style = {
        "axes_thickness_mm": 0.2,
        "trace_thickness_mm": 0.3,
        "tick_length_mm": 1.0,
        "tick_thickness_mm": 0.2,
        "axis_font_size_pt": 8,
        "tick_font_size_pt": 7,
        "theme": "light",
    }

    trace_lw = apply_style_mm(ax, style)

    x = np.linspace(0, 2 * np.pi, 100)
    ax.plot(x, np.sin(x), lw=trace_lw)
    ax.set_xlabel("X axis")
    ax.set_ylabel("Y axis")
    ax.set_title("Test Plot")

    plt.savefig("/tmp/test_style.png", dpi=300, bbox_inches="tight")
    print("Saved to /tmp/test_style.png")
    plt.close()

# EOF
