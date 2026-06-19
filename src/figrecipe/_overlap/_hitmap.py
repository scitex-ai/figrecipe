#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Element-ownership hitmap shared by all three overlap detectors.

This module wraps :func:`figrecipe._editor._hitmap.generate_hitmap`,
which already renders each element with a unique RGB ID. We add:

* ID parsing — convert the unique RGB color back to an integer element
  ID so we can ask "which element owns this pixel?".
* Per-element pixel-mask extraction.
* A pairwise overlap-iterator that yields (id_a, id_b, mask) tuples for
  every pair of elements with a non-empty intersection.

We keep this code path independent of matplotlib so it can be unit-
tested with synthetic numpy arrays.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple

import numpy as np


@dataclass
class ElementHitmap:
    """A pixel-grid where each pixel is owned by at most one element.

    Attributes
    ----------
    owner_id : ndarray of int
        Shape (H, W). ``-1`` means background / no owner.
    color_map : dict
        Mapping ``element_key -> {"id": int, "type": str, "label": str,
        "ax_index": int, "rgb": [r, g, b]}`` — same shape as
        ``_editor._hitmap.generate_hitmap`` output.
    rendered_rgb : ndarray of uint8 or None
        The actual (real-color) rendered figure. Used by the color
        detector to read CIEDE2000-distinguishability. ``None`` when
        only the ID hitmap is needed (shape detector).
    """

    owner_id: np.ndarray
    color_map: Dict[str, Dict[str, Any]]
    rendered_rgb: Optional[np.ndarray] = None

    @property
    def element_ids(self) -> List[int]:
        """Sorted unique element IDs present in the hitmap (excluding background)."""
        ids = np.unique(self.owner_id)
        return [int(i) for i in ids if int(i) >= 1]

    def id_to_key(self, eid: int) -> Optional[str]:
        for key, meta in self.color_map.items():
            if int(meta.get("id", -1)) == int(eid):
                return key
        return None

    def mask_for(self, eid: int) -> np.ndarray:
        return self.owner_id == int(eid)

    def axes_for(self, eid: int) -> Optional[int]:
        key = self.id_to_key(eid)
        if key is None:
            return None
        return self.color_map[key].get("ax_index")


def _rgb_to_owner_id(hitmap_rgb: np.ndarray, color_map: Dict[str, Dict[str, Any]]):
    """Translate the per-pixel RGB stamp back to integer element IDs.

    Returns
    -------
    owner_id : ndarray (H, W) of int
        ``-1`` for background; otherwise the element id from color_map.
    """
    h, w = hitmap_rgb.shape[:2]
    # Pack RGB → single int24 for fast lookup
    packed = (
        hitmap_rgb[..., 0].astype(np.int64) * 256 * 256
        + hitmap_rgb[..., 1].astype(np.int64) * 256
        + hitmap_rgb[..., 2].astype(np.int64)
    )
    owner = np.full((h, w), -1, dtype=np.int64)
    for meta in color_map.values():
        rgb = meta.get("rgb")
        if rgb is None:
            continue
        key = int(rgb[0]) * 256 * 256 + int(rgb[1]) * 256 + int(rgb[2])
        owner[packed == key] = int(meta.get("id", -1))
    return owner


def build_element_hitmap(
    fig,
    *,
    dpi: int = 150,
    include_text: bool = False,
    include_real_render: bool = True,
) -> ElementHitmap:
    """Build a per-pixel element-ownership hitmap for ``fig``.

    Parameters
    ----------
    fig : matplotlib.Figure or RecordingFigure
        The figure to scan. We pull out the underlying matplotlib figure
        if a RecordingFigure is passed.
    dpi : int
        Render DPI for the hitmap. Lower DPI = faster, but precision of
        small-element detection drops. 150 is the published default of
        ``generate_hitmap``.
    include_text : bool
        If False, text artists are ignored (recommended for shape /
        color detection — text labels often cross plot lines on
        purpose).
    include_real_render : bool
        If True, also save the actual real-color render so the color
        detector can read CIEDE2000.
    """
    from PIL import Image

    from .._editor._hitmap_main import generate_hitmap

    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
    hitmap_img, color_map = generate_hitmap(mpl_fig, dpi=dpi, include_text=include_text)
    hitmap_rgb = np.asarray(hitmap_img)
    owner_id = _rgb_to_owner_id(hitmap_rgb, color_map)

    rendered_rgb = None
    if include_real_render:
        import io

        buf = io.BytesIO()
        mpl_fig.savefig(buf, format="png", dpi=dpi)
        buf.seek(0)
        rendered_rgb = np.asarray(Image.open(buf).convert("RGB"))
        # Match hitmap shape if matplotlib re-quantized somehow.
        if rendered_rgb.shape[:2] != hitmap_rgb.shape[:2]:
            real_img = (
                Image.open(buf)
                .convert("RGB")
                .resize((hitmap_rgb.shape[1], hitmap_rgb.shape[0]), Image.NEAREST)
            )
            rendered_rgb = np.asarray(real_img)

    return ElementHitmap(
        owner_id=owner_id,
        color_map=color_map,
        rendered_rgb=rendered_rgb,
    )


