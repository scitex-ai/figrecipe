#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-call replay dispatch for figure reproduction.

``_replay_call`` maps one recorded ``CallRecord`` back to a matplotlib call:
special handlers for the figrecipe/seaborn/scitex constructs that can't be
re-invoked by a plain ``getattr(ax, name)``, then a generic matplotlib dispatch
for everything else. Extracted from ``_core.py`` (which kept the figure-level
orchestration) to stay under the module line limit.
"""

from typing import Any, Dict, Optional

from matplotlib.axes import Axes

from .._recorder import CallRecord


def _maybe_parse_datetime(value: Any) -> Any:
    """Parse an ISO datetime string to a datetime (for datetime-axis limits).

    Recipes record datetime axis limits as ISO strings; matplotlib cannot
    convert a raw string to axis units on replay. Returns a ``datetime`` when
    ``value`` parses as one, otherwise returns ``value`` unchanged.
    """
    if not isinstance(value, str):
        return value
    try:
        from datetime import datetime

        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return value


def _replay_call(
    ax: Axes, call: CallRecord, result_cache: Optional[Dict[str, Any]] = None
) -> Any:
    """Replay a single call on an axes.

    Parameters
    ----------
    ax : Axes
        The matplotlib axes.
    call : CallRecord
        The call to replay.
    result_cache : dict, optional
        Cache mapping call_id -> result for resolving references.

    Returns
    -------
    Any
        Result of the matplotlib call.
    """
    if result_cache is None:
        result_cache = {}

    method_name = call.function

    # Special method handlers
    if method_name.startswith("sns."):
        from ._seaborn import replay_seaborn_call

        return replay_seaborn_call(ax, call)
    if method_name == "boxplot":
        from ._boxplot import replay_boxplot_call

        return replay_boxplot_call(ax, call)
    if method_name == "violinplot":
        from ._violin import replay_violinplot_call

        return replay_violinplot_call(ax, call)
    if method_name == "joyplot":
        from ._custom_plots import replay_joyplot_call

        return replay_joyplot_call(ax, call)
    if method_name == "swarmplot":
        from ._custom_plots import replay_swarmplot_call

        return replay_swarmplot_call(ax, call)
    if method_name == "stat_annotation":
        from .._wrappers._stat_annotation import draw_stat_annotation

        kwargs = call.kwargs.copy()
        x1, x2 = kwargs.pop("x1", 0), kwargs.pop("x2", 1)
        return draw_stat_annotation(ax, x1, x2, **kwargs)
    if method_name == "graph":
        from ._replay_graph import replay_graph_call

        return replay_graph_call(ax, call)
    if method_name in ("diagram", "schematic"):
        from ._replay_diagram import replay_diagram_native_call

        return replay_diagram_native_call(ax, call)
    if method_name == "add_patch":
        from ._replay_patch import replay_add_patch_call

        return replay_add_patch_call(ax, call)
    if method_name == "legend":
        from ._legend import replay_legend_call

        return replay_legend_call(ax, call, result_cache)
    if method_name == "stem":
        from ._stem import replay_stem_call

        return replay_stem_call(ax, call)
    if method_name == "rotate_labels":
        # figrecipe tick-label rotation: a styles helper, not an mpl axes method,
        # so getattr(ax, "rotate_labels") fails on the raw replay axes. Dispatch
        # to the helper so the rotation (and the tick re-nicing it applies) is
        # reproduced -- otherwise labels stay horizontal + limits drift.
        from ..styles._axis_helpers import rotate_labels as _rotate_labels

        kw = {k: call.kwargs.get(k) for k in ("x", "y", "x_ha", "y_ha", "auto_adjust")}
        try:
            _rotate_labels(ax, **{k: v for k, v in kw.items() if v is not None})
        except Exception:
            pass
        return None
    if method_name.startswith("stx_"):
        # figrecipe scitex-compat plot methods are functions taking a raw mpl
        # axes; a plain getattr(ax, name) fails on raw axes (e.g. mm-compose
        # add_axes panels), silently dropping the plot + its make_axes_locatable
        # marginals. Dispatch to the compat function so it reconstructs fully.
        from ._scitex import replay_stx_call

        return replay_stx_call(ax, call, result_cache)

    method = getattr(ax, method_name, None)

    if method is None:
        # Method not found, skip
        return None

    # Reconstruct args
    from ._reconstruct import reconstruct_kwargs, reconstruct_value

    args = []
    for arg_data in call.args:
        value = reconstruct_value(arg_data, result_cache)
        args.append(value)

    # Get kwargs and reconstruct arrays
    kwargs = reconstruct_kwargs(call.kwargs)

    # Axis-limit methods on a datetime axis recorded their bounds as ISO
    # datetime strings; matplotlib can't convert a raw string to axis units on
    # replay (raises "Failed to convert value(s) to axis units"). Parse such
    # strings back to datetime so the recorded limits are reapplied.
    if method_name in ("set_xlim", "set_ylim", "axvline", "axhline"):
        args = [_maybe_parse_datetime(a) for a in args]
        kwargs = {k: _maybe_parse_datetime(v) for k, v in kwargs.items()}

    # Handle special transform markers
    if "transform" in kwargs:
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

    # Fix fill_between: 'color' overrides 'edgecolor', use 'facecolor' instead
    if method_name in ("fill_between", "fill_betweenx"):
        if "color" in kwargs and "edgecolor" in kwargs:
            kwargs["facecolor"] = kwargs.pop("color")

    # Call the method
    try:
        return method(*args, **kwargs)
    except Exception as e:
        # Log warning but continue
        import warnings

        warnings.warn(f"Failed to replay {method_name}: {e}")
        return None


__all__ = ["_replay_call", "_maybe_parse_datetime"]

# EOF
