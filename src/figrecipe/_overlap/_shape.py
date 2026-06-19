#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shape (geometric) overlap detection.

The id-stamped hitmap is the canonical ground-truth for "what pixel is
owned by what element". Because the hitmap is drawn top-down, the
*last-drawn* element on a pixel wins — so plain owner-mask intersection
is always zero.

Instead we detect shape overlap by:

1. Walking each pair of element masks.
2. Asking: did element ``b`` paint over a region that element ``a``
   would have owned if drawn alone? We approximate this via the
   1-pixel adjacency intersection from
   :func:`figrecipe._overlap._hitmap.iter_overlapping_pairs` — a pixel
   from ``a`` whose neighbour is ``b`` means the two elements share a
   boundary, which is the rasterised signature of overlap.
3. The opt-in policy is per-artist (``allow_overlap='warn'``).

The result is a list of :class:`ShapeOverlapReport`s plus the elements'
``element_id`` pairs.
"""

from __future__ import annotations

from typing import List, Optional

from ._hitmap import ElementHitmap, bbox_of_mask, iter_overlapping_pairs
from ._report import ShapeOverlapReport

DEFAULT_MIN_OVERLAP_PIXELS = 4  # ignore single-pixel antialiasing seams


def _resolve_artist_policy(color_map: dict, fig, eid: int, default: str) -> str:
    """Walk back from element id -> artist -> policy attribute."""
    key = None
    for k, meta in color_map.items():
        if int(meta.get("id", -1)) == int(eid):
            key = k
            break
    if key is None:
        return default
    # The hitmap colour-map stores ax_index but not the artist itself —
    # we need the live matplotlib axes/artists list to look up an
    # ``_figrecipe_allow_overlap`` flag. We do a best-effort traversal:
    # for line/scatter we expect the same artist order as
    # ``ax.get_lines()`` / ``ax.collections``. This is an opt-in marker,
    # so a missing artist is safe — we return the default.
    mpl_fig = getattr(fig, "_fig", fig)
    ax_idx = color_map[key].get("ax_index")
    if mpl_fig is None or ax_idx is None:
        return default
    axes_list = mpl_fig.get_axes()
    if not (0 <= ax_idx < len(axes_list)):
        return default
    ax = axes_list[ax_idx]
    label = color_map[key].get("label", "")
    for child in (
        list(ax.get_lines()) + list(ax.collections) + list(ax.patches) + list(ax.images)
    ):
        if hasattr(child, "get_label") and child.get_label() == label:
            pol = getattr(child, "_figrecipe_allow_overlap", None)
            if pol is not None:
                return str(pol)
    return default


def detect_shape_overlaps(
    hitmap: ElementHitmap,
    *,
    fig=None,
    default_severity: str = "error",
    min_overlap_pixels: int = DEFAULT_MIN_OVERLAP_PIXELS,
) -> List[ShapeOverlapReport]:
    """Walk all pairs and report adjacency-based overlaps.

    Parameters
    ----------
    hitmap : ElementHitmap
        Pre-computed element-ownership map.
    fig : optional
        Live figure used to look up per-artist ``_figrecipe_allow_overlap``
        flags. Pass ``None`` to skip per-artist overrides.
    default_severity : 'error' | 'warn'
        The severity to use when no per-artist override is present.
    """
    reports: List[ShapeOverlapReport] = []
    if hitmap.owner_id.size == 0:
        return reports

    total_pixels = hitmap.owner_id.size

    for eid_a, eid_b, adj_mask in iter_overlapping_pairs(
        hitmap, min_overlap_pixels=min_overlap_pixels
    ):
        # Resolve per-element severity overrides.
        sev_a = _resolve_artist_policy(hitmap.color_map, fig, eid_a, default_severity)
        sev_b = _resolve_artist_policy(hitmap.color_map, fig, eid_b, default_severity)
        # Worst-of: if either element opts out to warn/off, demote.
        severity = _combine_severity(sev_a, sev_b, default_severity)
        if severity == "off":
            continue

        key_a = hitmap.id_to_key(eid_a) or f"id_{eid_a}"
        key_b = hitmap.id_to_key(eid_b) or f"id_{eid_b}"
        ax_idx = hitmap.axes_for(eid_a)
        axes_key = f"ax_{ax_idx}" if ax_idx is not None else None
        count = int(adj_mask.sum())
        bbox = bbox_of_mask(adj_mask)
        reports.append(
            ShapeOverlapReport(
                element_a=key_a,
                element_b=key_b,
                axes_key=axes_key,
                severity=severity,
                overlap_pixels=count,
                overlap_fraction=count / total_pixels,
                region_bbox=bbox,
            )
        )
    return reports


def _combine_severity(a: str, b: str, default: str) -> str:
    """Combine two per-element severities into one effective level.

    Rule: the most permissive wins (so a KDE marked ``warn`` paired with
    a default ``error`` element downgrades to ``warn``). ``off`` from
    either side fully silences. This matches the operator's intent:
    "intentional overlay" is a property of the participating elements,
    not the whole panel.
    """
    order = {"off": 0, "warn": 1, "error": 2}
    a_v = order.get(a, order.get(default, 2))
    b_v = order.get(b, order.get(default, 2))
    eff = min(a_v, b_v)
    return {0: "off", 1: "warn", 2: "error"}[eff]


__all__ = [
    "detect_shape_overlaps",
    "DEFAULT_MIN_OVERLAP_PIXELS",
]
