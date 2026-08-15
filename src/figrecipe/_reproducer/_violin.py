#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Violin plot replay for figure reproduction."""

from typing import Any

from matplotlib.axes import Axes

from .._recorder import CallRecord
from ._warnings import ReplayFailureWarning


def replay_violinplot_call(ax: Axes, call: CallRecord) -> Any:
    """Replay a violinplot call with inner option support.

    Parameters
    ----------
    ax : Axes
        The matplotlib axes.
    call : CallRecord
        The violinplot call to replay.

    Returns
    -------
    Any
        Result of the violinplot call.
    """
    from ._reconstruct import reconstruct_kwargs, reconstruct_value

    # Reconstruct args
    args = []
    for arg_data in call.args:
        value = reconstruct_value(arg_data)
        args.append(value)

    # Get kwargs and reconstruct arrays
    kwargs = reconstruct_kwargs(call.kwargs)

    # Extract custom options (not matplotlib kwargs)
    inner = kwargs.pop("inner", None)
    kde_extend = kwargs.pop("kde_extend", False)
    body_colors = kwargs.pop("_body_colors", None)
    body_alphas = kwargs.pop("_body_alphas", None)
    showmeans = kwargs.pop("showmeans", False)
    showmedians = kwargs.pop("showmedians", False)
    showextrema = kwargs.pop("showextrema", False)

    try:
        from ..styles._internal import get_style

        style = get_style()
        violin_style = style.get("violinplot", {}) if style else {}

        dataset = args[0] if args else []
        positions = kwargs.get("positions")
        if positions is None:
            positions = list(range(1, len(dataset) + 1))

        # Draw violin bodies
        if kde_extend:
            from .._wrappers._violin_kde import draw_kde_violins

            result = draw_kde_violins(ax, dataset, positions, None, violin_style)
        else:
            result = ax.violinplot(
                *args,
                showmeans=showmeans,
                showmedians=showmedians,
                showextrema=showextrema,
                **kwargs,
            )
            if "bodies" in result:
                for i, body in enumerate(result["bodies"]):
                    if body_colors is not None and i < len(body_colors):
                        body.set_facecolor(body_colors[i])
                    if (
                        body_alphas is not None
                        and i < len(body_alphas)
                        and body_alphas[i] is not None
                    ):
                        body.set_alpha(body_alphas[i])
                    else:
                        body.set_alpha(violin_style.get("alpha", 0.7))

        # Overlay inner elements (supports "box+swarm" combos)
        from .._wrappers._violin_helpers import (
            add_violin_inner_box,
            add_violin_inner_point,
            add_violin_inner_stick,
            add_violin_inner_swarm,
        )

        parts = (
            [p.strip() for p in inner.split("+")]
            if inner and "+" in inner
            else [inner]
            if inner
            else []
        )
        for part in parts:
            if part == "box":
                add_violin_inner_box(ax, dataset, positions, violin_style)
            elif part == "swarm":
                add_violin_inner_swarm(ax, dataset, positions, violin_style)
            elif part == "stick":
                add_violin_inner_stick(ax, dataset, positions, violin_style)
            elif part == "point":
                add_violin_inner_point(ax, dataset, positions, violin_style)

        # Tighten x-axis
        x_pad = 0.5
        ax.set_xlim(min(positions) - x_pad, max(positions) + x_pad)

        return result
    except Exception as e:
        import warnings

        warnings.warn(
            f"Failed to replay violinplot: {e}", ReplayFailureWarning
        )
        return None


__all__ = ["replay_violinplot_call"]
