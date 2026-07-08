#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Data-only "ink" raster for the save-time overlap detector.

Split out of ``_overlap.py`` (which sat at the 512-line ceiling) so the ink
helpers have room for the idiomatic ``isinstance`` text check. ``_overlap.py``
re-imports ``_render_ink_mask`` + ``_ink_fraction_in_bbox`` from here and stays
a thin orchestrator.

The ink mask hides all Text (labels, ticks, titles, annotations) and all
legends, then rasterizes what remains — the DATA ink (lines, markers,
collections, images, patches) — for the ``legend <-> ink`` occlusion check.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.figure import Figure
    from matplotlib.transforms import Bbox

# Color distance (max per-channel, 0-255) under which a pixel counts as
# "background". Small, to tolerate antialiasing without swallowing faint ink.
_BG_TOL = 18


def _parse_bg_color(style: Optional[dict]) -> Tuple[int, int, int]:
    """Background RGB (0-255) from style ``theme_colors``, fallback white.

    Tries ``axes_bg`` then ``figure_bg``; a transparent/none/missing value
    falls back to white (the raster canvas is white when bg is transparent).
    """
    import matplotlib.colors as mcolors

    candidates = []
    if isinstance(style, dict):
        theme = style.get("theme_colors")
        if isinstance(theme, dict):
            candidates = [theme.get("axes_bg"), theme.get("figure_bg")]
    for color in candidates:
        if not color:
            continue
        if isinstance(color, str) and color.lower() in ("none", "transparent"):
            continue
        try:
            r, g, b = mcolors.to_rgb(color)
            return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))
        except (ValueError, TypeError):
            continue
    return 255, 255, 255


def _render_ink_mask(fig: "Figure", style: Optional[dict]):
    """Render a data-only raster; return ``(ink_mask, height)`` or ``None``.

    All Text artists and all legends are hidden so only data ink (lines,
    markers, collections, images, patches) remains. Pixels whose distance
    from the background color exceeds ``_BG_TOL`` are ink. Returns ``None``
    when numpy is unavailable or the canvas cannot rasterize.
    """
    try:
        import numpy as np
    except Exception:  # pragma: no cover - numpy always present in practice
        return None

    import matplotlib.text as mtext

    hidden: List = []
    canvas = fig.canvas
    try:
        for artist in fig.findobj():
            # isinstance so Text SUBCLASSES (Annotation, etc.) are also hidden;
            # an exact class-name check leaked annotation pixels into the mask.
            if isinstance(artist, mtext.Text) and artist.get_visible():
                hidden.append(artist)
                artist.set_visible(False)
        for ax in fig.get_axes():
            legend = ax.get_legend()
            if legend is not None and legend.get_visible():
                hidden.append(legend)
                legend.set_visible(False)
        for legend in getattr(fig, "legends", []) or []:
            if legend.get_visible():
                hidden.append(legend)
                legend.set_visible(False)
        try:
            canvas.draw()
            buf = np.asarray(canvas.buffer_rgba())
        except Exception:
            return None
    finally:
        for artist in hidden:
            artist.set_visible(True)

    if buf.ndim != 3 or buf.shape[2] < 3:
        return None
    rgb = buf[..., :3].astype(np.int16)
    bg = np.array(_parse_bg_color(style), dtype=np.int16)
    diff = np.abs(rgb - bg).max(axis=-1)
    ink = diff > _BG_TOL
    return ink, buf.shape[0]


def _ink_fraction_in_bbox(ink_mask, height: int, bbox: "Bbox") -> float:
    """Fraction of ink pixels inside a display-coord bbox (y is flipped)."""
    import numpy as np  # local: only reached when a mask exists

    x0 = max(0, int(np.floor(bbox.x0)))
    x1 = int(np.ceil(bbox.x1))
    # Display y grows upward; array row 0 is the top -> flip.
    r0 = max(0, int(np.floor(height - bbox.y1)))
    r1 = int(np.ceil(height - bbox.y0))
    if x1 <= x0 or r1 <= r0:
        return 0.0
    region = ink_mask[r0:r1, x0:x1]
    if region.size == 0:
        return 0.0
    return float(region.mean())


__all__ = [
    "_render_ink_mask",
    "_ink_fraction_in_bbox",
    "_parse_bg_color",
    "_BG_TOL",
]

# EOF
