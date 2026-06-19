#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Color overlap detection using CIEDE2000.

For each pair of spatially-adjacent (or overlapping) elements we sample
the *actual* rendered RGB colors of the two elements and compute the
CIEDE2000 perceptual distance. If ΔE < threshold (default 5) we flag
the pair as a "color overlap" — two visually-indistinguishable elements
in the same region.

CIEDE2000 reference: Sharma G., Wu W., Dalal E. N. (2005), "The CIEDE2000
color-difference formula: implementation notes, supplementary test data,
and mathematical observations", Color Research & Application.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from ._hitmap import ElementHitmap, bbox_of_mask, iter_overlapping_pairs
from ._report import ColorOverlapReport

DEFAULT_DELTA_E_THRESHOLD = 5.0


# ---------------------------------------------------------------------------
# sRGB → CIE Lab conversion (D65, observer 2°)
# ---------------------------------------------------------------------------


def _srgb_to_linear(c: np.ndarray) -> np.ndarray:
    c = c.astype(np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _linear_to_xyz(rgb_linear: np.ndarray) -> np.ndarray:
    # sRGB → XYZ D65 matrix
    M = np.array(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ]
    )
    return rgb_linear @ M.T


def _xyz_to_lab(xyz: np.ndarray) -> np.ndarray:
    # D65 white reference
    xn, yn, zn = 0.95047, 1.00000, 1.08883
    x = xyz[..., 0] / xn
    y = xyz[..., 1] / yn
    z = xyz[..., 2] / zn

    def f(t: np.ndarray) -> np.ndarray:
        return np.where(t > 0.008856, np.cbrt(t), (903.3 * t + 16.0) / 116.0)

    fx, fy, fz = f(x), f(y), f(z)
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return np.stack([L, a, b], axis=-1)


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """Convert sRGB ([0..255], any shape) to CIE Lab."""
    linear = _srgb_to_linear(np.asarray(rgb))
    xyz = _linear_to_xyz(linear)
    return _xyz_to_lab(xyz)


def ciede2000(lab1: np.ndarray, lab2: np.ndarray) -> float:
    """Return scalar CIEDE2000 ΔE between two Lab triplets.

    Reference implementation: Sharma 2005. Inputs must be length-3 arrays.
    """
    L1, a1, b1 = float(lab1[0]), float(lab1[1]), float(lab1[2])
    L2, a2, b2 = float(lab2[0]), float(lab2[1]), float(lab2[2])

    C1 = np.hypot(a1, b1)
    C2 = np.hypot(a2, b2)
    Cbar = (C1 + C2) / 2.0
    G = 0.5 * (1.0 - np.sqrt(Cbar**7 / (Cbar**7 + 25.0**7)))
    a1p = (1.0 + G) * a1
    a2p = (1.0 + G) * a2
    C1p = np.hypot(a1p, b1)
    C2p = np.hypot(a2p, b2)

    h1p = np.degrees(np.arctan2(b1, a1p)) % 360.0
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360.0

    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    else:
        dhp = h2p - h1p
        if dhp > 180:
            dhp -= 360
        elif dhp < -180:
            dhp += 360
    dHp = 2.0 * np.sqrt(C1p * C2p) * np.sin(np.radians(dhp / 2.0))

    Lbarp = (L1 + L2) / 2.0
    Cbarp = (C1p + C2p) / 2.0
    if C1p * C2p == 0:
        hbarp = h1p + h2p
    else:
        hsum = h1p + h2p
        hdiff = abs(h1p - h2p)
        if hdiff <= 180:
            hbarp = hsum / 2.0
        else:
            hbarp = (hsum + (360 if hsum < 360 else -360)) / 2.0

    T = (
        1.0
        - 0.17 * np.cos(np.radians(hbarp - 30.0))
        + 0.24 * np.cos(np.radians(2.0 * hbarp))
        + 0.32 * np.cos(np.radians(3.0 * hbarp + 6.0))
        - 0.20 * np.cos(np.radians(4.0 * hbarp - 63.0))
    )
    dTheta = 30.0 * np.exp(-(((hbarp - 275.0) / 25.0) ** 2))
    Rc = 2.0 * np.sqrt(Cbarp**7 / (Cbarp**7 + 25.0**7))
    Sl = 1.0 + (0.015 * (Lbarp - 50.0) ** 2) / np.sqrt(20.0 + (Lbarp - 50.0) ** 2)
    Sc = 1.0 + 0.045 * Cbarp
    Sh = 1.0 + 0.015 * Cbarp * T
    Rt = -np.sin(np.radians(2.0 * dTheta)) * Rc

    Kl = Kc = Kh = 1.0
    return float(
        np.sqrt(
            (dLp / (Kl * Sl)) ** 2
            + (dCp / (Kc * Sc)) ** 2
            + (dHp / (Kh * Sh)) ** 2
            + Rt * (dCp / (Kc * Sc)) * (dHp / (Kh * Sh))
        )
    )


