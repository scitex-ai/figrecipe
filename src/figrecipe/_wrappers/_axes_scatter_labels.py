#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""``scatter_labels(declutter=True)`` -- deterministic, recorded point labels.

Labels a set of data points so the labels avoid each other, the data ink, and
the legend, with optional leader lines. The declutter solver runs ONCE here at
record time (``figrecipe._declutter.solve_label_positions``); every label is
then emitted through the RECORDED ``text``/``annotate`` path at its resolved
coordinates, so the recipe replays byte-identically with no solver in the replay
path (that is why an iterative library like adjustText can't be used directly --
its post-hoc moves would not be recorded).
"""

from __future__ import annotations

import warnings
from typing import Optional, Sequence

# Draw a leader line only when the label center ends up at least this many
# display pixels from its point (a label sitting on its point needs no leader).
_LEADER_MIN_DISP = 14.0

# A panel this covered in ink leaves the solver no free space, so every label
# would fall back to its point and the declutter would quietly do nothing. Real
# data ink never fills this much of a panel; a mask this full means the
# background was misread (or the panel is a full-bleed image), so say so instead
# of degrading in silence.
_INK_SATURATED = 0.95


class ScatterLabelsMixin:
    """Mixin adding ``scatter_labels`` to ``RecordingAxes``."""

    def scatter_labels(
        self,
        x: Sequence[float],
        y: Sequence[float],
        labels: Sequence[str],
        *,
        declutter: bool = True,
        avoid: str = "ink",
        leader_lines: bool = False,
        clip: bool = True,
        fontsize: Optional[float] = None,
        id: Optional[str] = None,
        **text_kwargs,
    ):
        """Label points at ``(x, y)`` with deterministic clutter avoidance.

        With ``declutter=True`` each label is repelled off the data ink, the
        legend, and the other labels via a seedless ring search, then drawn as a
        recorded ``text`` at its solved position (plus a recorded leader
        ``annotate`` when ``leader_lines`` and the label moved). ``avoid="ink"``
        rasterizes the current data (markers + lines + error bars) to avoid ALL
        ink, not just point centers; ``avoid="points"`` skips the raster.
        ``clip`` keeps labels inside the axes. Any label with no clear spot is
        left at its point and a warning is emitted (never silently dropped).
        """
        import numpy as np

        xs = np.atleast_1d(np.asarray(x, dtype=float))
        ys = np.atleast_1d(np.asarray(y, dtype=float))
        labels = list(labels)
        if not (len(xs) == len(ys) == len(labels)):
            raise ValueError(
                "scatter_labels: x, y, and labels must have equal length "
                f"(got {len(xs)}, {len(ys)}, {len(labels)})"
            )

        ax = self._ax
        fs = fontsize if fontsize is not None else _resolve_fontsize(ax)

        if not declutter:
            for xi, yi, lab in zip(xs, ys, labels):
                self.text(float(xi), float(yi), lab, fontsize=fs, **text_kwargs)
            return

        fig = ax.figure
        fig.canvas.draw()
        renderer = fig._get_renderer()

        anchors = [
            tuple(ax.transData.transform((float(xi), float(yi))))
            for xi, yi in zip(xs, ys)
        ]
        sizes = _measure_labels(ax, labels, fs, renderer)

        ink_mask, height = None, 0
        if avoid == "ink":
            from .._quality._overlap import _render_ink_mask

            # No style dict here, so _render_ink_mask resolves the background
            # from the figure itself -- without that it assumed white, and a
            # dark-theme panel rasterized as 100% ink (nowhere to put a label).
            rendered = _render_ink_mask(fig, None)
            if rendered is not None:
                ink_mask, height = rendered
                _warn_if_ink_saturated(ink_mask, height, ax, renderer)

        obstacles = _legend_obstacles(ax, renderer)
        clip_rect = None
        if clip:
            ab = ax.get_window_extent(renderer=renderer)
            clip_rect = (ab.x0, ab.y0, ab.x1, ab.y1)

        from .._declutter import solve_label_positions

        centers, placed_clear = solve_label_positions(
            anchors, sizes, ink_mask, height, obstacles, clip_rect
        )

        inv = ax.transData.inverted()
        n_fallback = 0
        for anchor, (cx, cy), (xi, yi), lab, ok in zip(
            anchors, centers, zip(xs, ys), labels, placed_clear
        ):
            xd, yd = inv.transform((cx, cy))
            self.text(
                float(xd),
                float(yd),
                lab,
                fontsize=fs,
                ha="center",
                va="center",
                **text_kwargs,
            )
            moved = ((cx - anchor[0]) ** 2 + (cy - anchor[1]) ** 2) ** 0.5
            if leader_lines and ok and moved >= _LEADER_MIN_DISP:
                self.annotate(
                    "",
                    xy=(float(xi), float(yi)),
                    xytext=(float(xd), float(yd)),
                    arrowprops={"arrowstyle": "-", "lw": 0.5},
                )
            if not ok:
                n_fallback += 1

        if n_fallback:
            warnings.warn(
                f"scatter_labels: {n_fallback} of {len(labels)} label(s) had no "
                "clear spot and were left on their point (crowded axes -- enlarge "
                "the panel or label fewer points).",
                UserWarning,
                stacklevel=2,
            )


def _warn_if_ink_saturated(ink_mask, height, ax, renderer) -> None:
    """Warn when the ink raster is so full that no label can be placed.

    Measured over the AXES, not the whole canvas: labels are clipped to the
    axes, so the surrounding figure margins are free space the solver can never
    use. A full-bleed heatmap saturates its panel while leaving those margins
    empty, which a canvas-wide mean would score as plenty of room.
    """
    from .._quality._overlap_ink import _ink_fraction_in_bbox

    bbox = ax.get_window_extent(renderer=renderer)
    if _ink_fraction_in_bbox(ink_mask, height, bbox) <= _INK_SATURATED:
        return
    warnings.warn(
        "scatter_labels: the data-ink raster is almost fully saturated, so the "
        "declutter solver has no free space and every label will stay on its "
        "point. This usually means the figure background was not recognised "
        "(a custom background color) or the panel is a full-bleed image; "
        "declutter cannot help here -- pass avoid='points' to skip the raster.",
        UserWarning,
        stacklevel=3,
    )


def _resolve_fontsize(ax) -> float:
    """Inline-label font size: axes tick size if set, else rcParams default."""
    import matplotlib as mpl

    for tick in ax.get_xticklabels():
        size = tick.get_fontsize()
        if size:
            return float(size)
    return float(mpl.rcParams.get("font.size", 10.0))


def _measure_labels(ax, labels, fontsize, renderer):
    """Display-coord (w, h) of each label, measured with UNRECORDED text.

    The temp Text is drawn with the same fontsize the final label uses, then
    removed before recording, so it never enters the recipe.
    """
    sizes = []
    for lab in labels:
        temp = ax.text(0.0, 0.0, lab, fontsize=fontsize, ha="center", va="center")
        try:
            bbox = temp.get_window_extent(renderer=renderer)
            sizes.append((float(bbox.width), float(bbox.height)))
        finally:
            temp.remove()
    return sizes


def _legend_obstacles(ax, renderer):
    """Legend bbox(es) as display-coord obstacle rects for the solver."""
    obstacles = []
    legend = ax.get_legend()
    if legend is not None and legend.get_visible():
        try:
            lb = legend.get_window_extent(renderer=renderer)
            obstacles.append((lb.x0, lb.y0, lb.x1, lb.y1))
        except Exception:
            pass
    return obstacles


__all__ = ["ScatterLabelsMixin"]

# EOF
