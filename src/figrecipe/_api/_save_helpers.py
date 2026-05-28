#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Helper functions for save operations (extracted for modularity)."""

from pathlib import Path
from typing import Optional

from .._utils._grid import parse_grid_id


def _crop_to_axes_size(
    fig,
    image_path: Path,
    mm_layout: dict,
    dpi: int,
) -> Optional[dict]:
    """Crop image based on tight bounding box of figure content.

    Used for constrained_layout figures where content-based cropping doesn't work
    because matplotlib fills the canvas. Uses matplotlib's get_tightbbox() to find
    the actual content bounds including labels, titles, and legends.

    Parameters
    ----------
    fig : RecordingFigure
        The figure (needed to get tight bounding box)
    image_path : Path
        Path to the saved image
    mm_layout : dict
        Layout configuration with crop margins
    dpi : int
        Image DPI

    Returns
    -------
    dict or None
        Crop offset dictionary if cropping was performed, None otherwise
    """
    from PIL import Image

    from .._utils._crop import mm_to_pixels

    # Get crop margins from mm_layout
    margin_left_mm = mm_layout.get("crop_margin_left_mm", 1)
    margin_right_mm = mm_layout.get("crop_margin_right_mm", 1)
    margin_top_mm = mm_layout.get("crop_margin_top_mm", 1)
    margin_bottom_mm = mm_layout.get("crop_margin_bottom_mm", 1)

    # Get tight bounding box of figure content (includes labels, titles, legends)
    # Need to draw the figure first to get accurate bbox
    fig.fig.canvas.draw()
    renderer = fig.fig.canvas.get_renderer()
    tight_bbox = fig.fig.get_tightbbox(renderer)

    if tight_bbox is None:
        return None

    # Open image to get dimensions
    img = Image.open(image_path)
    orig_w, orig_h = img.size

    # tight_bbox is in inches, convert to pixels
    fig_dpi = fig.fig.dpi
    content_left_px = int(tight_bbox.x0 * fig_dpi)
    content_right_px = int(tight_bbox.x1 * fig_dpi)
    # Flip y coordinate: tight_bbox y=0 is bottom, image y=0 is top
    content_top_px = int(orig_h - tight_bbox.y1 * fig_dpi)
    content_bottom_px = int(orig_h - tight_bbox.y0 * fig_dpi)

    # Calculate margins in pixels
    margin_left_px = mm_to_pixels(margin_left_mm, dpi)
    margin_right_px = mm_to_pixels(margin_right_mm, dpi)
    margin_top_px = mm_to_pixels(margin_top_mm, dpi)
    margin_bottom_px = mm_to_pixels(margin_bottom_mm, dpi)

    # Calculate crop bounds with margins around content
    crop_left = content_left_px - margin_left_px
    crop_top = content_top_px - margin_top_px
    crop_right = content_right_px + margin_right_px
    crop_bottom = content_bottom_px + margin_bottom_px

    # Clamp to image boundaries
    crop_left = max(0, crop_left)
    crop_top = max(0, crop_top)
    crop_right = min(orig_w, crop_right)
    crop_bottom = min(orig_h, crop_bottom)

    # Crop the image
    cropped_img = img.crop((crop_left, crop_top, crop_right, crop_bottom))

    # Preserve DPI metadata
    save_kwargs = {}
    if "dpi" in img.info:
        save_kwargs["dpi"] = img.info["dpi"]

    ext = image_path.suffix.lower()
    if ext == ".png":
        save_kwargs["compress_level"] = 0
        save_kwargs["optimize"] = False

    cropped_img.save(image_path, **save_kwargs)

    return {
        "left": crop_left,
        "upper": crop_top,
        "right": crop_right,
        "lower": crop_bottom,
        "original_width": orig_w,
        "original_height": orig_h,
        "new_width": cropped_img.width,
        "new_height": cropped_img.height,
    }


