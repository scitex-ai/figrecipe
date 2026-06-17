#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replay a recorded ``add_patch`` call.

Reconstructs a ``matplotlib.patches.Patch`` from the {patch_class, geom, props}
descriptor written by ``_wrappers/_axes_patch.serialize_patch`` and adds it to
the reproduced axes. Mirrors the live ``add_patch`` so the patch reproduces
pixel-for-pixel.
"""

from typing import Any, Dict

import matplotlib.patches as mpatches
from matplotlib.path import Path as MplPath


def _props_to_kwargs(props: Dict[str, Any]) -> Dict[str, Any]:
    """Turn the serialised style props back into Patch constructor kwargs."""
    kwargs: Dict[str, Any] = {}

    facecolor = props.get("facecolor")
    if facecolor is not None:
        kwargs["facecolor"] = tuple(facecolor)
    edgecolor = props.get("edgecolor")
    if edgecolor is not None:
        kwargs["edgecolor"] = tuple(edgecolor)

    for key in ("linewidth", "hatch", "fill", "zorder"):
        if props.get(key) is not None:
            kwargs[key] = props[key]

    linestyle = props.get("linestyle")
    if isinstance(linestyle, str):
        kwargs["linestyle"] = linestyle
    elif isinstance(linestyle, (list, tuple)) and len(linestyle) == 2:
        offset, seq = linestyle
        kwargs["linestyle"] = "solid" if seq is None else (offset, tuple(seq))

    return kwargs


def replay_add_patch_call(ax, call):
    """Reconstruct and add the patch recorded in ``call``.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The reproduced axes to add the patch to.
    call : CallRecord
        The recorded call; ``call.kwargs`` holds the patch descriptor.
    """
    descriptor = call.kwargs or {}
    patch_class = descriptor.get("patch_class")
    geom = descriptor.get("geom", {})
    kwargs = _props_to_kwargs(descriptor.get("props", {}))

    if patch_class == "Rectangle":
        patch = mpatches.Rectangle(
            tuple(geom["xy"]),
            geom["width"],
            geom["height"],
            angle=geom.get("angle", 0.0),
            **kwargs,
        )
    elif patch_class == "Circle":
        patch = mpatches.Circle(tuple(geom["xy"]), geom["radius"], **kwargs)
    elif patch_class == "Ellipse":
        patch = mpatches.Ellipse(
            tuple(geom["xy"]),
            geom["width"],
            geom["height"],
            angle=geom.get("angle", 0.0),
            **kwargs,
        )
    elif patch_class == "Polygon":
        patch = mpatches.Polygon(geom["xy"], closed=True, **kwargs)
    else:  # "PathPatch" generic fallback: vertices/codes already in data coords
        vertices = geom.get("path_vertices", [])
        codes = geom.get("path_codes")
        path = MplPath(vertices, codes) if codes is not None else MplPath(vertices)
        patch = mpatches.PathPatch(path, **kwargs)

    return ax.add_patch(patch)


__all__ = ["replay_add_patch_call"]

# EOF