def _element_average_rgb(
    rendered: np.ndarray,
    owner: np.ndarray,
    eid: int,
) -> Optional[Tuple[float, float, float]]:
    mask = owner == eid
    if not mask.any():
        return None
    pixels = rendered[mask]
    if pixels.size == 0:
        return None
    mean = pixels.mean(axis=0)
    return float(mean[0]), float(mean[1]), float(mean[2])


def detect_color_overlaps(
    hitmap: ElementHitmap,
    *,
    threshold: float = DEFAULT_DELTA_E_THRESHOLD,
    severity: str = "warn",
) -> List[ColorOverlapReport]:
    """Return a list of ColorOverlapReport for all problematic pairs.

    The detector only fires on pairs that are *also* spatially adjacent —
    two indistinguishable colors on opposite sides of the figure are not
    a "color overlap"; they're only a problem when the two elements
    share a region of the figure.
    """
    if hitmap.rendered_rgb is None:
        return []

    reports: List[ColorOverlapReport] = []
    for eid_a, eid_b, adj_mask in iter_overlapping_pairs(hitmap):
        rgb_a = _element_average_rgb(hitmap.rendered_rgb, hitmap.owner_id, eid_a)
        rgb_b = _element_average_rgb(hitmap.rendered_rgb, hitmap.owner_id, eid_b)
        if rgb_a is None or rgb_b is None:
            continue
        lab_a = rgb_to_lab(np.array(rgb_a))
        lab_b = rgb_to_lab(np.array(rgb_b))
        d_e = ciede2000(lab_a, lab_b)
        if d_e >= threshold:
            continue

        key_a = hitmap.id_to_key(eid_a) or f"id_{eid_a}"
        key_b = hitmap.id_to_key(eid_b) or f"id_{eid_b}"
        ax_idx = hitmap.axes_for(eid_a)
        axes_key = f"ax_{ax_idx}" if ax_idx is not None else None
        bbox = bbox_of_mask(adj_mask)
        # Region summary: descriptive shorthand
        if bbox is not None:
            x1, y1, x2, y2 = bbox
            region_str = (
                f"approx px-bbox ({x1},{y1})-({x2},{y2}); "
                f"{int(adj_mask.sum())} adjacent pixels"
            )
        else:
            region_str = "no contiguous region"
        # Shared color summary: mean colour
        avg_rgb = (
            (rgb_a[0] + rgb_b[0]) / 2,
            (rgb_a[1] + rgb_b[1]) / 2,
            (rgb_a[2] + rgb_b[2]) / 2,
        )
        color_str = (
            f"approx rgb({int(avg_rgb[0])},{int(avg_rgb[1])},{int(avg_rgb[2])}) "
            f"ΔE={d_e:.2f}"
        )
        reports.append(
            ColorOverlapReport(
                element_a=key_a,
                element_b=key_b,
                axes_key=axes_key,
                severity=severity,
                delta_e=float(d_e),
                threshold=float(threshold),
                color_a_rgb=rgb_a,
                color_b_rgb=rgb_b,
                shared_color_summary=color_str,
                region_summary=region_str,
            )
        )
    return reports


__all__ = [
    "DEFAULT_DELTA_E_THRESHOLD",
    "ciede2000",
    "rgb_to_lab",
    "detect_color_overlaps",
]
