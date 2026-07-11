#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Record ``bar_label`` + ``secondary_xaxis``/``secondary_yaxis`` so they
round-trip through a recipe.

``bar_label`` draws Annotations anchored at bar tops (``xy`` in data coords +
a points offset), and figrecipe already records ``annotate``. So we FREEZE each
label into a recorded ``annotate()`` call (solve-then-freeze, like
scatter_labels) — no live BarContainer in the recipe, byte-identical replay.

``secondary_xaxis``/``secondary_yaxis`` with a plain ``location`` (mirroring the
primary axis) is recorded by location. With custom forward/inverse transform
CALLABLES it cannot be serialized, so it is drawn but WARNS (never silently
vanishes on reproduce()).
"""

from __future__ import annotations

import warnings


def build_bar_label_wrapper(recording_axes):
    """Wrapper for ``ax.bar_label`` that freezes each label into a recorded
    ``annotate`` so the labels reproduce without the live BarContainer."""

    def bar_label(*args, id=None, track=True, **kwargs):
        anns = recording_axes._ax.bar_label(*args, **kwargs)
        if not (recording_axes._track and track):
            return anns
        frozen = []
        for ann in anns:
            xy = (float(ann.xy[0]), float(ann.xy[1]))
            xytext = (
                tuple(float(v) for v in ann.xyann) if ann.xyann is not None else None
            )
            ann.remove()  # drop the raw annotation; re-add via the recorded path
            frozen.append(
                recording_axes.annotate(
                    ann.get_text(),
                    xy=xy,
                    xytext=xytext,
                    textcoords=ann.anncoords,
                    ha=ann.get_ha(),
                    va=ann.get_va(),
                    rotation=float(ann.get_rotation()),
                )
            )
        return frozen

    return bar_label


def build_secondary_axis_wrapper(recording_axes, method_name: str):
    """Wrapper for ``ax.secondary_xaxis``/``ax.secondary_yaxis``: record the
    plain-``location`` case; warn when custom transform functions are given."""
    method = getattr(recording_axes._ax, method_name)

    def secondary_axis(location, *args, functions=None, id=None, track=True, **kwargs):
        recording = recording_axes._track and track
        if functions is not None:
            result = method(location, *args, functions=functions, **kwargs)
            if recording:
                warnings.warn(
                    f"figrecipe: ax.{method_name}(..., functions=...) is drawn but "
                    f"NOT recorded (transform callables are not recipe-serializable), "
                    f"so it will be absent when the recipe is reproduced.",
                    UserWarning,
                    stacklevel=2,
                )
            return result
        result = method(location, *args, **kwargs)
        if recording:
            recording_axes._recorder.record_call(
                ax_position=recording_axes._position,
                method_name=method_name,
                args=(location,),
                kwargs={},
                call_id=id,
            )
        return result

    return secondary_axis


__all__ = ["build_bar_label_wrapper", "build_secondary_axis_wrapper"]

# EOF
