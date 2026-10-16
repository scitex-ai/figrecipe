#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replay recorded ``add_line`` / ``add_artist`` / ``add_collection`` calls.

Counterpart to ``figrecipe/_wrappers/_axes_lines.py`` (the record side):
rebuild the artist from its spec and add it to the replay axes.
"""

from typing import Any, Dict

from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

from ._replay_patches import _resolve_transform


def _apply_line_style(line, style: Dict[str, Any]) -> None:
    for attr in (
        "color",
        "linewidth",
        "linestyle",
        "marker",
        "markersize",
        "markerfacecolor",
        "markeredgecolor",
        "markeredgewidth",
        "drawstyle",
        "alpha",
        "zorder",
    ):
        if attr in style:
            getattr(line, f"set_{attr}")(style[attr])


def reconstruct_line(spec: Dict[str, Any]):
    """Rebuild a matplotlib Line2D from a recorded spec."""
    if spec.get("type") != "Line2D":
        raise ValueError(
            f"figrecipe cannot reproduce line type {spec.get('type')!r} "
            f"(recipe written by an incompatible figrecipe version)."
        )
    line = Line2D(spec["xdata"], spec["ydata"])
    _apply_line_style(line, spec.get("style", {}))
    return line


def reconstruct_collection(spec: Dict[str, Any]):
    """Rebuild a matplotlib LineCollection from a recorded spec."""
    if spec.get("type") != "LineCollection":
        raise ValueError(
            f"figrecipe cannot reproduce collection type {spec.get('type')!r} "
            f"(recipe written by an incompatible figrecipe version)."
        )
    coll = LineCollection(
        spec["segments"],
        colors=spec.get("colors") or None,
        linewidths=spec.get("linewidths") or None,
        linestyles=[
            (offset, tuple(dashes) if dashes is not None else None)
            for offset, dashes in spec.get("linestyles", [])
        ]
        or None,
    )
    return coll


def _replay_spec_call(ax, call, key: str, reconstruct, adder: str):
    spec = call.kwargs.get(key)
    if spec is None:
        raise ValueError(f"{adder} call {call.id!r} is missing {key}")
    artist = reconstruct(spec)
    transform = spec.get("style", {}).get("transform")
    if transform:
        artist.set_transform(_resolve_transform(transform, ax))
    return getattr(ax, adder)(artist)


def replay_add_line_call(ax, call):
    """Replay a recorded ``add_line`` call."""
    return _replay_spec_call(ax, call, "line_spec", reconstruct_line, "add_line")


def replay_add_artist_call(ax, call):
    """Replay a recorded ``add_artist`` call."""
    return _replay_spec_call(
        ax, call, "line_spec", reconstruct_line, "add_artist"
    )


def replay_add_collection_call(ax, call):
    """Replay a recorded ``add_collection`` call."""
    return _replay_spec_call(
        ax, call, "collection_spec", reconstruct_collection, "add_collection"
    )


__all__ = [
    "replay_add_line_call",
    "replay_add_artist_call",
    "replay_add_collection_call",
    "reconstruct_line",
    "reconstruct_collection",
]
