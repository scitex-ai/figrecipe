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


def stx_scatter_hist(
    ax: Axes,
    x,
    y,
    fig=None,
    hist_bins=20,
    scatter_alpha=0.6,
    scatter_size=20,
    scatter_color="blue",
    hist_color_x="blue",
    hist_color_y="red",
    hist_alpha=0.5,
    scatter_ratio=0.8,
    marginal_label=None,
    **kwargs,
):
    """Scatter plot with marginal histograms.

    Parameters
    ----------
    ax : Axes
        Main axes for scatter plot.
    x, y : array-like
        Data arrays.
    fig : Figure, optional
        Figure object (needed for histogram axes). Auto-detected if None.
    hist_bins : int
    scatter_alpha, scatter_size, scatter_color : scatter styling
    hist_color_x, hist_color_y, hist_alpha : histogram styling
    scatter_ratio : float
        Fraction of axes used for scatter.
    marginal_label : str, optional
        Text label for the count/density dimension of the marginal axes. When
        set, it becomes the y-label of the top marginal and the x-label of
        the right marginal so the reader knows what the marginal encodes
        even though the numeric ticks are hidden. When left as ``None`` (the
        default) the histogram marginals auto-label as ``"Count"`` — the
        operator should not have to set this on every call. Pass an empty
        string (``""``) to opt out entirely.

    Returns
    -------
    ax : Axes
    df : DataFrame
    """
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    x, y = np.asarray(x), np.asarray(y)

    if fig is None:
        fig = ax.get_figure()

    # Main scatter
    ax.scatter(x, y, s=scatter_size, alpha=scatter_alpha, c=scatter_color, **kwargs)

    # Default the marginal label to "Count" for histogram marginals when the
    # caller passed nothing (None == auto). An explicit value (incl. "") still
    # wins, so callers can opt out without surprising defaults.
    if marginal_label is None:
        marginal_label = "Count"

    # Marginal size as percentage string (e.g. scatter_ratio=0.8 → margin=20%)
    margin_pct = f"{int(round((1 - scatter_ratio) * 100))}%"
    divider = make_axes_locatable(ax)
    ax_histx = divider.append_axes("top", size=margin_pct, pad=0.1, sharex=ax)
    ax_histy = divider.append_axes("right", size=margin_pct, pad=0.1, sharey=ax)

    ax_histx.hist(x, bins=hist_bins, alpha=hist_alpha, color=hist_color_x)
    ax_histy.hist(
        y,
        bins=hist_bins,
        alpha=hist_alpha,
        color=hist_color_y,
        orientation="horizontal",
    )

    # Top histogram: hide x-tick labels (shared with scatter) and y-axis entirely
    ax_histx.tick_params(labelbottom=False, labelleft=False, left=False)
    ax_histx.spines["right"].set_visible(False)
    ax_histx.spines["top"].set_visible(False)

    # Right histogram: hide y-tick labels (shared with scatter) and x-axis entirely
    ax_histy.tick_params(labelleft=False, labelbottom=False, bottom=False)
    ax_histy.spines["top"].set_visible(False)
    ax_histy.spines["right"].set_visible(False)

    # Auto-applied label for the count dimension of the marginals. Numeric
    # ticks stay hidden because the absolute count value is arbitrary (bin
    # width depends on `hist_bins`); only the text label is shown so the
    # reader knows what the marginal encodes.
    if marginal_label:
        ax_histx.set_ylabel(marginal_label)
        ax_histy.set_xlabel(marginal_label)

    df = pd.DataFrame({"x": x, "y": y})
    return ax, df


__all__ = [
    "stx_conf_mat",
    "stx_ecdf",
    "stx_raster",
    "stx_scatter_hist",
]

# EOF
