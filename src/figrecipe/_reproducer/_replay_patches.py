#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replay a recorded ``add_patch`` call by rebuilding the patch from its spec.

Counterpart to ``figrecipe/_wrappers/_axes_patches.py`` (the record side).
"""

from typing import Any, Dict

import matplotlib.patches as mpatches


def _resolve_transform(marker: str, ax):
    """Resolve a serialized transform marker to the target axes' transform."""
    if marker == "axes":
        return ax.transAxes
    if marker == "figure":
        return ax.figure.transFigure
    return ax.transData


def reconstruct_patch(spec: Dict[str, Any]):
    """Rebuild a matplotlib patch from a recorded spec (geometry only)."""
    ptype = spec.get("type")
    if ptype == "Rectangle":
        return mpatches.Rectangle(
            tuple(spec["xy"]),
            spec["width"],
            spec["height"],
            angle=spec.get("angle", 0.0),
        )
    if ptype == "Circle":
        return mpatches.Circle(tuple(spec["center"]), radius=spec["radius"])
    if ptype == "Ellipse":
        return mpatches.Ellipse(
            tuple(spec["center"]),
            width=spec["width"],
            height=spec["height"],
            angle=spec.get("angle", 0.0),
        )
    if ptype == "Polygon":
        return mpatches.Polygon(spec["xy"], closed=spec.get("closed", True))
    if ptype == "FancyArrowPatch":
        return mpatches.FancyArrowPatch(
            tuple(spec["posA"]),
            tuple(spec["posB"]),
            arrowstyle=spec.get("arrowstyle", "-|>"),
            connectionstyle=spec.get("connectionstyle", "arc3"),
            mutation_scale=spec.get("mutation_scale", 1.0),
        )
    raise ValueError(
        f"figrecipe cannot reproduce patch type {ptype!r} (recipe written by an "
        f"incompatible figrecipe version)."
    )


def replay_add_patch_call(ax, call):
    """Reconstruct the patch from ``call`` and add it to ``ax``."""
    spec = call.kwargs.get("patch_spec")
    if not spec:
        raise ValueError(f"add_patch call {call.id!r} is missing patch_spec")

    patch = reconstruct_patch(spec)

    style = dict(spec.get("style", {}))
    # Set the transform before add_patch so matplotlib does not override it
    # with transData (add_patch only sets transData when none is set).
    transform_marker = style.pop("transform", None)
    if transform_marker is not None:
        patch.set_transform(_resolve_transform(transform_marker, ax))
    for key, value in style.items():
        setter = getattr(patch, f"set_{key}", None)
        if setter is not None:
            setter(value)

    return ax.add_patch(patch)


__all__ = ["replay_add_patch_call", "reconstruct_patch"]
