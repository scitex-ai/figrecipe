#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic ring-search label placement (pure geometry, display coords).

Given anchor points, label box sizes, an ink-occupancy mask, and obstacle
rectangles (legend box, already-drawn labels), place each label at the nearest
position whose box is clear of ink, of prior labels, and of the obstacles,
clipped to the axes. Search order is a FIXED preference ring (up / up-right /
right / ... at increasing radius), so the result is fully deterministic and
seedless -- the same inputs always yield the same positions, which is what makes
the recipe reproduce byte-identically.

All coordinates are matplotlib DISPLAY coordinates (pixels, y growing upward, to
match ``transData.transform``). The ink mask is the boolean array from
``_quality._overlap._render_ink_mask`` (row 0 = top of canvas).
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

# Rectangle as (x0, y0, x1, y1) in display coords, y growing upward.
Rect = Tuple[float, float, float, float]
Point = Tuple[float, float]

# Fraction of ink pixels inside a label box above which the box is "on data".
DEFAULT_INK_TOL = 0.02
# Fractional box-overlap with an obstacle above which the box "collides".
_OBSTACLE_TOL = 0.0
# Eight compass directions in preference order: up first (labels above a point
# read best), then the upper diagonals, sides, and finally below. Fixed order =
# deterministic placement.
_COMPASS: Tuple[Point, ...] = (
    (0.0, 1.0),  # up
    (1.0, 1.0),  # up-right
    (-1.0, 1.0),  # up-left
    (1.0, 0.0),  # right
    (-1.0, 0.0),  # left
    (1.0, -1.0),  # down-right
    (-1.0, -1.0),  # down-left
    (0.0, -1.0),  # down
)


def _rect_at(cx: float, cy: float, w: float, h: float) -> Rect:
    """Axis-aligned box of size (w, h) centered at (cx, cy)."""
    hw, hh = w / 2.0, h / 2.0
    return (cx - hw, cy - hh, cx + hw, cy + hh)


def _overlap_fraction(a: Rect, b: Rect) -> float:
    """intersection_area / min(area_a, area_b); 0 if disjoint."""
    iw = min(a[2], b[2]) - max(a[0], b[0])
    ih = min(a[3], b[3]) - max(a[1], b[1])
    if iw <= 0 or ih <= 0:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    denom = min(area_a, area_b)
    return (iw * ih) / denom if denom > 0 else 0.0


def _inside(inner: Rect, outer: Rect) -> bool:
    """True if ``inner`` lies fully within ``outer`` (used for axes clipping)."""
    return (
        inner[0] >= outer[0]
        and inner[1] >= outer[1]
        and inner[2] <= outer[2]
        and inner[3] <= outer[3]
    )


def _ink_fraction(ink_mask, height: int, rect: Rect) -> float:
    """Fraction of ink (True) pixels inside a display-coord rect (y flipped)."""
    import numpy as np

    x0 = max(0, int(np.floor(rect[0])))
    x1 = int(np.ceil(rect[2]))
    # Display y grows upward; array row 0 is the top of the canvas -> flip.
    r0 = max(0, int(np.floor(height - rect[3])))
    r1 = int(np.ceil(height - rect[1]))
    if x1 <= x0 or r1 <= r0:
        return 0.0
    region = ink_mask[r0:r1, x0:x1]
    if region.size == 0:
        return 0.0
    return float(region.mean())


def _ring_offsets(radius: float) -> List[Point]:
    """Offsets at a given radius in fixed compass order. radius 0 -> origin."""
    if radius <= 0:
        return [(0.0, 0.0)]
    return [(dx * radius, dy * radius) for dx, dy in _COMPASS]


def _candidate_positions(anchor: Point, step: float, max_radius: float) -> List[Point]:
    """Anchor-relative candidate CENTERS, nearest first (deterministic)."""
    ax_, ay_ = anchor
    positions: List[Point] = []
    radius = 0.0
    while radius <= max_radius:
        for dx, dy in _ring_offsets(radius):
            positions.append((ax_ + dx, ay_ + dy))
        radius += step
    return positions


def solve_label_positions(
    anchors: Sequence[Point],
    sizes: Sequence[Point],
    ink_mask,
    height: int,
    obstacles: Optional[Sequence[Rect]] = None,
    clip_rect: Optional[Rect] = None,
    *,
    step: float = 6.0,
    max_radius: float = 160.0,
    ink_tol: float = DEFAULT_INK_TOL,
) -> Tuple[List[Point], List[bool]]:
    """Place each label deterministically, avoiding ink / obstacles / siblings.

    Parameters
    ----------
    anchors : list of (x, y)
        Display-coord point each label belongs to.
    sizes : list of (w, h)
        Display-coord box size of each label's rendered text.
    ink_mask, height :
        Boolean data-ink array + canvas height from ``_render_ink_mask``. Pass
        ``ink_mask=None`` to skip the ink test (obstacles/siblings still apply).
    obstacles : list of rects, optional
        Extra display-coord boxes to avoid (e.g. the legend). Grows internally
        with each placed label so labels never overlap each other.
    clip_rect : rect, optional
        Axes box; candidate boxes must lie fully inside it. ``None`` = no clip.
    step, max_radius :
        Ring search granularity / reach, in display pixels.
    ink_tol :
        Max ink fraction inside a label box before it counts as "on data".

    Returns
    -------
    (centers, placed_clear)
        ``centers`` are the solved label CENTERS in display coords.
        ``placed_clear[i]`` is False when no clear spot was found within
        ``max_radius`` and the label fell back to its anchor (caller should
        warn -- a fallback is a visible clutter, never silent).
    """
    occupied: List[Rect] = list(obstacles or [])
    centers: List[Point] = []
    placed_clear: List[bool] = []

    for anchor, (w, h) in zip(anchors, sizes):
        chosen: Optional[Point] = None
        for cx, cy in _candidate_positions(anchor, step, max_radius):
            box = _rect_at(cx, cy, w, h)
            if clip_rect is not None and not _inside(box, clip_rect):
                continue
            if any(_overlap_fraction(box, o) > _OBSTACLE_TOL for o in occupied):
                continue
            if ink_mask is not None and _ink_fraction(ink_mask, height, box) > ink_tol:
                continue
            chosen = (cx, cy)
            break

        if chosen is None:
            # No clear spot within reach: fall back to the anchor and flag it so
            # the caller can warn. NOT silent -- a dropped-on-data label is a
            # real quality issue the author must see.
            chosen = anchor
            placed_clear.append(False)
        else:
            placed_clear.append(True)
        occupied.append(_rect_at(chosen[0], chosen[1], w, h))
        centers.append(chosen)

    return centers, placed_clear


__all__ = ["solve_label_positions", "DEFAULT_INK_TOL"]

# EOF
