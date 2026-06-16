#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert style DotDict to subplots kwargs."""

from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from ._dotdict import DotDict


def to_subplots_kwargs(style: Optional["DotDict"] = None) -> Dict[str, Any]:
    """Convert style DotDict to kwargs for ps.subplots().

    Uses YAML-compatible flattened key names as the single source of truth.
    For example, YAML `fonts.axis_label_pt` becomes `fonts_axis_label_pt`.

    Parameters
    ----------
    style : DotDict, optional
        Style configuration. If None, uses current loaded style.

    Returns
    -------
    dict
        Keyword arguments for ps.subplots() with YAML-compatible flattened keys.

    Examples
    --------
    >>> style = load_style()
    >>> kwargs = to_subplots_kwargs(style)
    >>> fig, ax = ps.subplots(**kwargs)
    """
    if style is None:
        from ._style_loader import get_style

        style = get_style()

    # YAML-compatible flattened keys (single source of truth)
    result = {
        # Axes (axes.* in YAML)
        "axes_width_mm": style.axes.width_mm,
        "axes_height_mm": style.axes.height_mm,
        "axes_thickness_mm": style.axes.thickness_mm,
        # Margins (margins.* in YAML)
        "margins_left_mm": style.margins.left_mm,
        "margins_right_mm": style.margins.right_mm,
        "margins_bottom_mm": style.margins.bottom_mm,
        "margins_top_mm": style.margins.top_mm,
        # Spacing (spacing.* in YAML)
        "spacing_horizontal_mm": style.spacing.horizontal_mm,
        "spacing_vertical_mm": style.spacing.vertical_mm,
        # Ticks (ticks.* in YAML)
        "ticks_length_mm": style.ticks.length_mm,
        "ticks_thickness_mm": style.ticks.thickness_mm,
        "ticks_direction": style.ticks.get("direction", "out"),
        "ticks_n_ticks_min": style.ticks.get("n_ticks_min", 3),
        "ticks_n_ticks_max": style.ticks.get("n_ticks_max", 4),
        # Lines (lines.* in YAML)
        "lines_trace_mm": style.lines.trace_mm,
        # General/default ordinary line width (KDE curves, single plots, …).
        # Falls back to the signal/trace width on legacy presets without it.
        "lines_linewidth_mm": style.lines.get("linewidth_mm", style.lines.trace_mm),
        # Thin width for dense signal traces (opt-in token lw="signal").
        "lines_signal_linewidth_mm": style.lines.get(
            "signal_linewidth_mm", style.lines.trace_mm
        ),
        "lines_errorbar_mm": style.lines.get("errorbar_mm", 0.12),
        "lines_errorbar_cap_mm": style.lines.get("errorbar_cap_mm", 0.8),
        "lines_grid_mm": style.lines.get("grid_mm"),
        # Markers (markers.* in YAML)
        "markers_size_mm": style.markers.size_mm,
        "markers_scatter_mm": style.markers.get("scatter_mm", style.markers.size_mm),
        "markers_flier_mm": style.markers.get("flier_mm", style.markers.size_mm),
        "markers_edge_width_mm": style.markers.get("edge_width_mm"),
        # Boxplot (boxplot.* in YAML)
        "boxplot_line_mm": style.get("boxplot", {}).get("line_mm", 0.2),
        "boxplot_whisker_mm": style.get("boxplot", {}).get("whisker_mm", 0.2),
        "boxplot_cap_mm": style.get("boxplot", {}).get("cap_mm", 0.2),
        "boxplot_median_mm": style.get("boxplot", {}).get("median_mm", 0.2),
        "boxplot_median_color": style.get("boxplot", {}).get("median_color", "black"),
        "boxplot_flier_edge_mm": style.get("boxplot", {}).get("flier_edge_mm", 0.2),
        # Violinplot (violinplot.* in YAML)
        "violinplot_line_mm": style.get("violinplot", {}).get("line_mm", 0.2),
        "violinplot_inner": style.get("violinplot", {}).get("inner", "box"),
        "violinplot_box_width_mm": style.get("violinplot", {}).get("box_width_mm", 1.5),
        "violinplot_whisker_mm": style.get("violinplot", {}).get("whisker_mm", 0.2),
        "violinplot_median_mm": style.get("violinplot", {}).get("median_mm", 0.8),
        # Barplot (barplot.* in YAML)
        "barplot_edge_mm": style.get("barplot", {}).get("edge_mm", 0.2),
        # Histogram (histogram.* in YAML)
        "histogram_edge_mm": style.get("histogram", {}).get("edge_mm", 0.2),
        # Pie chart (pie.* in YAML)
        "pie_text_pt": style.get("pie", {}).get("text_pt", 6),
        "pie_show_axes": style.get("pie", {}).get("show_axes", False),
        # Imshow (imshow.* in YAML)
        "imshow_show_axes": style.get("imshow", {}).get("show_axes", False),
        "imshow_show_labels": style.get("imshow", {}).get("show_labels", False),
        # Fonts (fonts.* in YAML)
        "fonts_family": style.fonts.family,
        "fonts_axis_label_pt": style.fonts.axis_label_pt,
        "fonts_tick_label_pt": style.fonts.tick_label_pt,
        "fonts_title_pt": style.fonts.title_pt,
        "fonts_suptitle_pt": style.fonts.suptitle_pt,
        "fonts_legend_pt": style.fonts.legend_pt,
        "fonts_annotation_pt": style.fonts.get("annotation_pt", 6),
        # Padding (padding.* in YAML)
        "padding_label_pt": style.padding.label_pt,
        "padding_tick_pt": style.padding.tick_pt,
        "padding_title_pt": style.padding.title_pt,
        # Output (output.* in YAML)
        "output_dpi": style.output.dpi,
        # Display DPI: inline notebook backend. Falls back to output_dpi
        # for backward compatibility with presets that lack display_dpi.
        "display_dpi": style.output.get("display_dpi", style.output.dpi),
        "output_transparent": style.output.get("transparent", True),
        "output_format": style.output.get("format", "pdf"),
        # Theme (theme.* in YAML)
        "theme_mode": style.theme.mode,
    }

    # Add theme colors from preset if available
    theme_mode = style.theme.mode
    if "theme" in style and theme_mode in style.theme:
        result["theme_colors"] = dict(style.theme[theme_mode])

    # Add color palette if available (skip if None for MATPLOTLIB style)
    if (
        "colors" in style
        and "palette" in style.colors
        and style.colors.palette is not None
    ):
        result["color_palette"] = list(style.colors.palette)

    # Add behavior settings (behavior.* in YAML)
    if "behavior" in style:
        behavior = style.behavior
        if hasattr(behavior, "hide_top_spine"):
            result["behavior_hide_top_spine"] = behavior.hide_top_spine
        if hasattr(behavior, "hide_right_spine"):
            result["behavior_hide_right_spine"] = behavior.hide_right_spine
        if hasattr(behavior, "grid"):
            result["behavior_grid"] = behavior.grid
        if hasattr(behavior, "auto_scale_axes"):
            result["behavior_auto_scale_axes"] = behavior.auto_scale_axes
        if hasattr(behavior, "constrained_layout"):
            result["behavior_constrained_layout"] = behavior.constrained_layout

    # Add colorbar settings (colorbar.* in YAML)
    if "colorbar" in style:
        colorbar = style.colorbar
        result["colorbar"] = {
            "auto": colorbar.get("auto", False),
            "outline_mm": colorbar.get("outline_mm", 0.2),
            "n_ticks_min": colorbar.get("n_ticks_min", 3),
            "n_ticks_max": colorbar.get("n_ticks_max", 4),
            "shrink": colorbar.get("shrink", 1.0),
            "aspect": colorbar.get("aspect", 20),
        }

    # Legacy key aliases for backwards compatibility
    result.update(_get_legacy_aliases(result))

    return result


