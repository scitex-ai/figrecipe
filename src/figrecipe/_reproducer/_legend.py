#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Legend reproduction with SCITEX styling."""

from typing import Any, Dict, Optional


def replay_legend_call(
    ax,
    call,
    result_cache: Optional[Dict[str, Any]] = None,
) -> Any:
    """Replay legend call with SCITEX styling.

    Parameters
    ----------
    ax : Axes
        The matplotlib axes.
    call : CallRecord
        The legend call to replay.
    result_cache : dict, optional
        Cache for result references.

    Returns
    -------
    Legend or None
        The created legend.
    """
    from ..styles import load_style
    from ._reconstruct import reconstruct_kwargs, reconstruct_value

    if result_cache is None:
        result_cache = {}

    # Reconstruct args and kwargs
    args = [reconstruct_value(arg_data, result_cache) for arg_data in call.args]
    kwargs = reconstruct_kwargs(call.kwargs)

    # Handle custom handles stored as _handle_specs
    if "_handle_specs" in kwargs:
        from matplotlib.patches import Patch

        handle_specs = kwargs.pop("_handle_specs")
        handles = []
        for spec in handle_specs:
            patch = Patch(
                facecolor=spec.get("facecolor", "gray"),
                edgecolor=spec.get("edgecolor", "black"),
                label=spec.get("label", ""),
            )
            handles.append(patch)
        kwargs["handles"] = handles

    # Drop figrecipe-internal metadata keys (underscore-prefixed) that
    # were recorded for provenance/debugging only and are NOT valid
    # matplotlib legend kwargs (e.g. ``_handler_map_summary``, the safe
    # summary of a dropped non-serializable custom handler_map).
    for meta_key in [k for k in kwargs if isinstance(k, str) and k.startswith("_")]:
        kwargs.pop(meta_key)

    # Create legend
    legend = ax.legend(*args, **kwargs)

    # Apply SCITEX style frame settings
    if legend is not None:
        style = load_style()
        legend_config = style.get("legend", {})

        frameon = legend_config.get("frameon", True)
        edge_mm = legend_config.get("edge_mm", 0.2)
        edgecolor = legend_config.get("edgecolor", "black")

        if frameon and edge_mm:
            frame = legend.get_frame()
            frame.set_linewidth(edge_mm * 72 / 25.4)  # mm to points
            if edgecolor:
                frame.set_edgecolor(edgecolor)

    return legend


__all__ = ["replay_legend_call"]
