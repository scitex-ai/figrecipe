#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save-time layout-conflict (overlap) detector.

Concept
-------
At save time we (1) enumerate every visual component, each as an object
with a ROLE and a REGION; (2) for every PAIR consult one POLICY table --
"is this role-combination allowed to overlap?"; (3) if a pair is NOT
allowed to overlap AND its regions actually overlap (beyond a tolerance),
emit a save-time WARNING naming both objects and where they collide. "No
conflict detected" means the layout is clean. The rules live in ONE table
(``_FORBIDDEN_PAIRS``), not scattered per element -- add/remove a rule
with a one-line edit there.

Roles
-----
- ``axes``    : each DATA Axes (colorbar + inset/embed axes excluded).
- ``colorbar``: each colorbar's Axes (``cax``).
- ``legend``  : each Axes legend + figure legends.
- ``text``    : every Text artist. BROAD definition -- includes tick
                labels, axis labels, titles, suptitle, ``ax.texts`` and
                ``fig.texts``, not just annotations.
- ``ink``     : non-background DATA pixels per axes (lines / markers /
                collections / images / patches), from ONE "data-only"
                render with all text + legends hidden.
- ``overlay`` : declared sub-panels (inset_axes / embed); allowed to
                overlap anything -- they are intentional overlays.

Detection
---------
- bbox <-> bbox (axes/colorbar/text): ``intersection / min(area_a, area_b)
  > TOL``. Using ``min(area)`` (not union) means a small box fully inside a
  big one trips, while flush/edge-touching panels (shared edge, zero-area
  intersection) do NOT -- so "no whitespace between panels" grids stay silent.
- ``legend <-> ink``: in the data-only raster, the fraction of
  non-background pixels inside the legend bbox ``> TOL`` => the legend covers
  data. Catches occlusion even under an opaque legend facecolor.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.transforms import Bbox

__all__ = [
    "Conflict",
    "detect_layout_conflicts",
    "run_overlap_check",
]

# Default overlap tolerance: an overlap whose fractional coverage is at or
# below this is treated as "touching", not a conflict. ~2% absorbs
# antialiasing fringes and flush/adjacent panels in tight grids.
DEFAULT_TOL = 0.02

# Color distance (max per-channel, 0-255) under which a pixel counts as
# "background". Small, to tolerate antialiasing without swallowing faint ink.
_BG_TOL = 18

# ---------------------------------------------------------------------------
# POLICY TABLE -- the single source of truth.
# A frozenset pair appears here IFF the two roles are FORBIDDEN to overlap.
# Every combination NOT listed is allowed:
#   (text, ink)    -> allowed  (intentional callouts / annotations on data)
#   (ink, ink)     -> allowed  (overlapping lines are normal)
#   (legend, axes) -> allowed  (a legend lives inside its axes)
#   (text, axes)   -> allowed  (labels/titles live around/inside an axes)
#   (overlay, *)   -> allowed  (declared inset/embed overlays)
# ---------------------------------------------------------------------------
_FORBIDDEN_PAIRS = frozenset(
    {
        frozenset({"axes", "axes"}),  # two data panels on top of each other
        frozenset({"colorbar", "axes"}),  # colorbar covering a data panel
        frozenset({"legend", "ink"}),  # legend sitting on data/ink
        frozenset({"text", "text"}),  # colliding text is unreadable
    }
)


def _is_forbidden(role_a: str, role_b: str) -> bool:
    """Return True if this role-combination is forbidden to overlap."""
    return frozenset({role_a, role_b}) in _FORBIDDEN_PAIRS


@dataclass
class _Component:
    """One enumerated visual component: a role, a label, and a region."""

    role: str
    label: str
    bbox: "Bbox"
    parent_ax: Optional["Axes"] = None  # the data Axes this belongs to


@dataclass
class Conflict:
    """A detected, forbidden overlap between two components.

    ``role_a``/``role_b`` are the colliding roles; ``label_a``/``label_b``
    are short human labels (e.g. ``"colorbar"``, ``"axes r0c4"``,
    ``"text 'PAC z-score'"``); ``fraction`` is the overlap measure that
    tripped the rule (intersection/min-area for bbox pairs; non-background
    pixel fraction for ``legend <-> ink``).
    """

    role_a: str
    role_b: str
    label_a: str
    label_b: str
    fraction: float

    def describe(self) -> str:
        """One-line, actionable description of the conflict."""
        return f"{self.label_a} overlaps {self.label_b} ({self.fraction:.0%} coverage)"


# ---------------------------------------------------------------------------
# Classification of Axes
# ---------------------------------------------------------------------------
def _is_colorbar_axes(ax: "Axes") -> bool:
    """True if ``ax`` is a colorbar's cax.

    matplotlib tags a colorbar cax differently depending on how it was made:
    the auto path (``fig.colorbar(im, ax=...)``) sets ``_colorbar_info``,
    while the explicit path (``fig.colorbar(im, cax=...)``) only sets a
    non-None ``_colorbar``. Plain data axes have ``_colorbar = None`` (or no
    such attribute), so checking either marker covers both paths.
    """
    if hasattr(ax, "_colorbar_info"):
        return True
    return getattr(ax, "_colorbar", None) is not None


