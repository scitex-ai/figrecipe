#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scientific plot types: confusion matrix, ECDF, raster, scatter+hist.

Ported from scitex.plt.ax._plot for figrecipe integration.
"""

import numpy as np
import pandas as pd
from matplotlib.axes import Axes


def stx_conf_mat(
    ax: Axes,
    conf_mat_2d,
    x_labels=None,
    y_labels=None,
    title="Confusion Matrix",
    cmap="Blues",
    cbar=True,
    **kwargs,
):
    """Plot a confusion matrix as a heatmap.

    Parameters
    ----------
    ax : Axes
    conf_mat_2d : array-like, shape (n_classes, n_classes)
        Confusion matrix (rows=true, cols=predicted).
    x_labels, y_labels : list, optional
        Axis labels.
    title : str
    cmap : str
    cbar : bool

    Returns
    -------
    ax : Axes
    """
    try:
        import seaborn as sns
    except ImportError:
        raise ImportError(
            "stx_conf_mat requires seaborn: pip install seaborn"
        ) from None

    conf_mat_2d = np.asarray(conf_mat_2d)
    n_classes = conf_mat_2d.shape[0]

    if x_labels is None:
        x_labels = [str(i) for i in range(n_classes)]
    if y_labels is None:
        y_labels = [str(i) for i in range(n_classes)]

    # Calculate balanced accuracy
    per_class = np.diag(conf_mat_2d) / conf_mat_2d.sum(axis=1).clip(min=1)
    bacc = per_class.mean()

    df = pd.DataFrame(conf_mat_2d, index=y_labels, columns=x_labels)
    sns.heatmap(
        df,
        annot=True,
        fmt="d",
        cmap=cmap,
        cbar=cbar,
        ax=ax,
        **kwargs,
    )

    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"{title}\n(bACC={bacc:.3f})")
    ax.invert_yaxis()

    # Clean up spines
    for spine in ax.spines.values():
        spine.set_visible(False)

    return ax


def stx_ecdf(ax: Axes, values_1d, **kwargs):
    """Plot an empirical cumulative distribution function (ECDF).

    Parameters
    ----------
    ax : Axes
    values_1d : array-like, shape (n,)
        Data values.
    **kwargs
        Passed to ax.plot().

    Returns
    -------
    ax : Axes
    df : DataFrame
        With columns: x, y, n, x_step, y_step.
    """
    values_1d = np.asarray(values_1d, dtype=float)

    # Remove NaN
    mask = ~np.isnan(values_1d)
    values = values_1d[mask]
    n = len(values)

    if n == 0:
        return ax, pd.DataFrame(columns=["x", "y", "n", "x_step", "y_step"])

    sorted_vals = np.sort(values)
    y = np.arange(1, n + 1) / n

    # Steps for proper step-function display
    x_step = np.repeat(sorted_vals, 2)
    y_step = np.zeros(2 * n)
    y_step[0] = 0
    y_step[1::2] = y
    y_step[2::2] = y[:-1]

    # Append final point
    x_step = np.append(x_step, sorted_vals[-1])
    y_step = np.append(y_step, 1.0)

    if "label" in kwargs and kwargs["label"]:
        kwargs["label"] = f"{kwargs['label']} ($n$={n})"

    ax.plot(x_step, y_step, drawstyle="steps-post", **kwargs)

    df = pd.DataFrame(
        {
            "x": np.concatenate([sorted_vals, [np.nan] * (len(x_step) - n)]),
            "y": np.concatenate([y, [np.nan] * (len(x_step) - n)]),
            "n": [n] + [np.nan] * (len(x_step) - 1),
            "x_step": x_step,
            "y_step": y_step,
        }
    )
    return ax, df


def stx_raster(
    ax: Axes,
    spike_times_list,
    time=None,
    labels=None,
    colors=None,
    orientation="horizontal",
    y_offset=None,
    lineoffsets=None,
    linelengths=None,
    **kwargs,
):
    """Plot a raster/event plot for spike times or event data.

    Parameters
    ----------
    ax : Axes
    spike_times_list : list of array-like
        Each element is spike/event times for one trial/channel.
    time : tuple, optional
        (start, end) for time axis limits.
    labels : list, optional
        Labels for each channel/trial.
    colors : list or str, optional
        Colors for event lines.
    orientation : str
        'horizontal' or 'vertical'.
    y_offset : float, optional
        Vertical offset between channels.
    lineoffsets : array-like, optional
        Y positions for each channel.
    linelengths : float or array-like, optional
        Length of event lines.

    Returns
    -------
    ax : Axes
    df : DataFrame
        Digital representation of spike data.
    """
    n_channels = len(spike_times_list)

    if lineoffsets is None:
        offset = y_offset if y_offset is not None else 1.0
        lineoffsets = np.arange(n_channels) * offset

    if linelengths is None:
        linelengths = 0.8

    kw = kwargs.copy()
    if colors is not None:
        kw["colors"] = colors

    ax.eventplot(
        spike_times_list,
        orientation=orientation,
        lineoffsets=lineoffsets,
        linelengths=linelengths,
        **kw,
    )

    if time is not None:
        if orientation == "horizontal":
            ax.set_xlim(time)
        else:
            ax.set_ylim(time)

    if labels is not None:
        if orientation == "horizontal":
            ax.set_yticks(lineoffsets[: len(labels)])
            ax.set_yticklabels(labels)
        else:
            ax.set_xticks(lineoffsets[: len(labels)])
            ax.set_xticklabels(labels)

    # Build digital representation
    if time is not None:
        t_start, t_end = time
        n_bins = int((t_end - t_start) * 1000)  # ms resolution
        bins = np.linspace(t_start, t_end, n_bins + 1)
        digital = np.zeros((n_channels, n_bins), dtype=int)
        for i, spikes in enumerate(spike_times_list):
            spikes = np.asarray(spikes)
            idx = np.digitize(spikes, bins) - 1
            idx = idx[(idx >= 0) & (idx < n_bins)]
            digital[i, idx] = 1
        df = pd.DataFrame(digital, columns=[f"t{j}" for j in range(n_bins)])
    else:
        df = pd.DataFrame({"channel": range(n_channels)})

    return ax, df


def _to_float_array(values):
    """Convert an array-like (incl. pandas datetime) to a float ndarray.

    Returns
    -------
    floats : np.ndarray
        Float representation suitable for KDE estimation.
    is_datetime : bool
        True when the input was datetime-like and converted via
        ``matplotlib.dates.date2num`` (so the caller can plot the density
        curve back onto the native datetime axis).
    """
    # Datetime detection: pandas datetime Series/Index, numpy datetime64,
    # or python datetime objects.
    is_datetime = False
    arr = np.asarray(values)

    pandas_dt = pd.api.types.is_datetime64_any_dtype(getattr(values, "dtype", None))
    if pandas_dt or np.issubdtype(arr.dtype, np.datetime64):
        import matplotlib.dates as mdates

        floats = mdates.date2num(np.asarray(values))
        return np.asarray(floats, dtype=float), True

    # Object dtype that may hold python datetimes / Timestamps.
    if arr.dtype == object:
        try:
            import matplotlib.dates as mdates

            converted = pd.to_datetime(values)
            floats = mdates.date2num(np.asarray(converted))
            return np.asarray(floats, dtype=float), True
        except (ValueError, TypeError):
            pass

    return np.asarray(arr, dtype=float), is_datetime


def _kde_curve(float_values, n_points=200, pad_frac=0.05):
    """Estimate a 1D KDE and return (grid, density) on a float grid.

    Returns ``(None, None)`` when the KDE cannot be estimated (e.g. fewer
    than two finite points or zero variance).
    """
    from scipy.stats import gaussian_kde

    vals = np.asarray(float_values, dtype=float)
    vals = vals[np.isfinite(vals)]
    if vals.size < 2 or np.allclose(vals, vals[0]):
        return None, None
    try:
        kde = gaussian_kde(vals)
    except (np.linalg.LinAlgError, ValueError):
        return None, None
    lo, hi = vals.min(), vals.max()
    pad = (hi - lo) * pad_frac if hi > lo else 1.0
    grid = np.linspace(lo - pad, hi + pad, n_points)
    return grid, kde(grid)


def stx_scatter_hist(
    ax: Axes,
    x,
    y,
    fig=None,
    hist_bins=20,
    scatter_alpha=0.6,
    scatter_size=20,
    scatter_color=None,
    hist_color_x="blue",
    hist_color_y="red",
    hist_alpha=0.5,
    scatter_ratio=0.8,
    kde=False,
    groups=None,
    palette=None,
    marginal_label=None,
    **kwargs,
):
    """Scatter plot with marginal histograms or per-class KDE curves.

    Parameters
    ----------
    ax : Axes
        Main axes for scatter plot.
    x, y : array-like
        Data arrays. ``x`` may be a pandas datetime Series; in that case the
        scatter stays on a native datetime axis and the KDE is estimated on
        the ``matplotlib.dates.date2num`` float representation, then plotted
        back on the datetime axis.
    fig : Figure, optional
        Figure object (needed for marginal axes). Auto-detected if None.
    hist_bins : int
    scatter_alpha, scatter_size : scatter styling
    scatter_color : color or array-like, optional
        Per-point colour(s) for the scatter. When None and ``groups`` +
        ``palette`` are given, points are coloured per group. When None and
        no groups, falls back to ``"blue"``.
    hist_color_x, hist_color_y, hist_alpha : histogram styling (hist mode)
    scatter_ratio : float
        Fraction of axes used for scatter.
    kde : bool, default False
        When True, draw smooth KDE density curves on the marginals instead of
        histograms. With ``groups`` set, one KDE per group is drawn on each
        marginal, coloured to match the scatter.
    groups : array-like, optional
        Per-point group labels (``len == len(x)``). One KDE per unique group.
    palette : dict, optional
        ``{group: color}`` mapping used to colour per-group KDE curves and,
        when ``scatter_color`` is None, the scatter points per group.
    marginal_label : str, optional
        Text label for the density/count dimension of the marginal axes. When
        set, it is applied as the y-label of the top marginal (``ax_histx``)
        and the x-label of the right marginal (``ax_histy``). The numeric ticks
        stay hidden (the density scale is arbitrary); only the text is shown.
        Applies in both ``kde=True`` (density) and ``kde=False`` (count) modes.
        When ``kde=True`` and this is left as ``None``, it defaults to
        ``"Density"`` so the KDE marginals are labelled automatically; pass an
        explicit value (including ``""``) to override.

    Returns
    -------
    ax : Axes
    df : DataFrame
    """
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    # Keep original x for datetime-aware scatter / DataFrame; floats for KDE.
    x_orig = x
    y_arr = np.asarray(y, dtype=float)
    x_float, x_is_datetime = _to_float_array(x)
    x_plot = np.asarray(x_orig) if x_is_datetime else np.asarray(x, dtype=float)

    groups_arr = None if groups is None else np.asarray(groups)
    palette = palette or {}

    if fig is None:
        fig = ax.get_figure()

    # ── Main scatter ────────────────────────────────────────────────
    if scatter_color is None and groups_arr is not None:
        # Per-group colouring.
        for g in pd.unique(groups_arr):
            mask = groups_arr == g
            ax.scatter(
                x_plot[mask],
                y_arr[mask],
                s=scatter_size,
                alpha=scatter_alpha,
                c=palette.get(g),
                label=str(g),
                **kwargs,
            )
    else:
        c = scatter_color if scatter_color is not None else "blue"
        ax.scatter(x_plot, y_arr, s=scatter_size, alpha=scatter_alpha, c=c, **kwargs)

    # Default the marginal label to "Density" for KDE marginals when the caller
    # passed nothing (None == auto). An explicit value (incl. "") still wins.
    if kde and marginal_label is None:
        marginal_label = "Density"

    # Marginal size as percentage string (e.g. scatter_ratio=0.8 → margin=20%)
    margin_pct = f"{int(round((1 - scatter_ratio) * 100))}%"
    divider = make_axes_locatable(ax)
    ax_histx = divider.append_axes("top", size=margin_pct, pad=0.1, sharex=ax)
    ax_histy = divider.append_axes("right", size=margin_pct, pad=0.1, sharey=ax)

    if kde:
        import matplotlib.dates as mdates

        def _x_grid_to_plot(grid):
            # Map a float KDE grid back to the native scatter x-axis.
            return mdates.num2date(grid) if x_is_datetime else grid

        if groups_arr is not None:
            for g in pd.unique(groups_arr):
                mask = groups_arr == g
                color = palette.get(g)
                # Top marginal: KDE over x (datetime-aware).
                gx, dx = _kde_curve(x_float[mask])
                if gx is not None:
                    gx_plot = _x_grid_to_plot(gx)
                    ax_histx.plot(gx_plot, dx, color=color, alpha=hist_alpha)
                    ax_histx.fill_between(
                        gx_plot, dx, color=color, alpha=hist_alpha * 0.4
                    )
                # Right marginal: KDE over y (plotted horizontally).
                gy, dy = _kde_curve(y_arr[mask])
                if gy is not None:
                    ax_histy.plot(dy, gy, color=color, alpha=hist_alpha)
                    ax_histy.fill_betweenx(gy, dy, color=color, alpha=hist_alpha * 0.4)
        else:
            gx, dx = _kde_curve(x_float)
            if gx is not None:
                ax_histx.plot(
                    _x_grid_to_plot(gx), dx, color=hist_color_x, alpha=hist_alpha
                )
            gy, dy = _kde_curve(y_arr)
            if gy is not None:
                ax_histy.plot(dy, gy, color=hist_color_y, alpha=hist_alpha)
    else:
        ax_histx.hist(x_plot, bins=hist_bins, alpha=hist_alpha, color=hist_color_x)
        ax_histy.hist(
            y_arr,
            bins=hist_bins,
            alpha=hist_alpha,
            color=hist_color_y,
            orientation="horizontal",
        )

    # Top marginal: hide x-tick labels (shared with scatter) and y-axis entirely
    ax_histx.tick_params(labelbottom=False, labelleft=False, left=False)
    ax_histx.spines["right"].set_visible(False)
    ax_histx.spines["top"].set_visible(False)

    # Right marginal: hide y-tick labels (shared with scatter) and x-axis entirely
    ax_histy.tick_params(labelleft=False, labelbottom=False, bottom=False)
    ax_histy.spines["top"].set_visible(False)
    ax_histy.spines["right"].set_visible(False)

    # Optional label for the density/count dimension of the marginals.
    if marginal_label is not None:
        ax_histx.set_ylabel(marginal_label)
        ax_histy.set_xlabel(marginal_label)

    df = pd.DataFrame({"x": np.asarray(x_orig), "y": y_arr})
    return ax, df


__all__ = [
    "stx_conf_mat",
    "stx_ecdf",
    "stx_raster",
    "stx_scatter_hist",
]

# EOF