def iter_overlapping_pairs(
    hitmap: ElementHitmap,
    *,
    min_overlap_pixels: int = 4,
) -> Iterator[Tuple[int, int, np.ndarray]]:
    """Yield ``(id_a, id_b, dilation_intersection_mask)`` for spatially
    co-located element pairs.

    Because :func:`build_element_hitmap` paints each pixel with a *single*
    owner (the topmost element), pure intersection of the owner masks is
    always zero. We therefore detect spatial proximity by checking which
    distinct IDs lie within a 1-pixel neighbourhood of each other — this
    is the classic "ID boundary touches another ID" pattern. The mask
    returned is the set of pixels owned by ``id_a`` that lie within one
    pixel of ``id_b`` (i.e. true ``adjacency``, which for rasterised
    elements is equivalent to overlap of the underlying geometry up to
    one pixel of antialiasing).
    """
    ids = hitmap.element_ids
    owner = hitmap.owner_id

    # Build per-id pixel masks once.
    masks: Dict[int, np.ndarray] = {eid: (owner == eid) for eid in ids}

    # For adjacency: a pixel touches another id if any of its 4-neighbours
    # has a different id (and != -1). We compute pairwise overlap via:
    #   neighbour_id_set = shift(owner, dx, dy) for (dx, dy) ∈ {(-1,0),(1,0),(0,-1),(0,1)}
    # Then for each element id_a's mask, intersection with shifted-mask of
    # id_b gives the adjacency overlap.
    h, w = owner.shape
    for i, eid_a in enumerate(ids):
        mask_a = masks[eid_a]
        for eid_b in ids[i + 1 :]:
            mask_b = masks[eid_b]
            if hitmap.axes_for(eid_a) != hitmap.axes_for(eid_b):
                # Don't flag overlap across different subplots — that's just
                # adjacent axes touching at their boundary.
                continue
            # Compute 1-pixel-dilated intersection: any pixel of mask_a whose
            # 4-neighbour is mask_b, plus vice versa.
            adj = _adjacency_intersection(mask_a, mask_b)
            count = int(adj.sum())
            if count >= min_overlap_pixels:
                yield eid_a, eid_b, adj


def _adjacency_intersection(mask_a: np.ndarray, mask_b: np.ndarray) -> np.ndarray:
    """Pixels of ``mask_a`` whose 4-neighbour is ``mask_b`` (OR vice versa)."""
    # Shift mask_b by one in each of 4 directions; pixels of mask_a that
    # land on shifted mask_b are adjacent to mask_b.
    up = np.zeros_like(mask_b)
    up[:-1, :] = mask_b[1:, :]
    down = np.zeros_like(mask_b)
    down[1:, :] = mask_b[:-1, :]
    left = np.zeros_like(mask_b)
    left[:, :-1] = mask_b[:, 1:]
    right = np.zeros_like(mask_b)
    right[:, 1:] = mask_b[:, :-1]
    neighbours_of_b = up | down | left | right | mask_b
    return mask_a & neighbours_of_b


def bbox_of_mask(mask: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Return (x1, y1, x2, y2) bounding box of True pixels, or None if empty."""
    if not mask.any():
        return None
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    y1, y2 = np.where(rows)[0][[0, -1]]
    x1, x2 = np.where(cols)[0][[0, -1]]
    return int(x1), int(y1), int(x2), int(y2)


__all__ = [
    "ElementHitmap",
    "build_element_hitmap",
    "iter_overlapping_pairs",
    "bbox_of_mask",
]
