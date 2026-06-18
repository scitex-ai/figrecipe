#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Custom plotting methods for RecordingAxes."""

from typing import TYPE_CHECKING, Any, List, Optional

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from .._recorder import Recorder


def pie_plot(
    ax: "Axes",
    x,
    recorder: "Recorder",
    position: tuple,
    track: bool,
    call_id: Optional[str],
    **kwargs,
) -> tuple:
    """Pie chart with automatic SCITEX styling."""
    from ..styles._internal import get_style, resolve_colors_in_kwargs
    from ._axes_helpers import inject_clip_on_from_style
    from ._pie_helpers import (
        apply_pie_autopct,
        apply_pie_axes_visibility,
        apply_pie_text_style,
        apply_pie_wedgeprops,
    )

    kwargs = resolve_colors_in_kwargs(kwargs)
    kwargs = inject_clip_on_from_style(kwargs, "pie")

    style = get_style()
    pie_style = style.get("pie", {}) if style else {}

    kwargs = apply_pie_wedgeprops(kwargs, pie_style)
    kwargs = apply_pie_autopct(kwargs, pie_style)

    result = ax.pie(x, **kwargs)

    if style:
        apply_pie_text_style(ax, pie_style, style)
        apply_pie_axes_visibility(ax, pie_style)

    if track:
        recorder.record_call(
            ax_position=position,
            method_name="pie",
            args=(x,),
            kwargs=kwargs,
            call_id=call_id,
        )

    return result


def imshow_plot(
    ax: "Axes",
    X,
    recorder: "Recorder",
    position: tuple,
    track: bool,
    call_id: Optional[str],
    **kwargs,
):
    """Display image with automatic SCITEX styling."""
    from ..styles._internal import get_style
    from ._axes_helpers import inject_clip_on_from_style

    kwargs = inject_clip_on_from_style(kwargs, "imshow")

    # Call matplotlib's imshow
    result = ax.imshow(X, **kwargs)

    # Get style settings
    style = get_style()
    if style:
        from ..styles._plot_styles import apply_imshow_axes_visibility

        imshow_style = style.get("imshow", {})
        apply_imshow_axes_visibility(
            ax,
            imshow_style.get("show_axes", True),
            imshow_style.get("show_labels", True),
        )

    # Record the call if tracking is enabled
    if track:
        recorder.record_call(
            ax_position=position,
            method_name="imshow",
            args=(X,),
            kwargs=kwargs,
            call_id=call_id,
        )

    return result


def violinplot_plot(
    ax: "Axes",
    dataset,
    positions,
    recorder: "Recorder",
    position: tuple,
    track: bool,
    call_id: Optional[str],
    inner: Optional[str],
    colors: Optional[List] = None,
    kde_extend: Optional[bool] = None,
    **kwargs,
) -> dict:
    """Violin plot with inner display options and optional KDE extension.

    Parameters
    ----------
    colors : list, optional
        Colors for each violin body.
    kde_extend : bool, optional
        When True, compute KDE with extended range so tails converge
        smoothly to zero.  Default from style or False.
    """
    import matplotlib.pyplot as mpl_plt

    from ..styles._internal import get_style

    style = get_style()
    violin_style = style.get("violinplot", {}) if style else {}

    if inner is None:
        inner = violin_style.get("inner", "box")
    if kde_extend is None:
        kde_extend = violin_style.get("kde_extend", False)
    if positions is None:
        positions = list(range(1, len(dataset) + 1))

    # --- Draw violin bodies ---
    if kde_extend:
        from ._violin_kde import draw_kde_violins

        result = draw_kde_violins(ax, dataset, positions, colors, violin_style)
    else:
        showmeans = kwargs.pop("showmeans", False)
        showmedians = kwargs.pop("showmedians", False)
        showextrema = kwargs.pop("showextrema", False)
        result = ax.violinplot(
            dataset,
            positions=positions,
            showmeans=showmeans,
            showmedians=showmedians,
            showextrema=showextrema,
            **kwargs,
        )
        alpha = violin_style.get("alpha", 0.7)
        if "bodies" in result:
            if colors is None:
                colors = mpl_plt.rcParams["axes.prop_cycle"].by_key()["color"]
            for i, body in enumerate(result["bodies"]):
                body.set_facecolor(colors[i % len(colors)])
                body.set_alpha(alpha)

    # --- Inner elements ---
    _add_violin_inner_elements(ax, dataset, positions, inner, violin_style)

    # Tighten x-axis around positions
    x_pad = 0.5
    ax.set_xlim(min(positions) - x_pad, max(positions) + x_pad)

    # --- Record ---
    if track:
        rec_kw = kwargs.copy()
        rec_kw.update(
            inner=inner,
            kde_extend=kde_extend,
            showmeans=False,
            showmedians=False,
            showextrema=False,
        )
        if not kde_extend and "bodies" in result:
            body_colors, body_alphas = [], []
            for body in result["bodies"]:
                fc = body.get_facecolor()
                if hasattr(fc, "tolist"):
                    fc = fc.tolist()
                body_colors.append(fc[0] if fc and len(fc) == 1 else fc)
                body_alphas.append(body.get_alpha())
            rec_kw["_body_colors"] = body_colors
            rec_kw["_body_alphas"] = body_alphas
        recorder.record_call(
            ax_position=position,
            method_name="violinplot",
            args=(dataset,),
            kwargs=rec_kw,
            call_id=call_id,
        )

    return result


