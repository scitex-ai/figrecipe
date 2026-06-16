#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper functions for the figure editor.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def get_form_values_from_style(style: Dict[str, Any]) -> Dict[str, Any]:
    """Extract form field values from a style dictionary.

    Maps style dictionary values to HTML form input IDs.

    Parameters
    ----------
    style : dict
        Style configuration dictionary

    Returns
    -------
    dict
        Mapping of form input IDs to values
    """
    values = {}

    # Axes dimensions
    if "axes" in style:
        values["axes_width_mm"] = style["axes"].get("width_mm", 80)
        values["axes_height_mm"] = style["axes"].get("height_mm", 55)
        values["axes_thickness_mm"] = style["axes"].get("thickness_mm", 0.2)

    # Margins
    if "margins" in style:
        values["margins_left_mm"] = style["margins"].get("left_mm", 12)
        values["margins_right_mm"] = style["margins"].get("right_mm", 3)
        values["margins_bottom_mm"] = style["margins"].get("bottom_mm", 10)
        values["margins_top_mm"] = style["margins"].get("top_mm", 3)

    # Spacing
    if "spacing" in style:
        values["spacing_horizontal_mm"] = style["spacing"].get("horizontal_mm", 8)
        values["spacing_vertical_mm"] = style["spacing"].get("vertical_mm", 8)

    # Fonts
    if "fonts" in style:
        values["fonts_family"] = style["fonts"].get("family", "DejaVu Sans")
        values["fonts_axis_label_pt"] = style["fonts"].get("axis_label_pt", 7)
        values["fonts_tick_label_pt"] = style["fonts"].get("tick_label_pt", 6)
        values["fonts_title_pt"] = style["fonts"].get("title_pt", 8)
        values["fonts_legend_pt"] = style["fonts"].get("legend_pt", 6)

    # Ticks
    if "ticks" in style:
        values["ticks_length_mm"] = style["ticks"].get("length_mm", 1.0)
        values["ticks_thickness_mm"] = style["ticks"].get("thickness_mm", 0.2)
        values["ticks_direction"] = style["ticks"].get("direction", "out")

    # Lines
    if "lines" in style:
        values["lines_trace_mm"] = style["lines"].get("trace_mm", 0.2)

    # Markers
    if "markers" in style:
        values["markers_size_mm"] = style["markers"].get("size_mm", 0.8)

    # Output
    if "output" in style:
        values["output_dpi"] = style["output"].get("dpi", 300)

    # Behavior - spine visibility for all four sides
    if "behavior" in style:
        values["behavior_hide_top_spine"] = style["behavior"].get(
            "hide_top_spine", True
        )
        values["behavior_hide_right_spine"] = style["behavior"].get(
            "hide_right_spine", True
        )
        values["behavior_hide_bottom_spine"] = style["behavior"].get(
            "hide_bottom_spine", False
        )
        values["behavior_hide_left_spine"] = style["behavior"].get(
            "hide_left_spine", False
        )
        values["behavior_grid"] = style["behavior"].get("grid", False)

    # Legend
    if "legend" in style:
        values["legend_frameon"] = style["legend"].get("frameon", True)

    return values


def _reset_to_light_mode(fig) -> None:
    """Reset figure text/spine colors to light mode defaults.

    Undoes apply_dark_mode mutations so text is visible on light canvas.
    """
    import matplotlib as mpl

    txt = "black"
    for key in ("text.color", "axes.labelcolor", "xtick.color", "ytick.color"):
        mpl.rcParams[key] = txt
    fig.patch.set_facecolor("white")
    for attr in ("_suptitle", "_supxlabel", "_supylabel"):
        obj = getattr(fig, attr, None)
        if obj is not None:
            obj.set_color(txt)
    for ax in fig.get_axes():
        ax.set_facecolor("white")
        ax.xaxis.label.set_color(txt)
        ax.yaxis.label.set_color(txt)
        ax.title.set_color(txt)
        ax.tick_params(colors=txt, which="both")
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color(txt)
        for spine in ax.spines.values():
            spine.set_color(txt)
        for text in ax.texts:
            text.set_color(txt)
        legend = ax.get_legend()
        if legend is not None:
            legend.get_frame().set_facecolor("white")
            legend.get_frame().set_edgecolor(txt)
            for t in legend.get_texts():
                t.set_color(txt)


