#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save-time COLOR-collision detector -- ambiguous, indistinguishable colors.

Concept
-------
Two data series a reader is asked to tell apart (i.e. both carry a real
legend label) but drawn in colors so close they are perceptually
indistinguishable make a figure ambiguous even when the shapes never
geometrically overlap. This detector, per data Axes, compares every pair
of labelled series in perceptual CIELAB space (ΔE*76) and flags any pair
whose colors sit below a just-noticeable threshold. It is the color
sibling of the geometric overlap check in ``_overlap`` and is surfaced
through the same save-time warning path.

Scope guards (avoid false positives)
------------------------------------
- Only series carrying a REAL legend label (not ``""``/``_``-prefixed) are
  compared -- decorative reference lines, grids, error bars without a
  label never trip the rule.
- Two artists sharing the SAME label are the same logical series drawn in
  parts -- identical color is intentional, never a collision.
- COLORMAPPED collections (a scatter with ``c=`` mapped to a colormap, so
  its points carry many colors) are skipped -- their gradient is
  deliberate, not an accidental duplicate.
- The default threshold (``_COLOR_JND_DELTA_E``) is conservative: distinct
  qualitative-palette entries sit well above it, so only genuine
  near-duplicate colors are flagged.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

__all__ = [
    "detect_color_collisions",
    "delta_e76",
]

# Minimum CIELAB ΔE*76 below which two labelled series are treated as
# indistinguishable. The JND for large solid patches is ~2.3; across a plot
# (thin lines, small markers) colors need more separation to read apart, but
# distinct qualitative-palette colors are all >15 ΔE, so 5.0 flags only real
# near-duplicates without touching legitimate palettes.
_COLOR_JND_DELTA_E = 5.0

_RGB = Tuple[float, float, float]
_LAB = Tuple[float, float, float]