def _add_violin_inner_elements(
    ax: "Axes", dataset, positions, inner: str, violin_style: dict
) -> None:
    """Add inner elements to violin plot."""
    from ._violin_helpers import (
        add_violin_inner_box,
        add_violin_inner_point,
        add_violin_inner_stick,
        add_violin_inner_swarm,
    )

    parts = [p.strip() for p in inner.split("+")] if "+" in inner else [inner]
    for part in parts:
        if part == "box":
            add_violin_inner_box(ax, dataset, positions, violin_style)
        elif part == "swarm":
            add_violin_inner_swarm(ax, dataset, positions, violin_style)
        elif part == "stick":
            add_violin_inner_stick(ax, dataset, positions, violin_style)
        elif part == "point":
            add_violin_inner_point(ax, dataset, positions, violin_style)


def joyplot_plot(
    ax: "Axes",
    recording_axes,
    arrays,
    recorder: "Recorder",
    position: tuple,
    track: bool,
    call_id: Optional[str],
    overlap: float,
    fill_alpha: float,
    line_alpha: float,
    colors,
    labels,
    **kwargs,
):
    """Create a joyplot (ridgeline plot)."""
    from .._utils._units import mm_to_pt
    from ..styles._internal import get_style

    # Convert dict to list of arrays
    if isinstance(arrays, dict):
        if labels is None:
            labels = list(arrays.keys())
        arrays = list(arrays.values())

    n_ridges = len(arrays)

    from ._plot_helpers import compute_joyplot_kdes, get_colors_from_style

    # Get colors from style or use default cycle
    colors = get_colors_from_style(n_ridges, colors)

    # Calculate global x range
    all_data = np.concatenate([np.asarray(arr) for arr in arrays])
    x_min, x_max = np.min(all_data), np.max(all_data)
    x_range = x_max - x_min
    x_padding = x_range * 0.1
    x = np.linspace(x_min - x_padding, x_max + x_padding, 200)

    # Calculate KDEs
    kdes, max_density = compute_joyplot_kdes(arrays, x)

    # Scale factor for ridge height
    ridge_height = 1.0 / (1.0 - overlap * 0.5) if overlap < 1 else 2.0

    # Get line width from style
    style = get_style()
    lw = mm_to_pt(0.2)
    if style and "lines" in style:
        lw = mm_to_pt(style.lines.get("trace_mm", 0.2))

    # Plot each ridge from back to front
    for i in range(n_ridges - 1, -1, -1):
        color = colors[i % len(colors)]
        baseline = i * (1.0 - overlap)
        scaled_density = (
            kdes[i] / max_density * ridge_height if max_density > 0 else kdes[i]
        )

        ax.fill_between(
            x,
            baseline,
            baseline + scaled_density,
            facecolor=color,
            edgecolor="none",
            alpha=fill_alpha,
        )
        ax.plot(
            x,
            baseline + scaled_density,
            color=color,
            alpha=line_alpha,
            linewidth=lw,
        )

    # Set y limits
    ax.set_ylim(-0.1, n_ridges * (1.0 - overlap) + ridge_height)

    # Set y-axis labels
    if labels:
        y_positions = [(i * (1.0 - overlap)) + 0.3 for i in range(n_ridges)]
        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels)
    else:
        ax.set_yticks([])

    # Record the call if tracking is enabled
    if track:
        recorder.record_call(
            ax_position=position,
            method_name="joyplot",
            args=(arrays,),
            kwargs={
                "overlap": overlap,
                "fill_alpha": fill_alpha,
                "line_alpha": line_alpha,
                "labels": labels,
            },
            call_id=call_id,
        )

    return recording_axes