def render_with_overrides(
    fig,
    overrides: Optional[Dict[str, Any]],
    dark_mode: bool = False,
    dpi: Optional[int] = None,
):
    """
    Re-render figure with overrides applied directly.

    Applies style overrides directly to the existing figure for reliable rendering.

    ``dpi`` sets the preview render resolution. Pass the editor canvas's display
    DPI so the returned image's pixel size equals the canvas's mm grid (a 180 mm
    figure then lands exactly on the 180 mm ruler mark). When given, it is
    remembered on the figure so every later edit re-render (axis/annotation/...
    handlers that don't pass dpi) stays the same size; when omitted, the
    remembered value is reused, falling back to 150. The bbox coordinates are
    extracted at the same dpi, so element selection stays aligned.
    """
    import base64
    import io
    import warnings

    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from PIL import Image

    from ._bbox import extract_bboxes

    # Use the underlying matplotlib Figure for canvas/render to avoid
    # RecordingFigure.__getattr__ issues with matplotlib internals (dpi etc.)
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig

    # Resolve the render DPI: an explicit dpi (from the canvas entry points) is
    # remembered on the figure so subsequent edit re-renders that omit it keep
    # the same pixel size; otherwise reuse the remembered value (default 150).
    if dpi is None:
        dpi = int(getattr(mpl_fig, "_editor_preview_dpi", 150))
    else:
        dpi = int(dpi)
        mpl_fig._editor_preview_dpi = dpi

    fig_width, fig_height = fig.get_size_inches()
    pixel_width = fig_width * dpi
    pixel_height = fig_height * dpi

    # Sanity check: prevent enormous figures (max 10000x10000 pixels)
    MAX_PIXELS = 10000
    if pixel_width > MAX_PIXELS or pixel_height > MAX_PIXELS:
        fig.set_size_inches(
            min(fig_width, MAX_PIXELS / dpi), min(fig_height, MAX_PIXELS / dpi)
        )

    # Switch to Agg backend to avoid Tkinter thread issues
    mpl_fig.set_canvas(FigureCanvasAgg(mpl_fig))

    # Disable constrained_layout if present (can cause rendering issues)
    layout_engine = fig.get_layout_engine()
    if layout_engine is not None and hasattr(layout_engine, "__class__"):
        layout_name = layout_engine.__class__.__name__
        if "Constrained" in layout_name:
            fig.set_layout_engine("none")

    # Set global font family via rcParams to catch any text matplotlib creates
    if overrides:
        import matplotlib as mpl

        from ..styles._fonts import check_font

        font_fam = overrides.get("fonts_family", overrides.get("font_family"))
        if font_fam:
            mpl.rcParams["font.family"] = "sans-serif"
            mpl.rcParams["font.sans-serif"] = [check_font(font_fam)]

    # Apply overrides directly to existing figure
    # Skip style overrides for diagram figures — diagrams have their own
    # layout/styling that would be corrupted by regular figure style settings
    is_diagram = getattr(fig, "_figrecipe_diagram", None) is not None
    if not is_diagram:
        record = fig.record if hasattr(fig, "record") else None
        if overrides:
            from ._render_overrides import apply_overrides

            apply_overrides(fig, overrides, record)

        # Apply dark/light mode to figure text and spine colors
        if dark_mode:
            from ._render_overrides import apply_dark_mode

            apply_dark_mode(fig)
        else:
            _reset_to_light_mode(fig)

    # Validate axes bounds before rendering (prevent infinite/invalid extents)
    for ax in fig.get_axes():
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        # Check for invalid limits (inf, nan, or extremely large)
        if any(not (-1e10 < v < 1e10) for v in xlim + ylim):
            ax.set_xlim(-1, 1)
            ax.set_ylim(-1, 1)

    # Save to PNG using same params as static save
    # Re-create canvas to ensure clean state (avoids matplotlib renderer issues)
    # IMPORTANT: Use mpl_fig (not RecordingFigure) for canvas/savefig to avoid
    # RecordingFigure.axes returning 2D list which breaks _tight_bbox.adjust_bbox
    original_draw = getattr(mpl_fig, "draw", None)
    mpl_fig.set_canvas(FigureCanvasAgg(mpl_fig))

    buf = io.BytesIO()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", "constrained_layout not applied")
        warnings.filterwarnings("ignore", category=UserWarning)
        try:
            # Editor preview always renders transparent — the canvas
            # provides its own background (dark/light grid theme)
            transparent = True
            render_dpi = dpi
            if is_diagram:
                fig_w, fig_h = fig.get_size_inches()
                max_dim = max(fig_w, fig_h)
                max_pixels = 1500
                if max_dim * render_dpi > max_pixels:
                    render_dpi = max(30, int(max_pixels / max_dim))
            # Make axes backgrounds transparent too (savefig transparent
            # only affects figure patch, not axes patches)
            saved_facecolors = []
            if transparent:
                for ax in mpl_fig.get_axes():
                    saved_facecolors.append((ax, ax.get_facecolor()))
                    ax.set_facecolor("none")
            save_kwargs = dict(
                format="png",
                dpi=render_dpi,
                transparent=transparent,
            )
            if is_diagram and not transparent:
                save_kwargs["facecolor"] = "white"
            mpl_fig.savefig(buf, **save_kwargs)
            # Restore axes facecolors
            for ax, fc in saved_facecolors:
                ax.set_facecolor(fc)
        except Exception as e1:
            logger.exception("[render_with_overrides] Primary render failed: %s", e1)
            buf = io.BytesIO()
            mpl_fig.set_canvas(FigureCanvasAgg(mpl_fig))
            if original_draw is not None:
                mpl_fig.draw = original_draw
            try:
                for ax in mpl_fig.get_axes():
                    ax.set_facecolor("none")
                mpl_fig.savefig(
                    buf,
                    format="png",
                    dpi=render_dpi,
                    transparent=True,
                )
            except Exception as e2:
                logger.exception(
                    "[render_with_overrides] Fallback render also failed: %s", e2
                )
                from PIL import Image as PILImage

                placeholder = PILImage.new("RGB", (400, 300), color=(240, 240, 240))
                placeholder.save(buf, format="PNG")
                buf.seek(0)
        finally:
            if original_draw is not None and hasattr(mpl_fig, "draw"):
                try:
                    mpl_fig.draw = original_draw
                except AttributeError:
                    pass
    buf.seek(0)
    png_bytes = buf.read()
    base64_str = base64.b64encode(png_bytes).decode("utf-8")

    # Get image size
    buf.seek(0)
    img = Image.open(buf)
    img_size = img.size

    # Extract bboxes using underlying mpl figure for clean canvas state
    mpl_fig.set_canvas(FigureCanvasAgg(mpl_fig))
    original_dpi = mpl_fig.dpi
    mpl_fig.set_dpi(render_dpi)
    try:
        mpl_fig.canvas.draw()
    except Exception:
        # Canvas draw failed, likely due to corrupted state - reset and retry
        mpl_fig.set_canvas(FigureCanvasAgg(mpl_fig))
        try:
            mpl_fig.canvas.draw()
        except Exception:
            pass  # If still fails, proceed with possibly stale bboxes
    bboxes = extract_bboxes(mpl_fig, img_size[0], img_size[1])
    mpl_fig.set_dpi(original_dpi)

    return base64_str, bboxes, img_size


def to_json_serializable(obj):
    """Convert numpy arrays and other non-serializable objects to JSON-safe types."""
    import numpy as np

    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    # Handle pandas Series
    elif hasattr(obj, "values") and hasattr(obj, "tolist"):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_json_serializable(item) for item in obj]
    return obj


__all__ = [
    "get_form_values_from_style",
    "render_with_overrides",
    "to_json_serializable",
]