# ---------------------------------------------------------------------------
# Color science: sRGB -> CIELAB (D65) + ΔE*76
# ---------------------------------------------------------------------------
def _srgb_to_linear(c: float) -> float:
    """Inverse sRGB companding for one channel in [0, 1]."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rgb_to_xyz(rgb: _RGB) -> Tuple[float, float, float]:
    """Linearise sRGB and apply the sRGB->XYZ (D65) matrix."""
    r, g, b = (_srgb_to_linear(c) for c in rgb)
    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505
    return x, y, z


def _f_lab(t: float) -> float:
    """CIELAB nonlinearity."""
    return t ** (1.0 / 3.0) if t > 0.008856 else (7.787 * t + 16.0 / 116.0)


def _srgb_to_lab(rgb: _RGB) -> _LAB:
    """Convert an sRGB triple in [0, 1] to CIELAB (D65 white point)."""
    x, y, z = _rgb_to_xyz(rgb)
    # D65 reference white.
    fx, fy, fz = _f_lab(x / 0.95047), _f_lab(y / 1.0), _f_lab(z / 1.08883)
    return (116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))


def delta_e76(rgb_a: _RGB, rgb_b: _RGB) -> float:
    """CIELAB ΔE*76 (Euclidean Lab distance) between two sRGB triples.

    Both inputs are sRGB in [0, 1]. Larger means more distinguishable;
    ~0 means identical.
    """
    la, lb = _srgb_to_lab(rgb_a), _srgb_to_lab(rgb_b)
    return math.sqrt(sum((p - q) ** 2 for p, q in zip(la, lb)))


# ---------------------------------------------------------------------------
# Per-artist representative color
# ---------------------------------------------------------------------------
def _single_rgb(color) -> Optional[_RGB]:
    """One sRGB triple from any matplotlib color spec, else None."""
    import matplotlib.colors as mcolors

    try:
        r, g, b, _a = mcolors.to_rgba(color)
        return (r, g, b)
    except Exception:
        return None


def _series_rgb(artist) -> Optional[_RGB]:
    """Representative sRGB for a data artist, or None if it has no single one.

    Line2D -> its line color. Patch -> its face color. Collection -> its
    single shared face color; a collection whose points carry MORE than one
    color (a colormapped scatter) returns None so its intentional gradient
    is never flagged.
    """
    import matplotlib.collections as mcoll
    import matplotlib.lines as mlines
    import numpy as np
    from matplotlib.patches import Patch

    if isinstance(artist, mlines.Line2D):
        return _single_rgb(artist.get_color())
    if isinstance(artist, mcoll.Collection):
        # Force colormap->facecolor mapping so a colormapped scatter exposes
        # its full per-point colors (matplotlib maps these lazily at draw).
        # A no-op for a single-color collection.
        try:
            artist.update_scalarmappable()
        except Exception:
            pass
        fc = np.asarray(artist.get_facecolor(), dtype=float)
        if fc.size == 0:
            fc = np.asarray(artist.get_edgecolor(), dtype=float)
        if fc.size == 0:
            return None
        rows = fc.reshape(-1, fc.shape[-1]) if fc.ndim > 1 else fc.reshape(1, -1)
        if np.unique(np.round(rows, 4), axis=0).shape[0] != 1:
            return None  # colormapped / multi-color -> intentional gradient
        return (float(rows[0][0]), float(rows[0][1]), float(rows[0][2]))
    if isinstance(artist, Patch):
        return _single_rgb(artist.get_facecolor())
    return None


def _real_label(label) -> bool:
    """True for a legend-worthy label (non-empty, not ``_``-prefixed)."""
    return isinstance(label, str) and bool(label) and not label.startswith("_")


def _collect_series(ax) -> List[Tuple[str, _RGB]]:
    """(label, rgb) for every visible, labelled data series in one Axes.

    Covers Line2D (``ax.lines``), Collections (scatter), labelled
    containers (bar/errorbar, label lives on the container) and any
    standalone labelled Patch. Bars are picked up once via their container;
    their child Rectangles carry ``_``-labels and are skipped.
    """
    series: List[Tuple[str, _RGB]] = []

    def _add(artist, label):
        if not getattr(artist, "get_visible", lambda: True)():
            return
        if not _real_label(label):
            return
        rgb = _series_rgb(artist)
        if rgb is not None:
            series.append((label, rgb))

    for ln in ax.get_lines():
        _add(ln, ln.get_label())
    for coll in ax.collections:
        _add(coll, coll.get_label())
    for cont in getattr(ax, "containers", []) or []:
        if not _real_label(cont.get_label()):
            continue
        for child in cont:
            rgb = _series_rgb(child)
            if rgb is not None:
                series.append((cont.get_label(), rgb))
                break
    for patch in ax.patches:
        _add(patch, patch.get_label())
    return series


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def _resolve_axes(fig_or_axes):
    """Accept a list of Axes, a matplotlib Figure, or a RecordingFigure."""
    if isinstance(fig_or_axes, (list, tuple)):
        return list(fig_or_axes)
    mpl_fig = getattr(fig_or_axes, "fig", fig_or_axes)
    if not hasattr(mpl_fig, "get_axes"):
        return []
    canvas = getattr(mpl_fig, "canvas", None)
    if canvas is not None:
        try:
            canvas.draw()
        except Exception:
            pass
    from ._overlap import _classify_axes

    data_axes, _colorbars, _overlays = _classify_axes(mpl_fig)
    return data_axes


def detect_color_collisions(fig_or_axes, min_delta_e: float = _COLOR_JND_DELTA_E):
    """Report pairs of labelled series with near-identical (ambiguous) colors.

    ``fig_or_axes`` may be a list of data Axes (already drawn -- the
    internal fast path used by ``detect_layout_conflicts``), a matplotlib
    Figure, or a ``RecordingFigure`` (drawn + classified here). Returns a
    list of ``Conflict`` objects with ``kind="color"``; ``fraction`` carries
    the measured ΔE. Empty when every labelled series is distinguishable.
    """
    from ._overlap import Conflict

    conflicts: List["Conflict"] = []
    for ax in _resolve_axes(fig_or_axes):
        series = _collect_series(ax)
        n = len(series)
        for i in range(n):
            for j in range(i + 1, n):
                label_a, rgb_a = series[i]
                label_b, rgb_b = series[j]
                if label_a == label_b:
                    continue  # same logical series drawn in parts
                de = delta_e76(rgb_a, rgb_b)
                if de < min_delta_e:
                    conflicts.append(
                        Conflict(
                            role_a="color",
                            role_b="color",
                            label_a=label_a,
                            label_b=label_b,
                            fraction=de,
                            kind="color",
                        )
                    )
    return conflicts


# EOF