def swarmplot_plot(
    ax: "Axes",
    data,
    positions,
    recorder: "Recorder",
    position: tuple,
    track: bool,
    call_id: Optional[str],
    size: Optional[float],
    color,
    alpha: float,
    jitter: float,
    **kwargs,
) -> List[Any]:
    """Create a swarm plot (beeswarm plot)."""
    from .._utils._units import mm_to_pt
    from ..styles._internal import get_style

    # Get style
    style = get_style()

    # Default marker size from style
    if size is None:
        if style and "markers" in style:
            size = style.markers.get("scatter_mm", 0.8)
        else:
            size = 0.8
    size_pt = mm_to_pt(size) ** 2

    from ._plot_helpers import beeswarm_positions, get_colors_from_style

    # Get colors
    colors = get_colors_from_style(len(data), color)

    # Default positions
    if positions is None:
        positions = list(range(1, len(data) + 1))

    # Random generator for reproducible jitter
    rng = np.random.default_rng(42)

    results = []
    for i, (arr, pos) in enumerate(zip(data, positions)):
        arr = np.asarray(arr)
        x_jitter = beeswarm_positions(arr, jitter, rng)
        x_positions = pos + x_jitter
        c = colors[i % len(colors)]
        result = ax.scatter(x_positions, arr, s=size_pt, c=[c], alpha=alpha, **kwargs)
        results.append(result)

    # Record the call if tracking is enabled
    if track:
        recorder.record_call(
            ax_position=position,
            method_name="swarmplot",
            args=(data,),
            kwargs={
                "positions": positions,
                "size": size,
                "alpha": alpha,
                "jitter": jitter,
            },
            call_id=call_id,
        )

    return results


def bar_plot(
    ax: "Axes",
    args: tuple,
    kwargs: dict,
    recorder: "Recorder",
    position: tuple,
    track: bool,
    call_id: Optional[str],
):
    """Bar chart with SCITEX error bar styling."""
    from .._utils._units import mm_to_pt
    from ..styles._internal import get_style, resolve_colors_in_kwargs
    from ._axes_helpers import inject_clip_on_from_style

    # Resolve named colors to style colors
    kwargs = resolve_colors_in_kwargs(kwargs)
    kwargs = inject_clip_on_from_style(kwargs, "bar")

    # Extract stats before passing to matplotlib (it's metadata only)
    stats = kwargs.pop("stats", None)

    # Get style settings
    style = get_style()

    # Apply error bar styling if yerr or xerr is present
    if style and ("yerr" in kwargs or "xerr" in kwargs):
        lines_style = style.get("lines", {})
        errorbar_mm = lines_style.get("errorbar_mm", 0.12)
        errorbar_cap_mm = lines_style.get("errorbar_cap_mm", 0.8)

        # Convert mm to points
        elinewidth = mm_to_pt(errorbar_mm)
        capthick = mm_to_pt(errorbar_mm)
        capsize = mm_to_pt(errorbar_cap_mm)

        # Merge with existing error_kw if provided
        error_kw = kwargs.get("error_kw", {})
        if "elinewidth" not in error_kw:
            error_kw["elinewidth"] = elinewidth
        if "capthick" not in error_kw:
            error_kw["capthick"] = capthick
        kwargs["error_kw"] = error_kw

        # Set capsize if not already specified
        if "capsize" not in kwargs:
            kwargs["capsize"] = capsize

    # Call matplotlib's bar
    result = ax.bar(*args, **kwargs)

    # Record the call if tracking is enabled
    if track:
        from ._axes_helpers import (
            args_have_fmt_color,
            extract_color_from_result,
        )

        recorded_kwargs = kwargs.copy()

        # Add stats back for recording (it's metadata)
        if stats is not None:
            recorded_kwargs["stats"] = stats

        # Capture color if not specified
        if (
            "color" not in recorded_kwargs
            and "c" not in recorded_kwargs
            and not args_have_fmt_color(args)
        ):
            actual_color = extract_color_from_result("bar", result)
            if actual_color is not None:
                recorded_kwargs["color"] = actual_color

        recorder.record_call(
            ax_position=position,
            method_name="bar",
            args=args,
            kwargs=recorded_kwargs,
            call_id=call_id,
        )

    return result


__all__ = [
    "pie_plot",
    "imshow_plot",
    "violinplot_plot",
    "joyplot_plot",
    "swarmplot_plot",
    "bar_plot",
]

# EOF
