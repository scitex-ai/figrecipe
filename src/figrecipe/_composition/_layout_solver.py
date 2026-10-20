#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layout solver for converting source lists to mm-based positioning."""

from pathlib import Path
from typing import Any, Dict, List

from .._utils._optional import missing_extra


def solve_layout_to_mm(
    sources: List[str], layout: str = "horizontal", gap_mm: float = 5.0
) -> Dict[str, Dict[str, Any]]:
    """Convert list of sources to mm-based positioning dict.

    Parameters
    ----------
    sources : list
        List of source file paths.
    layout : str
        Layout mode: 'horizontal', 'vertical', or 'grid'.
    gap_mm : float
        Gap between panels in mm.

    Returns
    -------
    dict
        Sources dict with mm positioning: {path: {"xy_mm": ..., "size_mm": ...}}
    """
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - supplied by a figrecipe extra
        raise missing_extra(exc) from exc

    # Get sizes of all sources
    sizes = []
    for src in sources:
        path = Path(src)
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"}:
            with Image.open(path) as img:
                # Assume 300 dpi, convert to mm
                w_mm = img.width / 300 * 25.4
                h_mm = img.height / 300 * 25.4
                sizes.append((w_mm, h_mm))
        else:
            # Recipe file - use default size
            sizes.append((60.0, 45.0))

    # Calculate positions based on layout
    sources_mm = {}
    x, y = 0.0, 0.0

    if layout == "horizontal":
        for src, (w, h) in zip(sources, sizes):
            sources_mm[src] = {"xy_mm": (x, 0.0), "size_mm": (w, h)}
            x += w + gap_mm
    elif layout == "vertical":
        for src, (w, h) in zip(sources, sizes):
            sources_mm[src] = {"xy_mm": (0.0, y), "size_mm": (w, h)}
            y += h + gap_mm
    else:  # grid
        import math

        ncols = max(1, int(math.ceil(math.sqrt(len(sources)))))
        col, row_height = 0, 0.0
        for src, (w, h) in zip(sources, sizes):
            sources_mm[src] = {"xy_mm": (x, y), "size_mm": (w, h)}
            row_height = max(row_height, h)
            col += 1
            x += w + gap_mm
            if col >= ncols:
                col, x = 0, 0.0
                y += row_height + gap_mm
                row_height = 0.0

    return sources_mm


__all__ = ["solve_layout_to_mm"]
