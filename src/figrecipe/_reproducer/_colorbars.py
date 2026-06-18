#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Colorbar replay for figure reproduction."""

from .._utils._grid import parse_grid_id

# 2D plot methods that return ScalarMappable (for finding mappable)
COLORBAR_METHODS = {
    "imshow",
    "pcolormesh",
    "pcolor",
    "contourf",
    "contour",
    "hexbin",
    "hist2d",
    "tripcolor",
    "tricontourf",
    "tricontour",
    "matshow",
    "spy",
    "specgram",
}

# Colorbar kwargs that only matter when matplotlib STEALS space from a host
# axes (the ``ax=`` path). When we instead pin the colorbar to a fixed ``cax``
# rectangle, these have no effect (and ``shrink``/``aspect``/``fraction`` are
# rejected by ``fig.colorbar(cax=...)``), so they are dropped on that path.
_STEAL_ONLY_KWARGS = {
    "ax",
    "shrink",
    "pad",
    "fraction",
    "aspect",
    "anchor",
    "panchor",
    "use_gridspec",
    "location",
}


def _grid_positions(ax_keys):
    """Yield the (row, col) tuples for parseable grid keys."""
    for key in ax_keys:
        parsed = parse_grid_id(key)
        if parsed is not None:
            yield parsed


def _find_mappable(record, ax_key, result_cache):
    """Return the ScalarMappable recorded on ``ax_key`` (or None)."""
    ax_record = record.axes.get(ax_key)
    if ax_record is None:
        return None
    for call in ax_record.calls:
        if call.function in COLORBAR_METHODS and call.id in result_cache:
            mappable = result_cache[call.id]
            # Some methods return tuples -- extract the actual image mappable.
            if isinstance(mappable, tuple):
                if call.function in ("hist2d", "specgram"):
                    mappable = mappable[3]
            return mappable
    return None


def _pin_source_axes(record, axes_2d, ax_keys):
    """Pin each source axes to its recorded (settled) position.

    A shared colorbar shrank these panels in the original; the reproducer's
    constrained_layout, with no colorbar stealing space, would otherwise place
    them at their FULL (no-colorbar) positions. Re-applying the recorded bbox
    restores the original tile rectangles so the pinned cax lines up and the
    cropped image matches the original pixel size.

    Pins to ``bbox_uncropped`` (the panel's position in the UNCROPPED figure
    fraction) when available: the figure is saved full-canvas and only then
    cropped to ``content_bbox``, so the reproduce must place panels at their
    full-canvas positions (``set_position`` is figure-fraction). The cropped
    ``bbox`` is in the post-crop frame and would shift every panel. Legacy
    recipes saved with ``bbox_inches="tight"`` have no crop offset, so their
    ``bbox`` already equals ``bbox_uncropped`` and the fallback is exact.
    """
    for key in ax_keys:
        parsed = parse_grid_id(key)
        if parsed is None:
            continue
        row, col = parsed
        try:
            ax = axes_2d[row, col]
        except (IndexError, KeyError):
            continue
        ax_record = record.axes.get(key)
        bbox = getattr(ax_record, "bbox_uncropped", None) if ax_record else None
        if bbox is None or len(bbox) != 4:
            bbox = getattr(ax_record, "bbox", None) if ax_record else None
        if bbox is not None and len(bbox) == 4:
            ax.set_position(bbox)


def _replay_colorbars(fig, axes_2d, record, result_cache):
    """Replay recorded colorbars for exact reproduction.

    For each recorded colorbar:

    * If ``cax_bbox`` was captured (current recipes), pin the colorbar to that
      exact figure-fraction rectangle via ``add_axes`` + ``colorbar(cax=...)``,
      pin its source panels to their recorded positions, and take them all out
      of the layout solver so the deterministic tight save can't re-flow them.
      This reproduces a shared colorbar's geometry exactly (the legacy re-steal
      does not -- it is draw-history-dependent under constrained_layout).
    * Otherwise (legacy recipes) fall back to the original ``ax=`` re-steal.
    """
    colorbars = getattr(record, "colorbars", []) or []
    if not colorbars:
        # No recorded colorbars - nothing to do
        # (Old recipes without colorbar recording won't reproduce colorbars)
        return

    from .._utils._colorbar import style_colorbar

    for cbar_info in colorbars:
        ax_key = cbar_info.get("ax_key")
        kwargs = dict(cbar_info.get("kwargs", {}))
        cax_bbox = cbar_info.get("cax_bbox")

        if ax_key is None:
            continue

        parsed = parse_grid_id(ax_key)
        if parsed is None:
            continue

        mappable = _find_mappable(record, ax_key, result_cache)
        if mappable is None:
            continue

        if cax_bbox is not None and len(cax_bbox) == 4:
            # --- Pinned-geometry path (deterministic) ---------------------
            # Pin the source panels to their recorded rectangles, place the
            # colorbar at the captured rectangle, and freeze every axes out of
            # the layout (``set_in_layout(False)``) so the deterministic
            # ``bbox_inches="tight"`` save reproduces the ORIGINAL pixels.
            #
            # NB: ``style_colorbar`` is intentionally NOT called here. The live
            # ``fig.colorbar`` recording path does not style the colorbar, so the
            # original carries matplotlib's default tick length / outline. Re-
            # styling on replay would shorten the ticks and shift the outboard
            # ink (a SIZE/MSE mismatch). The recorded ``cax_bbox`` (geometry),
            # ``cax_ticks`` (labels) and the replayed rcParams already reproduce
            # the colorbar's appearance exactly.
            ax_keys = cbar_info.get("ax_keys") or [ax_key]
            _pin_source_axes(record, axes_2d, ax_keys)
            cax = fig.add_axes(cax_bbox)
            pinned_kwargs = {
                k: v for k, v in kwargs.items() if k not in _STEAL_ONLY_KWARGS
            }
            cbar = fig.colorbar(mappable, cax=cax, **pinned_kwargs)
            cax.set_position(cax_bbox)  # colorbar() can nudge the cax; re-pin.

            # Force the recorded ticks. ``set_ticks`` with explicit values turns
            # autoscale back on and expands the cax to span the tick range (e.g.
            # ticks [-4..3] -> ylim [-4, 3]) -- but the original's cax spans its
            # CLIM, with out-of-range ticks simply clipped. Restore the colorbar-
            # creation (clim) ylim afterwards so the gradient maps identically.
            cax_ticks = cbar_info.get("cax_ticks")
            if cax_ticks:
                clim_ylim = cbar.ax.get_ylim()
                try:
                    cbar.set_ticks(cax_ticks)
                    cbar.ax.set_ylim(clim_ylim)
                except Exception:
                    pass

            # Freeze: keep constrained_layout enabled (so the save still uses the
            # deterministic tight path) but take the pinned axes out of the solver
            # so the save-time re-solve can't move them.
            for managed in (*[axes_2d[p] for p in _grid_positions(ax_keys)], cax):
                try:
                    managed.set_in_layout(False)
                except Exception:
                    pass
        else:
            # --- Legacy re-steal path (pre-cax_bbox recipes) --------------
            row, col = parsed
            ax = axes_2d[row, col]
            kwargs.pop("ax", None)
            cbar = fig.colorbar(mappable, ax=ax, **kwargs)
            # Apply styling to match original (style_colorbar called by add_colorbar)
            style_colorbar(cbar, record.style)


# EOF
