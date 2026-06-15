#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple plot helpers: fillv, rectangle, image, violin.

Ported from scitex.plt.ax._plot for figrecipe integration.
"""

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.patches import Rectangle


def stx_fillv(ax, starts_1d, ends_1d, color="red", alpha=0.2):
    """Fill vertical spans between start and end positions.

    Parameters
    ----------
    ax : Axes or array of Axes
        Axes to fill on.
    starts_1d : array-like
        Start x-positions.
    ends_1d : array-like
        End x-positions.
    color : str
    alpha : float

    Returns
    -------
    ax : Axes or list
    """
    is_array = isinstance(ax, np.ndarray)
    axes = ax if is_array else [ax]

    for a in axes:
        for start, end in zip(starts_1d, ends_1d):
            a.axvspan(start, end, facecolor=color, edgecolor="none", alpha=alpha)

    return ax if is_array else axes[0]


def stx_rectangle(ax: Axes, xx, yy, ww, hh, **kwargs):
    """Add a rectangle patch to axes.

    Parameters
    ----------
    ax : Axes
    xx, yy : float
        Bottom-left corner.
    ww, hh : float
        Width and height.
    **kwargs
        Passed to Rectangle.

    Returns
    -------
    ax : Axes
    """
    if "edgecolor" not in kwargs and "ec" not in kwargs:
        kwargs["edgecolor"] = "none"
    ax.add_patch(Rectangle((xx, yy), ww, hh, **kwargs))
    return ax


def stx_image(
    ax: Axes,
    arr_2d,
    cbar=True,
    cbar_label=None,
    cbar_shrink=1.0,
    cbar_fraction=0.046,
    cbar_pad=0.04,
    cmap="viridis",
    aspect="auto",
    vmin=None,
    vmax=None,
    **kwargs,
):
    """Display a 2D array as an image with correct orientation.

    The first dimension is x (left-right), second is y (bottom-top).

    Parameters
    ----------
    ax : Axes
    arr_2d : array-like, shape (nx, ny)
    cbar : bool
    cbar_label : str, optional
    cmap : str
    aspect : str
    vmin, vmax : float, optional

    Returns
    -------
    ax : Axes
    """
    arr_2d = np.asarray(arr_2d)

    # Transpose for correct orientation
    arr_2d = arr_2d.T

    im = ax.imshow(arr_2d, cmap=cmap, vmin=vmin, vmax=vmax, aspect=aspect, **kwargs)

    if cbar:
        fig = ax.get_figure()
        cb = fig.colorbar(
            im, ax=ax, shrink=cbar_shrink, fraction=cbar_fraction, pad=cbar_pad
        )
        if cbar_label:
            cb.set_label(cbar_label)

    ax.invert_yaxis()
    return ax


def stx_violin(
    ax: Axes,
    values_list,
    labels=None,
    colors=None,
    half=False,
    **kwargs,
):
    """Plot violins from a list of arrays.

    Parameters
    ----------
    ax : Axes
    values_list : list of array-like
        One array per violin group.
    labels : list, optional
        Group labels.
    colors : list, optional
        Violin colors.
    half : bool
        If True, show only left half.
    **kwargs
        Passed to seaborn.violinplot.

    Returns
    -------
    ax : Axes
    """
    try:
        import seaborn as sns
    except ImportError:
        raise ImportError("stx_violin requires seaborn: pip install seaborn") from None

    # Build DataFrame
    all_values, all_groups = [], []
    for idx, values in enumerate(values_list):
        all_values.extend(values)
        lbl = labels[idx] if labels and idx < len(labels) else f"x {idx}"
        all_groups.extend([lbl] * len(values))

    df = pd.DataFrame({"x": all_groups, "y": all_values})

    if colors:
        if isinstance(colors, list):
            unique_groups = list(dict.fromkeys(all_groups))
            kwargs["palette"] = {
                g: c for g, c in zip(unique_groups, colors[: len(unique_groups)])
            }
        else:
            kwargs["palette"] = colors

    if not half:
        sns.violinplot(data=df, x="x", y="y", hue="x", ax=ax, **kwargs)
    else:
        _half_violin(ax, df, "x", "y", **kwargs)

    return ax


def _half_violin(ax, df, x_col, y_col, **kwargs):
    """Plot half-violins (left side only)."""

    try:
        import seaborn as sns
    except ImportError:
        raise ImportError("half violin requires seaborn") from None

    hue = x_col
    df = df.copy()
    df["_fake"] = df[hue] + "_right"

    groups = df[x_col].unique().tolist()
    hue_order = []
    for g in groups:
        hue_order.extend([g, g + "_right"])
    kwargs["hue_order"] = hue_order

    if "palette" in kwargs:
        pal = kwargs["palette"]
        if isinstance(pal, dict):
            kwargs["palette"] = {**pal, **{k + "_right": v for k, v in pal.items()}}

    # Left: real data, Right: NaN
    df_left = df[[x_col, y_col]]
    df_right = df[["_fake", y_col]].rename(columns={"_fake": x_col})
    df_right[y_col] = np.nan
    df_conc = pd.concat([df_left, df_right], ignore_index=True).sort_values(x_col)

    sns.violinplot(
        data=df_conc, x=x_col, y=y_col, hue=x_col, split=True, ax=ax, **kwargs
    )

    # Clean legend
    if ax.legend_ is not None:
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[: len(handles) // 2], labels[: len(labels) // 2])

    return ax


def stx_scalebar(
    ax: Axes,
    x_len,
    y_len,
    x_label="1 min",
    y_label="a.u.",
    loc="lower left",
    color="black",
    lw=1.5,
    pad_frac=(0.04, 0.06),
    label_pad_frac=(0.015, 0.03),
):
    """Draw an L-shaped scale bar for axis-off trace / EEG panels.

    Raw time-series / iEEG panels follow the EEG convention of having no
    x/y axes; an L-shaped scale bar conveys the time (horizontal arm) and
    amplitude (vertical arm) scales instead. The two arms share a corner;
    ``x_label`` sits below the horizontal arm and ``y_label`` sits left of
    the vertical arm, both padded clear so they never overlap the arms or
    each other. Works with ``ax.axis("off")``.

    Font sizes follow the active rcParams / SCITEX_STYLE (no hardcoded
    ``fontsize=``).

    Parameters
    ----------
    ax : Axes
        Target axes. Its current ``xlim`` / ``ylim`` are used to position
        the bar, so call this after the trace data is plotted.
    x_len : float
        Length of the horizontal (time) arm in data units.
    y_len : float
        Length of the vertical (amplitude) arm in data units.
    x_label : str, default "1 min"
        Label for the horizontal arm (a round time unit).
    y_label : str, default "a.u."
        Label for the vertical arm (amplitude unit; may legitimately be
        ``"unknown"`` when the source has no documented gain).
    loc : {"lower left", "lower right", "upper left", "upper right"}
        Corner placement of the L's vertex.
    color : color, default "black"
        Colour of both arms and both labels.
    lw : float, default 1.5
        Line width of the arms.
    pad_frac : (float, float), default (0.04, 0.06)
        Corner inset from the axes edges as a fraction of the axes span
        (x_frac, y_frac).
    label_pad_frac : (float, float), default (0.015, 0.03)
        Label offset off the arms as a fraction of the axes span
        (x_frac, y_frac).

    Returns
    -------
    ax : Axes
    """
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    x_span = x1 - x0
    y_span = y1 - y0

    pad_x = pad_frac[0] * x_span
    pad_y = pad_frac[1] * y_span
    lbl_px = label_pad_frac[0] * x_span
    lbl_py = label_pad_frac[1] * y_span

    # Locate the L's vertex so both arms grow into the plot, regardless of
    # corner. The horizontal arm runs along +x_dir, the vertical along +y_dir.
    if "right" in loc:
        xc = x1 - pad_x - x_len
    else:  # left (default)
        xc = x0 + pad_x
    if "upper" in loc:
        yc = y1 - pad_y - y_len
    else:  # lower (default)
        yc = y0 + pad_y

    # Arms (shared vertex at (xc, yc)).
    ax.plot([xc, xc + x_len], [yc, yc], color=color, lw=lw, solid_capstyle="butt")
    ax.plot([xc, xc], [yc, yc + y_len], color=color, lw=lw, solid_capstyle="butt")

    # Labels, padded clear of the arms (and thus each other).
    ax.text(
        xc + x_len / 2.0,
        yc - lbl_py,
        x_label,
        ha="center",
        va="top",
        color=color,
    )
    ax.text(
        xc - lbl_px,
        yc + y_len / 2.0,
        y_label,
        ha="right",
        va="center",
        rotation=90,
        color=color,
    )

    return ax


__all__ = [
    "stx_fillv",
    "stx_image",
    "stx_rectangle",
    "stx_scalebar",
    "stx_violin",
]

# EOF
