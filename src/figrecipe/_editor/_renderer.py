#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Preview rendering with style overrides.

This module renders figure previews with user-specified style overrides
applied, enabling real-time preview updates in the GUI editor.
"""

import io
from typing import Any, Dict, Optional, Tuple

from .._utils._optional import missing_extra
from .._wrappers import RecordingFigure
from ._bbox import extract_bboxes
from ._render_overrides import apply_dark_mode, apply_overrides


def _restore_light_mode(fig) -> None:
    """Restore light mode colors to figure (undo dark mode changes)."""
    text_color = "black"

    # Figure background (transparent)
    fig.patch.set_facecolor("none")

    # Figure-level text
    if hasattr(fig, "_suptitle") and fig._suptitle is not None:
        fig._suptitle.set_color(text_color)
    if hasattr(fig, "_supxlabel") and fig._supxlabel is not None:
        fig._supxlabel.set_color(text_color)
    if hasattr(fig, "_supylabel") and fig._supylabel is not None:
        fig._supylabel.set_color(text_color)

    for ax in fig.get_axes():
        # Axes background (transparent)
        ax.set_facecolor("none")
        # Text colors
        ax.xaxis.label.set_color(text_color)
        ax.yaxis.label.set_color(text_color)
        ax.title.set_color(text_color)
        ax.tick_params(colors=text_color)
        # Spines
        for spine in ax.spines.values():
            spine.set_edgecolor(text_color)
        # Text objects (panel labels, annotations)
        for text in ax.texts:
            text.set_color(text_color)
        # Bracket lines (Line2D with clip_on=False)
        for line in ax.get_lines():
            if not line.get_clip_on():
                line.set_color(text_color)
        # Legend
        legend = ax.get_legend()
        if legend is not None:
            legend.get_frame().set_facecolor("none")
            legend.get_frame().set_edgecolor(text_color)
            for text in legend.get_texts():
                text.set_color(text_color)


def render_preview(
    fig: RecordingFigure,
    overrides: Optional[Dict[str, Any]] = None,
    dpi: int = 150,
    dark_mode: bool = False,
) -> Tuple[bytes, Dict[str, Any], Tuple[int, int]]:
    """
    Render figure preview with style overrides applied.

    Parameters
    ----------
    fig : RecordingFigure
        Figure to render.
    overrides : dict, optional
        Style overrides to apply.
    dpi : int, optional
        Render resolution (default: 150).
    dark_mode : bool, optional
        Whether to render in dark mode (default: False).

    Returns
    -------
    png_bytes : bytes
        PNG image data.
    bboxes : dict
        Element bounding boxes.
    img_size : tuple
        (width, height) in pixels.
    """
    record = fig.record if hasattr(fig, "record") else None

    if overrides:
        apply_overrides(fig, overrides, record)

    if dark_mode:
        apply_dark_mode(fig)
    else:
        _restore_light_mode(fig)

    _finalize_figure(fig)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    png_bytes = buf.read()

    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
        raise missing_extra(exc) from exc

    buf.seek(0)
    img = Image.open(buf)
    img_width, img_height = img.size

    original_dpi = fig.dpi
    fig.set_dpi(dpi)
    fig.canvas.draw()

    bboxes = extract_bboxes(fig, img_width, img_height)

    fig.set_dpi(original_dpi)

    return png_bytes, bboxes, (img_width, img_height)


def render_to_base64(
    fig: RecordingFigure,
    overrides: Optional[Dict[str, Any]] = None,
    dpi: int = 150,
    dark_mode: bool = False,
) -> Tuple[str, Dict[str, Any], Tuple[int, int]]:
    """
    Render figure preview as base64 string.

    Parameters
    ----------
    fig : RecordingFigure
        Figure to render.
    overrides : dict, optional
        Style overrides to apply.
    dpi : int, optional
        Render resolution (default: 150).
    dark_mode : bool, optional
        Whether to render in dark mode (default: False).

    Returns
    -------
    base64_str : str
        Base64-encoded PNG image.
    bboxes : dict
        Element bounding boxes.
    img_size : tuple
        (width, height) in pixels.
    """
    import base64

    png_bytes, bboxes, img_size = render_preview(fig, overrides, dpi, dark_mode)
    base64_str = base64.b64encode(png_bytes).decode("utf-8")

    return base64_str, bboxes, img_size


def render_download(
    fig: RecordingFigure,
    fmt: str = "png",
    dpi: int = 300,
    overrides: Optional[Dict[str, Any]] = None,
    dark_mode: bool = False,
) -> bytes:
    """
    Render figure for download in specified format.

    Parameters
    ----------
    fig : RecordingFigure
        Figure to render.
    fmt : str
        Output format: 'png', 'svg', 'pdf' (default: 'png').
    dpi : int
        Resolution for raster formats (default: 300).
    overrides : dict, optional
        Style overrides to apply.
    dark_mode : bool, optional
        Whether to render in dark mode.

    Returns
    -------
    bytes
        File content.
    """
    record = fig.record if hasattr(fig, "record") else None

    if overrides:
        apply_overrides(fig, overrides, record)

    if dark_mode:
        apply_dark_mode(fig)

    _finalize_figure(fig)

    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches="tight")
    buf.seek(0)

    return buf.read()


def _finalize_figure(fig: RecordingFigure) -> None:
    """Finalize ticks and special plots for all axes in the figure."""
    from ..styles._style_applier import finalize_special_plots, finalize_ticks

    style_dict = {}
    if hasattr(fig, "style") and fig.style:
        from ..styles._internal import get_style

        style_dict = get_style(fig.style)

    for ax in fig.get_axes():
        finalize_ticks(ax)
        finalize_special_plots(ax, style_dict)


__all__ = [
    "render_preview",
    "render_to_base64",
    "render_download",
]

# EOF