def _get_legacy_aliases(result: Dict[str, Any]) -> Dict[str, Any]:
    """Get legacy key aliases for backwards compatibility.

    These allow existing code using old keys to still work.
    """
    return {
        "margin_left_mm": result["margins_left_mm"],
        "margin_right_mm": result["margins_right_mm"],
        "margin_bottom_mm": result["margins_bottom_mm"],
        "margin_top_mm": result["margins_top_mm"],
        "space_w_mm": result["spacing_horizontal_mm"],
        "space_h_mm": result["spacing_vertical_mm"],
        "tick_length_mm": result["ticks_length_mm"],
        "tick_thickness_mm": result["ticks_thickness_mm"],
        "n_ticks_min": result["ticks_n_ticks_min"],
        "n_ticks_max": result["ticks_n_ticks_max"],
        "trace_thickness_mm": result["lines_trace_mm"],
        "marker_size_mm": result["markers_size_mm"],
        "font_family": result["fonts_family"],
        "axis_font_size_pt": result["fonts_axis_label_pt"],
        "tick_font_size_pt": result["fonts_tick_label_pt"],
        "title_font_size_pt": result["fonts_title_pt"],
        "suptitle_font_size_pt": result["fonts_suptitle_pt"],
        "legend_font_size_pt": result["fonts_legend_pt"],
        "label_pad_pt": result["padding_label_pt"],
        "tick_pad_pt": result["padding_tick_pt"],
        "title_pad_pt": result["padding_title_pt"],
        # Figure construction uses display_dpi (inline notebook backend);
        # savefig() reads output_dpi separately. Splitting these keeps
        # publication-grade saved files while making inline previews
        # ~9x lighter.
        "dpi": result.get("display_dpi", result["output_dpi"]),
        "savefig_dpi": result["output_dpi"],
        "theme": result["theme_mode"],
        "hide_top_spine": result.get("behavior_hide_top_spine", True),
        "hide_right_spine": result.get("behavior_hide_right_spine", True),
        "grid": result.get("behavior_grid", False),
        "auto_scale_axes": result.get("behavior_auto_scale_axes", True),
        "constrained_layout": result.get("behavior_constrained_layout", False),
    }


__all__ = ["to_subplots_kwargs"]

# EOF
