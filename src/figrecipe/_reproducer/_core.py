#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Core reproduction logic for figure reproduction."""

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
from matplotlib.axes import Axes

from .._recorder import CallRecord, FigureRecord
from .._serializer import load_recipe
from .._utils._bundle import resolve_recipe_path
from .._utils._grid import parse_grid_id
from ._colorbars import _replay_colorbars


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


def reproduce(
    path: Union[str, Path],
    calls: Optional[List[str]] = None,
    skip_decorations: bool = False,
    apply_overrides: bool = True,
):
    """Reproduce a figure from a recipe file.

    Parameters
    ----------
    path : str or Path
        Path to recipe. Supports multiple formats:
        - .yaml/.yml file: Direct recipe file
        - .png/.jpg/etc: Image with associated .yaml
        - Directory: Bundle containing recipe.yaml
        - .zip: ZIP archive containing recipe.yaml
    calls : list of str, optional
        If provided, only reproduce these specific call IDs.
    skip_decorations : bool
        If True, skip decoration calls (labels, legends, etc.).
    apply_overrides : bool
        If True (default), apply .overrides.json if it exists.
        This preserves manual GUI editor changes.

    Returns
    -------
    fig : RecordingFigure
        Reproduced figure (same type as subplots() returns).
    axes : RecordingAxes or ndarray of RecordingAxes
        Reproduced axes (single if 1x1, otherwise numpy array).

    Examples
    --------
    >>> import figrecipe as fr
    >>> fig, ax = fr.reproduce("experiment_001.yaml")
    >>> fig, ax = fr.reproduce("experiment_001.png")  # Also works
    >>> fig, ax = fr.reproduce("figure_bundle/")      # Directory bundle
    >>> fig, ax = fr.reproduce("figure.zip")          # ZIP bundle
    >>> plt.show()
    """
    # Resolve path to actual recipe YAML (handles directories, ZIPs, images)
    path, temp_dir = resolve_recipe_path(path)

    try:
        record = load_recipe(path)

        # Check for override file and merge if exists
        if apply_overrides:
            overrides_path = path.with_suffix(".overrides.json")
            if overrides_path.exists():
                import json

                with open(overrides_path) as f:
                    data = json.load(f)

                # Apply style overrides
                manual_overrides = data.get("manual_overrides", {})
                if manual_overrides:
                    if record.style is None:
                        record.style = {}
                    record.style.update(manual_overrides)

                # Apply call overrides (kwargs changes from editor)
                call_overrides = data.get("call_overrides", {})
                if call_overrides:
                    for ax_key, ax_record in record.axes.items():
                        for call in ax_record.calls:
                            if call.id in call_overrides:
                                call.kwargs.update(call_overrides[call.id])

        return reproduce_from_record(
            record, calls=calls, skip_decorations=skip_decorations
        )
    finally:
        if temp_dir is not None and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def reproduce_from_record(
    record: FigureRecord,
    calls: Optional[List[str]] = None,
    skip_decorations: bool = False,
):
    """Reproduce a figure from a FigureRecord.

    Parameters
    ----------
    record : FigureRecord
        The figure record to reproduce.
    calls : list of str, optional
        If provided, only reproduce these specific call IDs.
    skip_decorations : bool
        If True, skip decoration calls.

    Returns
    -------
    fig : RecordingFigure
        Reproduced figure (wrapped).
    axes : RecordingAxes or ndarray of RecordingAxes
        Reproduced axes (wrapped, numpy array for multi-axes).
    """
    from .._recorder import Recorder
    from .._wrappers import RecordingAxes, RecordingFigure

    # mm-based composed figures (plt.compose) key their panels "ax_mm_*" and
    # position each via add_axes(bbox); the grid model below can't represent that
    # (every ax_mm_* collapses to grid cell (0,0) -> only one panel survives, wrong
    # size). Rebuild them faithfully via the dedicated mm reproducer.
    from ._mm_compose import is_mm_composed, reproduce_mm_composed

    if is_mm_composed(record):
        return reproduce_mm_composed(record)

    # Determine grid size from axes positions
    max_row = 0
    max_col = 0
    for ax_key in record.axes.keys():
        parsed = parse_grid_id(ax_key)
        if parsed is not None:
            max_row = max(max_row, parsed[0])
            max_col = max(max_col, parsed[1])

    nrows = max_row + 1
    ncols = max_col + 1

    # Create figure
    import matplotlib.pyplot as plt

    fig, mpl_axes = plt.subplots(
        nrows,
        ncols,
        figsize=record.figsize,
        dpi=record.dpi,
        constrained_layout=record.constrained_layout,
    )

    # Apply layout if recorded (skip if constrained_layout is used)
    if record.layout is not None and not record.constrained_layout:
        fig.subplots_adjust(**record.layout)

    # Ensure axes is 2D array
    if nrows == 1 and ncols == 1:
        axes_2d = np.array([[mpl_axes]])
    else:
        axes_2d = np.atleast_2d(mpl_axes)
        if nrows == 1:
            axes_2d = axes_2d.reshape(1, -1)
        elif ncols == 1:
            axes_2d = axes_2d.reshape(-1, 1)

    # Apply style BEFORE replaying calls (to match original order:
    # style is applied during subplots(), then user creates plots/decorations)
    if record.style is not None:
        from ..styles._internal import apply_style_mm

        for row in range(nrows):
            for col in range(ncols):
                apply_style_mm(axes_2d[row, col], record.style)

    # Result cache for resolving references (e.g., clabel needs ContourSet from contour)
    result_cache: Dict[str, Any] = {}

    # Replay calls on each axes
    for ax_key, ax_record in record.axes.items():
        parsed = parse_grid_id(ax_key)
        row, col = parsed if parsed else (0, 0)

        ax = axes_2d[row, col]

        # Replay plotting calls
        for call in ax_record.calls:
            if calls is not None and call.id not in calls:
                continue
            result = _replay_call(ax, call, result_cache)
            if result is not None:
                result_cache[call.id] = result

        # Replay decorations
        if not skip_decorations:
            for call in ax_record.decorations:
                if calls is not None and call.id not in calls:
                    continue
                result = _replay_call(ax, call, result_cache)
                if result is not None:
                    result_cache[call.id] = result

        # Apply panel visibility
        if not getattr(ax_record, "visible", True):
            ax.set_visible(False)

    # Replay recorded colorbars (exact reproduction)
    _replay_colorbars(fig, axes_2d, record, result_cache)

    # Finalize tick configuration and special plot types
    from ..styles._style_applier import finalize_special_plots, finalize_ticks
    from ._line_styles import apply_line_styles

    for row in range(nrows):
        for col in range(ncols):
            finalize_ticks(axes_2d[row, col])
            finalize_special_plots(axes_2d[row, col], record.style or {})

    # Apply trace linewidth to all Line2D objects created during replay
    apply_line_styles(axes_2d, record.style or {})

    # Apply figure-level labels if recorded
    if record.suptitle is not None:
        text = record.suptitle.get("text", "")
        kwargs = record.suptitle.get("kwargs", {}).copy()
        # Only add y=1.02 if not using constrained_layout (which handles positioning)
        if "y" not in kwargs and not record.constrained_layout:
            kwargs["y"] = 1.02
        fig.suptitle(text, **kwargs)

    if record.supxlabel is not None:
        text = record.supxlabel.get("text", "")
        kwargs = record.supxlabel.get("kwargs", {})
        fig.supxlabel(text, **kwargs)

    if record.supylabel is not None:
        text = record.supylabel.get("text", "")
        kwargs = record.supylabel.get("kwargs", {})
        fig.supylabel(text, **kwargs)

    # Replay figure-level fig.text() annotations
    for txt_entry in record.figure_texts:
        fig.text(
            txt_entry["x"],
            txt_entry["y"],
            txt_entry.get("s", ""),
            **txt_entry.get("kwargs", {}),
        )

    # Wrap in Recording types (same as subplots() returns)
    recorder = Recorder()
    recorder._figure_record = record

    # Wrap axes in RecordingAxes
    wrapped_axes = np.empty((nrows, ncols), dtype=object)
    for i in range(nrows):
        for j in range(ncols):
            wrapped_axes[i, j] = RecordingAxes(axes_2d[i, j], recorder, position=(i, j))

    # Create RecordingFigure
    wrapped_fig = RecordingFigure(fig, recorder, wrapped_axes.tolist())

    # Restore mm_layout for consistent cropping during save
    if record.mm_layout is not None:
        wrapped_fig._mm_layout = record.mm_layout

    # Reproduce panel labels if recorded
    if record.panel_labels is not None:
        labels = record.panel_labels.get("labels")
        loc = record.panel_labels.get("loc", "upper left")
        offset = tuple(record.panel_labels.get("offset", (-0.1, 1.05)))
        fontsize = record.panel_labels.get("fontsize")
        fontweight = record.panel_labels.get("fontweight", "bold")
        color = record.panel_labels.get("color")
        extra_kwargs = record.panel_labels.get("kwargs", {})
        if color is not None:
            extra_kwargs["color"] = color
        wrapped_fig.add_panel_labels(
            labels=labels,
            loc=loc,
            offset=offset,
            fontsize=fontsize,
            fontweight=fontweight,
            **extra_kwargs,
        )

    # Return in appropriate format (matching subplots() behavior)
    if nrows == 1 and ncols == 1:
        return wrapped_fig, wrapped_axes[0, 0]
    elif nrows == 1:
        return wrapped_fig, np.array(wrapped_axes[0], dtype=object)
    elif ncols == 1:
        return wrapped_fig, np.array(wrapped_axes[:, 0], dtype=object)
    else:
        return wrapped_fig, wrapped_axes


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


def get_recipe_info(path: Union[str, Path]) -> Dict[str, Any]:
    """Get recipe metadata (id, figsize, dpi, n_axes, calls) without reproducing."""
    record = load_recipe(path)

    all_calls = []
    for ax_record in record.axes.values():
        for call in ax_record.calls:
            all_calls.append(
                {
                    "id": call.id,
                    "function": call.function,
                    "n_args": len(call.args),
                    "kwargs": list(call.kwargs.keys()),
                }
            )
        for call in ax_record.decorations:
            all_calls.append(
                {
                    "id": call.id,
                    "function": call.function,
                    "type": "decoration",
                }
            )

    return {
        "id": record.id,
        "created": record.created,
        "matplotlib_version": record.matplotlib_version,
        "figsize": record.figsize,
        "dpi": record.dpi,
        "n_axes": len(record.axes),
        "calls": all_calls,
    }


__all__ = [
    "reproduce",
    "reproduce_from_record",
    "get_recipe_info",
]
