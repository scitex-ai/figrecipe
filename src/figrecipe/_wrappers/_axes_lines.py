#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Record ``ax.add_line()`` / ``ax.add_artist()`` / ``ax.add_collection()``.

A bare artist object is live matplotlib state, so it is decomposed into a
YAML-serializable spec at record time and rebuilt on replay (see
``figrecipe/_reproducer/_replay_lines.py``). Artists that are not a ``Line2D``
(add_line/add_artist) or ``LineCollection`` (add_collection) FAIL LOUD at call
time rather than being silently dropped (which would fail save-time
reproducibility): patches belong to ``add_patch``, anything else needs its
own spec branch.
"""

from typing import Any, Dict, List

import matplotlib.colors as mcolors
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

from ._axes_patches import _serialize_transform

SUPPORTED_LINE_TYPES = ("Line2D",)
SUPPORTED_COLLECTION_TYPES = ("LineCollection",)

_LINE_STYLE_ATTRS = (
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
)


def _hex_or_none(value):
    if value is None:
        return None
    try:
        return mcolors.to_hex(value, keep_alpha=True)
    except (ValueError, TypeError):
        return value


def _line_style_of(line) -> Dict[str, Any]:
    style: Dict[str, Any] = {}
    for attr in _LINE_STYLE_ATTRS:
        getter = getattr(line, f"get_{attr}", None)
        if getter is None:
            continue
        value = getter()
        if value is None or value == "None":
            continue
        if attr in ("color", "markerfacecolor", "markeredgecolor"):
            value = _hex_or_none(value)
        elif attr in ("linewidth", "markersize", "markeredgewidth", "zorder"):
            value = float(value)
        style[attr] = value
    style["transform"] = _serialize_transform(line)
    return style


def _float_list(values, what: str) -> List[float]:
    try:
        return [float(v) for v in values]
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"figrecipe cannot record {what} with non-numeric data for "
            f"reproduction (it would not round-trip). Plot numeric data, or "
            f"convert it before drawing."
        ) from exc


def extract_line_spec(line) -> Dict[str, Any]:
    """Decompose a Line2D into a serializable spec. FAIL LOUD otherwise."""
    if not isinstance(line, Line2D):
        raise ValueError(
            f"figrecipe cannot record {type(line).__name__!r} via add_line for "
            f"reproduction (it would be dropped on replay). Supported: "
            f"{', '.join(SUPPORTED_LINE_TYPES)}. Patches belong to add_patch."
        )
    return {
        "type": "Line2D",
        "xdata": _float_list(line.get_xdata(), "Line2D xdata"),
        "ydata": _float_list(line.get_ydata(), "Line2D ydata"),
        "style": _line_style_of(line),
    }


def extract_collection_spec(coll) -> Dict[str, Any]:
    """Decompose a LineCollection into a serializable spec. FAIL LOUD otherwise."""
    if not isinstance(coll, LineCollection):
        raise ValueError(
            f"figrecipe cannot record {type(coll).__name__!r} via add_collection "
            f"for reproduction (it would be dropped on replay). Supported: "
            f"{', '.join(SUPPORTED_COLLECTION_TYPES)}."
        )
    segments = [
        [[float(x), float(y)] for x, y in seg] for seg in coll.get_segments()
    ]
    colors = [_hex_or_none(c) for c in coll.get_colors()]
    linewidths = [float(w) for w in coll.get_linewidths()]
    linestyles = [
        [offset, list(dashes) if dashes is not None else None]
        for offset, dashes in coll.get_linestyle()
    ]
    return {
        "type": "LineCollection",
        "segments": segments,
        "colors": colors,
        "linewidths": linewidths,
        "linestyles": linestyles,
        "style": {"transform": _serialize_transform(coll)},
    }


def _record_spec_call(recording_axes, name, spec, result, call_id):
    from ._axes_helpers import record_call_with_color_capture

    record_call_with_color_capture(
        recording_axes._recorder,
        recording_axes._position,
        name,
        (),
        {"line_spec" if name != "add_collection" else "collection_spec": spec},
        result,
        call_id,
        recording_axes._result_refs,
        recording_axes._RESULT_REFERENCING_METHODS,
        recording_axes._RESULT_REFERENCEABLE_METHODS,
        recording_axes._artist_refs,
    )


def build_add_line_wrapper(recording_axes):
    """Build the recording wrapper for ``RecordingAxes.add_line``."""

    def add_line(line, *, id=None, track=True, **kwargs):
        result = recording_axes._ax.add_line(line)
        if recording_axes._track and track:
            # extract_line_spec FAILS LOUD here on unsupported types, so the
            # author learns at call time that the artist will not round-trip.
            _record_spec_call(
                recording_axes, "add_line", extract_line_spec(line), result, id
            )
        return result

    return add_line


def build_add_artist_wrapper(recording_axes):
    """Build the recording wrapper for ``RecordingAxes.add_artist``."""

    def add_artist(artist, *, id=None, track=True, **kwargs):
        result = recording_axes._ax.add_artist(artist)
        if recording_axes._track and track:
            _record_spec_call(
                recording_axes,
                "add_artist",
                extract_line_spec(artist),
                result,
                id,
            )
        return result

    return add_artist


def build_add_collection_wrapper(recording_axes):
    """Build the recording wrapper for ``RecordingAxes.add_collection``."""

    def add_collection(coll, *, id=None, track=True, **kwargs):
        result = recording_axes._ax.add_collection(coll)
        if recording_axes._track and track:
            _record_spec_call(
                recording_axes,
                "add_collection",
                extract_collection_spec(coll),
                result,
                id,
            )
        return result

    return add_collection


__all__ = [
    "extract_line_spec",
    "extract_collection_spec",
    "build_add_line_wrapper",
    "build_add_artist_wrapper",
    "build_add_collection_wrapper",
    "SUPPORTED_LINE_TYPES",
    "SUPPORTED_COLLECTION_TYPES",
]
