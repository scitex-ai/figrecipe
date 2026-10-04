#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save-time capture of resolved live-figure geometry for faithful replay.

Extracted from ``_save_helpers.py`` to keep that module under the per-file line
budget. These helpers run on the LIVE matplotlib figure at save (after
``settle_constrained_layout``) and stash the resolved geometry onto
``fig.record`` so the reproducer can pin it exactly instead of re-deriving it.
"""


def _capture_colorbar_geometry(fig) -> None:
    """Record each colorbar's resolved cax position so replay can pin it.

    A shared colorbar (``fig.colorbar(im, ax=[...])``) steals space from its
    source panels, and under ``constrained_layout`` the amount stolen is
    draw-history-dependent -- a freshly ``reproduce()``-d figure that re-steals
    lands on a DIFFERENT cax width than the original, so the tight-cropped image
    comes out a different pixel size (validator SIZE mismatch). Capturing the
    colorbar Axes' settled ``get_position()`` here (this runs after
    ``settle_constrained_layout``, on the live figure) lets the reproducer place
    the colorbar at that EXACT rectangle via ``add_axes`` instead of re-stealing.

    Stored as ``cax_bbox = [left, bottom, width, height]`` in UNCROPPED figure
    fraction (matching ``add_axes`` input). Best-effort and index-aligned with
    ``record.colorbars`` via the transient ``record.live_colorbars`` handles;
    on any mismatch the entry is left without ``cax_bbox`` and replay falls back
    to the legacy ``ax=`` re-steal path.
    """
    live = getattr(fig.record, "live_colorbars", None) or []
    colorbars = fig.record.colorbars or []
    for cbar, cbar_rec in zip(live, colorbars):
        try:
            cax = cbar.ax
            pos = cax.get_position()
            cbar_rec["cax_bbox"] = [
                float(pos.x0),
                float(pos.y0),
                float(pos.width),
                float(pos.height),
            ]
        except Exception:
            # Leave cax_bbox unset -> reproducer uses the legacy ax= path.
            continue
        # Also record the resolved tick positions. A colorbar built with a
        # stolen host axes (``ax=``) and one pinned to a fixed ``cax=`` pick
        # DIFFERENT default tick counts even at identical clim + size (matplotlib
        # initialises the locator differently per mode), and the tick LABELS
        # drive the colorbar's outboard ink -> a SIZE mismatch. Replaying the
        # exact ticks makes the two render identically.
        try:
            ticks = cbar.get_ticks()
            cbar_rec["cax_ticks"] = [float(t) for t in ticks]
        except Exception:
            pass
        # Also record the resolved colorbar presentation (outline width, tick
        # size, label size). An automatically styled colorbar (add_colorbar)
        # and a manually built one (bare fig.colorbar) carry DIFFERENT artist
        # properties at identical geometry; replaying geometry alone restores
        # a default-styled colorbar over a styled original (heavier outline,
        # longer ticks, shifted labels). Replaying the captured values
        # restores the original appearance without re-deriving style.
        try:
            major_ticks = cbar.ax.yaxis.get_major_ticks()
            first = major_ticks[0]
            cbar_rec["cax_presentation"] = {
                "outline_linewidth": float(cbar.ax.spines["outline"].get_linewidth()),
                "tick_width": float(first.tick2line.get_markeredgewidth()),
                "tick_length": float(first.tick2line.get_markersize()),
                "tick_pad": float(first.get_pad()),
                "label_fontsize": float(first.label2.get_fontsize()),
            }
        except Exception:
            pass


__all__ = ["_capture_colorbar_geometry"]