def _capture_axes_bboxes(fig, crop_offset: Optional[dict] = None) -> None:
    """Capture bounding boxes of all axes for alignment/snap functionality.

    Stores bbox as [left, bottom, width, height] in figure coordinates (0-1).
    If crop_offset is provided, adjusts bbox to post-crop coordinate system.

    Parameters
    ----------
    fig : RecordingFigure
        The figure with record to update.
    crop_offset : dict, optional
        Crop information from crop() with return_offset=True.
        Contains: left, upper, right, lower, original_width, original_height,
        new_width, new_height (all in pixels).
    """
    for ax in fig.fig.get_axes():
        # Get axes position in figure coordinates (0-1 range)
        bbox = ax.get_position()
        bbox_list = [bbox.x0, bbox.y0, bbox.width, bbox.height]

        # Adjust for crop offset if provided
        if crop_offset is not None:
            # Convert from figure coords to pixel coords, then to cropped coords
            orig_w = crop_offset["original_width"]
            orig_h = crop_offset["original_height"]
            new_w = crop_offset["new_width"]
            new_h = crop_offset["new_height"]
            crop_left = crop_offset["left"]
            crop_upper = crop_offset["upper"]

            # Original pixel positions (matplotlib y=0 is bottom, image y=0 is top)
            x0_px = bbox.x0 * orig_w
            y0_px = (1 - bbox.y0 - bbox.height) * orig_h  # Convert to image coords
            w_px = bbox.width * orig_w
            h_px = bbox.height * orig_h

            # Adjust for crop (translate origin)
            x0_cropped = x0_px - crop_left
            y0_cropped = y0_px - crop_upper

            # Convert back to figure coordinates (0-1 range in cropped image)
            new_x0 = x0_cropped / new_w
            new_y0 = 1 - (y0_cropped + h_px) / new_h  # Back to matplotlib coords
            new_w_frac = w_px / new_w
            new_h_frac = h_px / new_h

            bbox_list = [new_x0, new_y0, new_w_frac, new_h_frac]

        # Find corresponding AxesRecord
        # Try to match by checking if this ax corresponds to a known position
        for key, ax_record in fig.record.axes.items():
            # Parse key (accepts "r0c0" or legacy "ax_0_0"); "ax_mm_idx" -> None
            parsed = parse_grid_id(key)
            if parsed is not None:
                # Standard grid format
                if ax_record.position == parsed:
                    ax_record.bbox = bbox_list
                    break
            elif key.startswith("ax_mm_"):
                # Mm-based format: ax_mm_idx
                ax_record.bbox = bbox_list
                break


def save_hitmap(
    fig,
    image_path: Path,
    dpi: int,
    verbose: bool,
    bbox_inches: Optional[str] = None,
    pad_inches: float = 0.0,
) -> Optional[Path]:
    """Save hitmap image for GUI editor element selection.

    Parameters
    ----------
    bbox_inches : str, optional
        If "tight", hitmap is rendered with bbox_inches="tight" to match
        figures saved with constrained_layout (e.g. pie, imshow).
    pad_inches : float
        Padding in inches when bbox_inches="tight".

    Returns
    -------
    Path or None
    """
    try:
        hitmap_path = image_path.with_stem(image_path.stem + "_hitmap")
        mpl_fig = fig.fig if hasattr(fig, "fig") else fig
        diagram = getattr(mpl_fig, "_figrecipe_diagram", None)

        if diagram is not None:
            from .._diagram._diagram._hitmap import save_diagram_hitmap

            save_diagram_hitmap(diagram, hitmap_path, dpi=min(dpi, 150))
        else:
            from .._editor._hitmap import generate_hitmap

            hitmap_img, _ = generate_hitmap(
                fig,
                dpi=min(dpi, 150),
                bbox_inches=bbox_inches,
                pad_inches=pad_inches,
            )
            hitmap_img.save(hitmap_path)

        if verbose:
            print(f"  Hitmap: {hitmap_path}")
        return hitmap_path
    except Exception as e:
        if verbose:
            print(f"  Hitmap generation failed: {e}")
        return None