def _collect_overlay_axes(all_axes: List["Axes"]) -> set:
    """Return the set of inset/embed (overlay) axes.

    figrecipe surfaces managed insets/embeds as matplotlib child axes:
    ``ax.inset_axes(...)`` / embed sub-panels register the new Axes in the
    parent's ``child_axes`` list. Anything that is some other Axes' child is
    a declared overlay. A manual ``fig.add_axes`` on top of a panel is NOT a
    child, so it stays a real ``axes`` and is still checked for conflicts.
    """
    overlays = set()
    for ax in all_axes:
        overlays.update(getattr(ax, "child_axes", []) or [])
    return overlays


def _classify_axes(fig: "Figure") -> Tuple[List["Axes"], List["Axes"], set]:
    """Split figure axes into (data_axes, colorbar_axes, overlay_axes)."""
    all_axes = list(fig.get_axes())
    overlays = _collect_overlay_axes(all_axes)
    data_axes: List["Axes"] = []
    colorbar_axes: List["Axes"] = []
    for ax in all_axes:
        if ax in overlays:
            continue  # declared overlay -- exempt from all conflict checks
        if _is_colorbar_axes(ax):
            colorbar_axes.append(ax)
        else:
            data_axes.append(ax)
    return data_axes, colorbar_axes, overlays


def _axes_grid_label(fig: "Figure", data_axes: List["Axes"]) -> Dict[int, str]:
    """Map id(ax) -> "axes rRcC" using each axes' subplot grid position."""
    labels: Dict[int, str] = {}
    for idx, ax in enumerate(data_axes):
        spec = ax.get_subplotspec() if hasattr(ax, "get_subplotspec") else None
        try:
            labels[id(ax)] = f"axes r{spec.rowspan.start}c{spec.colspan.start}"
        except Exception:
            labels[id(ax)] = f"axes #{idx}"
    return labels


# ---------------------------------------------------------------------------
# Region helpers
# ---------------------------------------------------------------------------
def _valid_bbox(bbox: Optional["Bbox"]) -> bool:
    """A region is usable only if it has strictly positive area."""
    if bbox is None:
        return False
    return bbox.width > 0 and bbox.height > 0


def _window_extent(artist, renderer) -> Optional["Bbox"]:
    """``get_window_extent`` guarded for failures + zero-area; else None."""
    try:
        bbox = artist.get_window_extent(renderer=renderer)
    except Exception:
        return None
    return bbox if _valid_bbox(bbox) else None


def _bbox_overlap_fraction(a: "Bbox", b: "Bbox") -> float:
    """intersection_area / min(area_a, area_b); 0 if they do not overlap."""
    iw = min(a.x1, b.x1) - max(a.x0, b.x0)
    ih = min(a.y1, b.y1) - max(a.y0, b.y0)
    if iw <= 0 or ih <= 0:
        return 0.0
    denom = min(a.width * a.height, b.width * b.height)
    return (iw * ih) / denom if denom > 0 else 0.0


def _text_label(artist, max_len: int = 24) -> str:
    """Short label for a Text artist, e.g. ``text 'PAC z-score'``."""
    try:
        s = artist.get_text()
    except Exception:
        s = ""
    s = (s or "").strip().replace("\n", " ")
    if len(s) > max_len:
        s = s[: max_len - 1] + "…"
    return f"text '{s}'" if s else "text"


# ---------------------------------------------------------------------------
# Enumeration
# ---------------------------------------------------------------------------
def _enumerate_text(fig: "Figure", renderer, overlays: set) -> List[_Component]:
    """Every visible Text artist (broad definition), as components.

    Text owned by overlay (inset/embed) axes is skipped.
    """
    comps: List[_Component] = []
    seen = set()
    for artist in fig.findobj():
        if not any(k.__name__ == "Text" for k in type(artist).__mro__):
            continue
        if id(artist) in seen:
            continue
        seen.add(id(artist))
        if not artist.get_visible():
            continue
        # Skip text owned by an overlay axes.
        owner = getattr(artist, "axes", None)
        if owner is not None and owner in overlays:
            continue
        try:
            if not (artist.get_text() or "").strip():
                continue  # empty text occupies no readable region
        except Exception:
            continue
        bbox = _window_extent(artist, renderer)
        if bbox is not None:
            comps.append(_Component(role="text", label=_text_label(artist), bbox=bbox))
    return comps


def _enumerate_legends(
    fig: "Figure", data_axes: List["Axes"], renderer
) -> List[_Component]:
    """Axes legends + figure legends as components."""
    comps: List[_Component] = []
    for ax in data_axes:
        legend = ax.get_legend()
        if legend is None or not legend.get_visible():
            continue
        bbox = _window_extent(legend, renderer)
        if bbox is not None:
            comps.append(_Component("legend", "legend", bbox, parent_ax=ax))
    for legend in getattr(fig, "legends", []) or []:
        if not legend.get_visible():
            continue
        bbox = _window_extent(legend, renderer)
        if bbox is not None:
            comps.append(_Component("legend", "figure legend", bbox))
    return comps


