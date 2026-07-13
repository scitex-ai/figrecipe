#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sample-size annotation helper: ``stx_annotate_n``.

Standardizes the "n=340" / "N=12 patients" style sample-size annotation
convention placed next to a data point or group, so callers do not need to
hand-roll ``f"{n:,}"`` formatting and ad-hoc ``ax.text`` placement for every
figure. Sibling module to ``_simple.py`` (kept separate to stay under the
project's per-file line budget).
"""

import warnings

from matplotlib.axes import Axes

__all__ = ["stx_annotate_n"]


def stx_annotate_n(
    ax: Axes,
    x,
    y,
    n,
    *,
    prefix="n",
    suffix="",
    comma=True,
    fontsize=None,
    color="black",
    avoid_overlap=True,
    offset_pt=(6.0, 6.0),
    step=6.0,
    max_radius=160.0,
    **kwargs,
):
    """Annotate a data point with a sample-size label (e.g. "n=340").

    Standardizes the sample-size annotation convention used throughout a
    paper (``n=340``, ``N=12 patients`` next to a group / data point):
    consistent font size (the active style's ``annotation_pt``, matching
    ``ax.annotate``/``ax.text``), consistent color (black by default), and
    a placement that avoids the plotted data and other labels.

    Font sizes follow the active rcParams / SCITEX style ``annotation_pt``
    (no hardcoded ``fontsize=`` unless explicitly passed).

    Parameters
    ----------
    ax : Axes
        Target axes. Placement uses the axes' current data limits and
        already-drawn artists, so call this after the data is plotted.
    x, y : float
        Data-coordinate anchor point the annotation belongs to.
    n : int or str
        Sample size. An ``int`` is thousands-comma formatted by default
        (``comma=True``, e.g. ``1234`` -> ``"1,234"``); a ``str`` is used
        verbatim (e.g. ``n="12 patients"``, ``prefix="N"`` -> ``"N=12
        patients"``).
    prefix : str, default "n"
        Label prefix, e.g. ``"n"`` or ``"N"``.
    suffix : str, default ""
        Text appended after the number, e.g. ``" patients"``.
    comma : bool, default True
        Thousands-comma format an integer ``n``.
    fontsize : float, optional
        Defaults to the active style's ``fonts.annotation_pt`` (falls back
        to 6pt if no style is active).
    color : default "black"
        Text color.
    avoid_overlap : bool, default True
        Nudge the label clear of existing plotted ink / legend / other
        labels using the same deterministic ring-search solver that backs
        ``scatter_labels`` (``figrecipe._declutter.solve_label_positions``)
        rather than re-implementing collision avoidance. Falls back to the
        plain ``offset_pt`` position (with a warning) if the figure cannot
        be rendered or no clear spot is found within reach -- never
        silent.
    offset_pt : (float, float), default (6.0, 6.0)
        Initial (dx, dy) offset from the anchor, in points, used as the
        search center for ``avoid_overlap`` (or as the final position when
        ``avoid_overlap=False``).
    step, max_radius : float
        Ring-search granularity / reach, in display pixels. See
        ``solve_label_positions``.
    **kwargs
        Passed to ``ax.text``.

    Returns
    -------
    matplotlib.text.Text

    Examples
    --------
    >>> ax.stx_annotate_n(1.0, 2.5, 340)  # "n=340"
    >>> ax.stx_annotate_n(1.0, 2.5, "12 patients", prefix="N")  # "N=12 patients"
    """
    from ..styles._internal import get_style

    if isinstance(n, str):
        text = f"{prefix}={n}{suffix}"
    elif comma:
        text = f"{prefix}={n:,}{suffix}"
    else:
        text = f"{prefix}={n}{suffix}"

    if fontsize is None:
        style = get_style()
        if style:
            fontsize = style.get("fonts", {}).get("annotation_pt", None)
    if fontsize is None:
        fontsize = 6

    xd, yd = _offset_point(ax, float(x), float(y), offset_pt)

    if avoid_overlap:
        resolved = _resolve_position(
            ax, xd, yd, text, fontsize, step=step, max_radius=max_radius
        )
        if resolved is not None:
            xd, yd = resolved

    text_kwargs = dict(kwargs)
    text_kwargs.setdefault("ha", "center")
    text_kwargs.setdefault("va", "center")
    text_kwargs["fontsize"] = fontsize
    text_kwargs["color"] = color

    return ax.text(xd, yd, text, **text_kwargs)


def _offset_point(ax, x, y, offset_pt):
    """Data-coordinate point offset from ``(x, y)`` by ``offset_pt`` points."""
    dpi = ax.figure.dpi
    dx_px = offset_pt[0] * dpi / 72.0
    dy_px = offset_pt[1] * dpi / 72.0
    disp = ax.transData.transform((x, y))
    xd, yd = ax.transData.inverted().transform((disp[0] + dx_px, disp[1] + dy_px))
    return float(xd), float(yd)


def _resolve_position(ax, x, y, text, fontsize, *, step, max_radius):
    """Nudge ``(x, y)`` clear of existing ink/labels via the declutter solver.

    Reuses ``figrecipe._declutter.solve_label_positions`` (the same
    deterministic ring-search solver behind ``scatter_labels``) instead of
    re-implementing collision avoidance. Best-effort: returns ``None`` (and
    warns) if the figure cannot be rendered or no clear spot is found, so
    the caller keeps the plain offset position -- never a silent fallback.
    """
    try:
        from .._declutter import solve_label_positions
        from .._quality._overlap import _render_ink_mask

        fig = ax.figure
        fig.canvas.draw()
        renderer = fig._get_renderer()

        anchor = tuple(ax.transData.transform((x, y)))
        temp = ax.text(0.0, 0.0, text, fontsize=fontsize, ha="center", va="center")
        try:
            bbox = temp.get_window_extent(renderer=renderer)
            size = (float(bbox.width), float(bbox.height))
        finally:
            temp.remove()

        rendered = _render_ink_mask(fig, None)
        ink_mask, height = rendered if rendered is not None else (None, 0)

        obstacles = []
        legend = ax.get_legend()
        if legend is not None and legend.get_visible():
            lb = legend.get_window_extent(renderer=renderer)
            obstacles.append((lb.x0, lb.y0, lb.x1, lb.y1))

        ab = ax.get_window_extent(renderer=renderer)
        clip_rect = (ab.x0, ab.y0, ab.x1, ab.y1)

        centers, placed_clear = solve_label_positions(
            [anchor],
            [size],
            ink_mask,
            height,
            obstacles,
            clip_rect,
            step=step,
            max_radius=max_radius,
        )
        if not placed_clear[0]:
            warnings.warn(
                "stx_annotate_n: no clear spot found within reach; label "
                "placed at its offset anchor (crowded axes -- consider "
                "enlarging the panel).",
                UserWarning,
                stacklevel=3,
            )
        cx, cy = centers[0]
        xd, yd = ax.transData.inverted().transform((cx, cy))
        return float(xd), float(yd)
    except Exception as exc:  # pragma: no cover - defensive, non-interactive backends
        warnings.warn(
            f"stx_annotate_n: overlap avoidance unavailable ({exc!r}); "
            "falling back to the plain offset position.",
            UserWarning,
            stacklevel=3,
        )
        return None


# EOF
