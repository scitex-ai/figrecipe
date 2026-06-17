#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Serialize matplotlib Patch artists for the recipe.

``ax.add_patch`` takes a live ``matplotlib.patches.Patch`` artist, which is not
serialisable to YAML. To make ``add_patch`` reproduce, we capture each patch's
*class + geometry + style* as plain primitives here; the reproducer
(``_reproducer/_replay_patch.py``) reconstructs an equivalent patch from this
descriptor.

Common analytic shapes (Rectangle, Circle, Ellipse, Polygon) are captured by
their constructor geometry so the recipe is human-readable. Anything else
(FancyBboxPatch, Wedge, Arc, arbitrary patches) falls back to its transformed
path vertices/codes, replayed as a ``PathPatch`` — geometrically faithful for
any patch type.
"""

from typing import Any, Dict, List, Optional

import matplotlib.patches as mpatches


def _color_to_list(color: Any) -> Optional[List[float]]:
    """An RGBA artist colour -> list of 4 floats (alpha folded in), or None.

    matplotlib has already folded any ``set_alpha`` into the returned RGBA, so
    we store the colour as-is and do NOT serialise a separate ``alpha`` (which
    would double-apply on replay).
    """
    if color is None:
        return None
    try:
        return [float(c) for c in color]
    except TypeError:
        return None


def _linestyle_repr(linestyle: Any) -> Any:
    """Patch linestyle -> a YAML-safe form (str, or [offset, dashes] list)."""
    if isinstance(linestyle, str):
        return linestyle
    # matplotlib returns the dash form (offset, onoffseq); onoffseq is None for
    # solid. Keep it as a list so the reproducer can rebuild the tuple.
    try:
        offset, seq = linestyle
        return [offset, (list(seq) if seq is not None else None)]
    except (TypeError, ValueError):
        return "solid"


def _common_props(patch: mpatches.Patch) -> Dict[str, Any]:
    """Capture the style props shared by every Patch."""
    return {
        "facecolor": _color_to_list(patch.get_facecolor()),
        "edgecolor": _color_to_list(patch.get_edgecolor()),
        "linewidth": float(patch.get_linewidth()),
        "linestyle": _linestyle_repr(patch.get_linestyle()),
        "hatch": patch.get_hatch(),
        "fill": bool(patch.get_fill()),
        "zorder": float(patch.get_zorder()),
    }


def serialize_patch(patch: mpatches.Patch) -> Dict[str, Any]:
    """Capture a Patch as a {patch_class, geom, props} descriptor.

    The descriptor is plain primitives (str / float / list / dict) so it passes
    the recorder's serialisability check unchanged and round-trips through YAML.
    """
    props = _common_props(patch)

    # FancyBboxPatch subclasses are NOT Rectangle; check Rectangle first but
    # exclude the fancy variant so it takes the path fallback (its rounded
    # outline is not a plain rectangle).
    if isinstance(patch, mpatches.Rectangle) and not isinstance(
        patch, mpatches.FancyBboxPatch
    ):
        geom = {
            "xy": [float(patch.get_x()), float(patch.get_y())],
            "width": float(patch.get_width()),
            "height": float(patch.get_height()),
            "angle": float(patch.get_angle()),
        }
        return {"patch_class": "Rectangle", "geom": geom, "props": props}

    if isinstance(patch, mpatches.Circle):
        cx, cy = patch.get_center()
        geom = {"xy": [float(cx), float(cy)], "radius": float(patch.get_radius())}
        return {"patch_class": "Circle", "geom": geom, "props": props}

    if isinstance(patch, mpatches.Ellipse):
        cx, cy = patch.get_center()
        geom = {
            "xy": [float(cx), float(cy)],
            "width": float(patch.get_width()),
            "height": float(patch.get_height()),
            "angle": float(patch.get_angle()),
        }
        return {"patch_class": "Ellipse", "geom": geom, "props": props}

    if isinstance(patch, mpatches.Polygon):
        geom = {"xy": [[float(x), float(y)] for x, y in patch.get_xy()]}
        return {"patch_class": "Polygon", "geom": geom, "props": props}

    # Generic fallback: any patch -> its outline path in data coords, replayed
    # as a PathPatch. transform the unit path through the patch transform so the
    # stored vertices are already in the axes' data space.
    tpath = patch.get_patch_transform().transform_path(patch.get_path())
    codes = tpath.codes
    geom = {
        "path_vertices": [[float(x), float(y)] for x, y in tpath.vertices],
        "path_codes": ([int(c) for c in codes] if codes is not None else None),
    }
    return {"patch_class": "PathPatch", "geom": geom, "props": props}


__all__ = ["serialize_patch"]

# EOF
