#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Generic argument fixups applied to a recorded call before replay.

Each fixup repairs one way a serialized recipe can fail to replay verbatim:
values that lost their type on the way to YAML, transform objects that could
only be stored as markers, a kwarg whose matplotlib meaning shifted, and legacy
tick recipes whose positions and labels disagree in count.

All of them return :class:`ReplayArgs`, so a fixup can also say "do not make
this call at all" — see ``_tick_heal`` for the case that needs it.
"""

from typing import Any, Dict, List, Tuple

from ._replay_action import ReplayArgs


def _coerce_axis_values(
    method_name: str, args: List[Any], kwargs: Dict[str, Any]
) -> Tuple[List[Any], Dict[str, Any]]:
    """Restore numeric/datetime types that a recipe stored as strings.

    These methods are inherently numeric/datetime, but a recipe may store the
    value as a string -- an ISO datetime (datetime axes) or a stringified
    number like '0' from stale recipes. matplotlib can't convert a raw string
    to axis units on replay ("Failed to convert value(s) to axis units"), so
    coerce it back to datetime/float before reapplying the recorded value.
    """
    from ._axis_coerce import coerce_axis_value

    if method_name in ("set_xlim", "set_ylim", "axvline", "axhline"):
        args = [coerce_axis_value(a) for a in args]
        kwargs = {k: coerce_axis_value(v) for k, v in kwargs.items()}
    return args, kwargs


def _resolve_transform_marker(ax: Any, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Turn a recorded ``transform`` marker back into a real transform."""
    if "transform" not in kwargs:
        return kwargs

    transform_val = kwargs["transform"]
    if transform_val == "axes":
        kwargs["transform"] = ax.transAxes
    elif transform_val == "data":
        kwargs["transform"] = ax.transData
    elif transform_val == "figure":
        kwargs["transform"] = ax.figure.transFigure
    elif isinstance(transform_val, str):
        # A non-marker stringified transform (e.g. a Bbox/blended transform
        # that the recorder could not serialize as a clean marker). Passing
        # the raw string to matplotlib raises
        # "'str' object has no attribute 'contains_branch_seperately'".
        # Map an axes-bbox transform back to ax.transAxes (the common case,
        # e.g. scalebars drawn in axes fraction); otherwise drop it so the
        # element still draws in the default (data) transform.
        low = transform_val.replace("\n", " ").replace(" ", "")
        if "BboxTransformTo" in transform_val and (
            "x1=1.0" in low or "Affine2D().scale" in transform_val
        ):
            kwargs["transform"] = ax.transAxes
        else:
            kwargs.pop("transform")
    return kwargs


def apply_arg_fixups(
    ax: Any, method_name: str, args: List[Any], kwargs: Dict[str, Any]
) -> ReplayArgs:
    """Repair one recorded call's arguments, or refuse to replay it.

    Returns :class:`ReplayArgs`; the caller MUST honour ``action`` rather than
    only reading ``args``/``kwargs``.
    """
    args, kwargs = _coerce_axis_values(method_name, args, kwargs)

    # Axis scale (set_xscale / set_yscale) replays as a generic decoration; warn
    # loudly on an unsupported scale name instead of degrading silently to linear.
    if method_name in ("set_xscale", "set_yscale"):
        from ._axis_scale import warn_if_unsupported_scale

        warn_if_unsupported_scale(method_name, args)

    kwargs = _resolve_transform_marker(ax, kwargs)

    # Fix fill_between: 'color' overrides 'edgecolor', use 'facecolor' instead
    if method_name in ("fill_between", "fill_betweenx"):
        if "color" in kwargs and "edgecolor" in kwargs:
            kwargs["facecolor"] = kwargs.pop("color")

    # Legacy recipes whose tick positions/labels counts diverge. This is the one
    # fixup that can return SKIP: labels with no authored positions are dropped
    # rather than pinned onto matplotlib's automatic ticks, because a mislabeled
    # axis reads as data while a bare one reads as broken.
    if method_name in (
        "set_xticks",
        "set_yticks",
        "set_xticklabels",
        "set_yticklabels",
    ):
        from ._tick_heal import heal_tick_call

        return heal_tick_call(ax, method_name, tuple(args), kwargs)

    return ReplayArgs.apply(args=tuple(args), kwargs=kwargs)


__all__ = [
    "apply_arg_fixups",
]
