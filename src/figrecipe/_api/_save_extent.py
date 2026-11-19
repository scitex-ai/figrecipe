"""Render overflowing ink before a requested deterministic content crop."""

import math


def _save_expanded_content_crop(
    fig, image_path, *, dpi, crop_margin_mm, crop_margins_mm, **save_kwargs
):
    """Save an overflowing recorded extent and return crop metadata and bbox.

    In-bounds figures return (None, None), preserving the existing raster crop.
    A post-render crop cannot recover artists clipped by the original canvas.
    The explicit Matplotlib bbox renders those artists without resizing axes.
    """
    from matplotlib.transforms import Bbox
    try:
        from PIL import Image
    except ImportError as exc:
        from .._utils._optional import missing_extra

        raise missing_extra(exc) from exc

    from ._save_helpers import _capture_content_layout

    if fig.record.content_bbox is None:
        _capture_content_layout(fig)
    content = fig.record.content_bbox
    if content is None:
        return None, None
    left, bottom, width, height = map(float, content)
    if not all(math.isfinite(v) for v in (left, bottom, width, height)):
        return None, None
    if width <= 0 or height <= 0:
        return None, None
    if left >= 0 and bottom >= 0 and left + width <= 1 and bottom + height <= 1:
        return None, None

    ml, mr, mt, mb = crop_margins_mm
    if crop_margin_mm is not None:
        ml = mr = mt = mb = crop_margin_mm
    fw, fh = map(float, fig.fig.get_size_inches())
    recorded = Bbox.from_bounds(left * fw, bottom * fh, width * fw, height * fh)
    # Glyph hinting can change physical text extents at the export DPI. Keep
    # the recorded extent as a floor and include actual output-DPI ink too.
    original_dpi = fig.fig.dpi
    try:
        fig.fig.set_dpi(dpi)
        fig.fig.canvas.draw()
        rendered = fig.fig.get_tightbbox(fig.fig.canvas.get_renderer())
    finally:
        fig.fig.set_dpi(original_dpi)
    extent = Bbox.union([recorded, rendered]) if rendered is not None else recorded
    bbox = Bbox.from_extents(
        extent.x0 - ml / 25.4,
        extent.y0 - mb / 25.4,
        extent.x1 + mr / 25.4,
        extent.y1 + mt / 25.4,
    )
    fig.fig.savefig(image_path, dpi=dpi, bbox_inches=bbox, **save_kwargs)
    with Image.open(image_path) as image:
        new_width, new_height = image.size
    offset = {
        "left": bbox.x0 * dpi,
        "upper": (fh - bbox.y1) * dpi,
        "right": bbox.x1 * dpi,
        "lower": (fh - bbox.y0) * dpi,
        "original_width": fw * dpi,
        "original_height": fh * dpi,
        "new_width": new_width,
        "new_height": new_height,
    }
    return offset, bbox