def _enumerate_bbox_components(
    fig: "Figure",
    data_axes: List["Axes"],
    colorbar_axes: List["Axes"],
    overlays: set,
    renderer,
) -> List[_Component]:
    """All bbox-based components: data axes, colorbars, legends, text."""
    comps: List[_Component] = []
    grid_labels = _axes_grid_label(fig, data_axes)

    for ax in data_axes:
        bbox = _window_extent(ax, renderer)
        if bbox is not None:
            comps.append(
                _Component(
                    role="axes",
                    label=grid_labels.get(id(ax), "axes"),
                    bbox=bbox,
                    parent_ax=ax,
                )
            )

    for ax in colorbar_axes:
        bbox = _window_extent(ax, renderer)
        if bbox is not None:
            comps.append(_Component(role="colorbar", label="colorbar", bbox=bbox))

    comps.extend(_enumerate_legends(fig, data_axes, renderer))
    comps.extend(_enumerate_text(fig, renderer, overlays))
    return comps


# ---------------------------------------------------------------------------
# Data-only raster ("ink" region)
# ---------------------------------------------------------------------------
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

    hidden: List = []
    canvas = fig.canvas
    try:
        for artist in fig.findobj():
            if artist.__class__.__name__ == "Text" and artist.get_visible():
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


# ---------------------------------------------------------------------------
# Pairwise detection
# ---------------------------------------------------------------------------
# A legend/text vs its OWN parent axes is never a conflict: the policy table
# lists neither (legend, axes) nor (text, axes), so _is_forbidden() drops
# those pairs before any geometry runs. ``parent_ax`` is kept only to scope
# the legend<->ink check.
def _detect_bbox_conflicts(comps: List[_Component], tol: float) -> List[Conflict]:
    """Forbidden bbox<->bbox overlaps (axes/axes, colorbar/axes, text/text)."""
    conflicts: List[Conflict] = []
    n = len(comps)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = comps[i], comps[j]
            if not _is_forbidden(a.role, b.role):
                continue
            frac = _bbox_overlap_fraction(a.bbox, b.bbox)
            if frac > tol:
                conflicts.append(Conflict(a.role, b.role, a.label, b.label, frac))
    return conflicts


def _detect_legend_ink_conflicts(
    legends: List[_Component],
    ink_mask,
    height: int,
    tol: float,
) -> List[Conflict]:
    """Forbidden legend<->ink overlaps via the data-only raster."""
    conflicts: List[Conflict] = []
    for legend in legends:
        frac = _ink_fraction_in_bbox(ink_mask, height, legend.bbox)
        if frac > tol:
            conflicts.append(Conflict("legend", "ink", legend.label, "data/ink", frac))
    return conflicts


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def detect_layout_conflicts(
    fig,
    style: Optional[dict] = None,
    tol: float = DEFAULT_TOL,
) -> List[Conflict]:
    """Enumerate components and report forbidden, real overlaps.

    ``fig`` may be a ``RecordingFigure`` (has ``.fig``, unwrapped) or a
    matplotlib Figure. ``style`` is the recipe style dict; only
    ``style['theme_colors']`` is read, for the ink-mask background color
    (white when absent). ``tol`` is the fractional overlap tolerance.
    Returns an empty list when the layout is clean.
    """
    mpl_fig = getattr(fig, "fig", fig)

    canvas = getattr(mpl_fig, "canvas", None)
    if canvas is None:
        return []
    try:
        canvas.draw()
        renderer = mpl_fig._get_renderer()
    except Exception:
        return []

    data_axes, colorbar_axes, overlays = _classify_axes(mpl_fig)

    comps = _enumerate_bbox_components(
        mpl_fig, data_axes, colorbar_axes, overlays, renderer
    )
    conflicts = _detect_bbox_conflicts(comps, tol)

    legends = [c for c in comps if c.role == "legend"]
    if legends:
        rendered = _render_ink_mask(mpl_fig, style)
        if rendered is not None:
            ink_mask, height = rendered
            conflicts.extend(
                _detect_legend_ink_conflicts(legends, ink_mask, height, tol)
            )

    return conflicts


def run_overlap_check(
    fig,
    style: Optional[dict] = None,
    tol: float = DEFAULT_TOL,
) -> List[Conflict]:
    """Detect conflicts; if any, emit ONE summarizing ``UserWarning``.

    Mirrors the save-time warning hooks in ``_api/_save.py``: never raises,
    only warns. Returns the conflict list for callers to inspect.
    """
    conflicts = detect_layout_conflicts(fig, style=style, tol=tol)
    if conflicts:
        lines = "\n  ".join(c.describe() for c in conflicts)
        warnings.warn(
            "Layout conflict detected: components overlap that should not.\n"
            f"  {lines}\n"
            "  (Move/resize the offending element, or pass a larger figure "
            "/ tighter layout.)",
            UserWarning,
            stacklevel=2,
        )
    return conflicts


# EOF
