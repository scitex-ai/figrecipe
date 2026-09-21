#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hitmap generation for interactive element selection.

This module generates color-coded images where each figure element
(line, scatter, bar, text, etc.) is rendered with a unique RGB color.
This enables precise pixel-based element detection when users click
on the figure preview.

The color encoding uses 24-bit RGB:
- First 12 elements: hand-picked visually distinct colors
- Elements 13+: HSV-based generation for deterministic uniqueness
"""

import io
from typing import Any, Dict, Optional, Tuple

from matplotlib.figure import Figure

from .._utils._optional import missing_extra

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
    raise missing_extra(exc) from exc


def generate_hitmap(
    fig: Figure,
    dpi: int = 150,
    include_text: bool = True,
    target_size: Optional[Tuple[int, int]] = None,
    bbox_inches: Optional[str] = None,
    pad_inches: float = 0.0,
) -> Tuple[Image.Image, Dict[str, Any]]:
    """
    Generate hitmap with unique colors per element.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure to generate hitmap for.
    dpi : int, optional
        Resolution for hitmap rendering (default: 150).
    include_text : bool, optional
        Whether to include text elements like labels (default: True).
    target_size : tuple of (width, height), optional
        Force hitmap to this exact pixel size to match the main render.
        Required for diagram figures where bbox_inches="tight" produces
        slightly different crops between renders due to color changes.

    Returns
    -------
    hitmap : PIL.Image.Image
        RGB image where each element has unique color.
    color_map : dict
        Mapping from element key to metadata:
        {
            'element_key': {
                'id': int,
                'type': str,  # 'line', 'scatter', 'bar', 'boxplot', 'violin', etc.
                'label': str,
                'ax_index': int,
                'rgb': [r, g, b],
            }
        }
    """
    # Import from helper modules (inside function to avoid circular imports)
    from ._hitmap._artists import (
        process_collections,
        process_figure_text,
        process_images,
        process_legend,
        process_lines,
        process_patches,
        process_text,
    )
    from ._hitmap._colors import (
        AXES_COLOR,
        BACKGROUND_COLOR,
        normalize_color,
    )
    from ._hitmap._detect import detect_plot_types
    from ._hitmap._restore import (
        restore_axes_properties,
        restore_backgrounds,
        restore_figure_text,
    )

    # Store original properties for restoration
    original_props = {}
    color_map = {}
    element_id = 1

    # Detect plot types from record
    plot_types = detect_plot_types(fig, debug=False)

    axes_list = fig.get_axes()

    # Detect diagram figures for special handling
    is_diagram = getattr(fig, "_figrecipe_diagram", None) is not None

    # Process all artists and assign colors
    for ax_idx, ax in enumerate(axes_list):
        ax_info = plot_types.get(ax_idx, {"types": set(), "call_ids": {}})

        # Process lines
        element_id = process_lines(
            ax, ax_idx, element_id, original_props, color_map, ax_info
        )

        # Process collections (scatter, fills, etc.)
        element_id = process_collections(
            ax, ax_idx, element_id, original_props, color_map, ax_info
        )

        # Process patches (bars, wedges, polygons)
        element_id = process_patches(
            ax, ax_idx, element_id, original_props, color_map, ax_info
        )

        # Process images (pass original_props to save/restore image data)
        element_id = process_images(
            ax, ax_idx, element_id, color_map, ax_info, original_props
        )

        # Process text elements
        if include_text:
            element_id = process_text(ax, ax_idx, element_id, original_props, color_map)

        # Process legend
        element_id = process_legend(ax, ax_idx, element_id, original_props, color_map)

    # Process figure-level text elements
    if include_text:
        element_id = process_figure_text(fig, element_id, original_props, color_map)

    # Set non-selectable elements to axes color
    for ax in axes_list:
        for spine in ax.spines.values():
            spine.set_color(normalize_color(AXES_COLOR))
        ax.tick_params(colors=normalize_color(AXES_COLOR))

    # Set figure background
    fig.patch.set_facecolor(normalize_color(BACKGROUND_COLOR))
    for ax in axes_list:
        ax.set_facecolor(normalize_color(BACKGROUND_COLOR))

    # Render to buffer
    # IMPORTANT: Do NOT use bbox_inches="tight" for regular figures - it causes
    # dimension changes between renders. Must match main render.
    # Exception: diagram figures NEED bbox_inches="tight" to crop whitespace,
    # matching how render_with_overrides() renders them.
    MAX_HITMAP_PIXELS = 2000  # cap per dimension to prevent hang on huge figures
    hitmap_dpi = dpi
    fig_w, fig_h = fig.get_size_inches()
    max_fig_dim = max(fig_w, fig_h)
    if is_diagram:
        max_pixels = 1500
        if max_fig_dim * hitmap_dpi > max_pixels:
            hitmap_dpi = max(30, int(max_pixels / max_fig_dim))
    else:
        # Cap DPI so estimated pixel size stays within safe bounds.
        # Protects against pathologically large images when constrained_layout
        # collapses axes to zero (e.g. quiver), causing tight bbox to expand hugely.
        if max_fig_dim * hitmap_dpi > MAX_HITMAP_PIXELS:
            hitmap_dpi = max(30, int(MAX_HITMAP_PIXELS / max_fig_dim))
    save_kwargs = dict(format="png", dpi=hitmap_dpi, facecolor=fig.get_facecolor())
    if is_diagram:
        # Use bbox_inches="tight" to match render_with_overrides() crop.
        # Color changes don't affect element positions so tight bbox is identical.
        save_kwargs["bbox_inches"] = "tight"
    elif bbox_inches is not None:
        # Caller explicitly requested a specific bbox mode (e.g. "tight" for pie/imshow)
        save_kwargs["bbox_inches"] = bbox_inches
        save_kwargs["pad_inches"] = pad_inches
    buf = io.BytesIO()
    fig.savefig(buf, **save_kwargs)
    buf.seek(0)

    # Load as PIL Image
    hitmap = Image.open(buf).convert("RGB")

    # Guard: if tight bbox expanded the image beyond safe limits (e.g. quiver with
    # collapsed constrained_layout), resize down to prevent encode hang.
    if max(hitmap.size) > MAX_HITMAP_PIXELS * 2:
        scale = (MAX_HITMAP_PIXELS * 2) / max(hitmap.size)
        new_size = (
            max(1, int(hitmap.width * scale)),
            max(1, int(hitmap.height * scale)),
        )
        hitmap = hitmap.resize(new_size, Image.NEAREST)

    # Force hitmap to match main render dimensions exactly.
    # bbox_inches="tight" recomputes the crop per render, and color changes
    # in the hitmap cause a slightly different tight bbox (typically 2-3px).
    # Use NEAREST resampling to preserve exact color-to-element mapping.
    if target_size and hitmap.size != target_size:
        import warnings

        warnings.warn(
            f"Hitmap size {hitmap.size} differs from main render {target_size}, resizing",
            UserWarning,
            stacklevel=2,
        )
        hitmap = hitmap.resize(target_size, Image.NEAREST)

    # Restore original properties
    restore_axes_properties(axes_list, original_props, include_text)
    restore_figure_text(fig, original_props, include_text)
    restore_backgrounds(fig, axes_list)

    return hitmap, color_map


def hitmap_to_base64(hitmap: Image.Image) -> str:
    """
    Convert hitmap image to base64 string.

    Parameters
    ----------
    hitmap : PIL.Image.Image
        Hitmap image.

    Returns
    -------
    str
        Base64-encoded PNG string.
    """
    import base64

    buf = io.BytesIO()
    hitmap.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


__all__ = [
    "generate_hitmap",
    "hitmap_to_base64",
]

# EOF
