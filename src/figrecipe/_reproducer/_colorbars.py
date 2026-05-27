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


def _replay_colorbars(fig, axes_2d, record, result_cache):
    """Replay recorded colorbars for exact reproduction."""
    colorbars = getattr(record, "colorbars", []) or []
    if not colorbars:
        # No recorded colorbars - nothing to do
        # (Old recipes without colorbar recording won't reproduce colorbars)
        return

    for cbar_info in colorbars:
        ax_key = cbar_info.get("ax_key")
        kwargs = cbar_info.get("kwargs", {})

        if ax_key is None:
            continue

        # Parse ax position (accepts "r0c0" or legacy "ax_0_0")
        parsed = parse_grid_id(ax_key)
        if parsed is None:
            continue
        row, col = parsed

        ax = axes_2d[row, col]

        # Find the mappable for this axes from result_cache
        ax_record = record.axes.get(ax_key)
        if ax_record is None:
            continue

        mappable = None
        method_name = None
        for call in ax_record.calls:
            if call.function in COLORBAR_METHODS and call.id in result_cache:
                mappable = result_cache[call.id]
                method_name = call.function
                break

        if mappable is None:
            continue

        # Some methods return tuples - extract the actual mappable
        if isinstance(mappable, tuple):
            if method_name == "hist2d":
                # hist2d returns (counts, xedges, yedges, image)
                mappable = mappable[3]
            elif method_name == "specgram":
                # specgram returns (spectrum, freqs, t, image)
                mappable = mappable[3]

        # Add colorbar with recorded kwargs - use raw fig.colorbar to avoid
        # add_colorbar adding extra styling kwargs that weren't in original
        cbar = fig.colorbar(mappable, ax=ax, **kwargs)

        # Apply styling to match original (style_colorbar is called by add_colorbar)
        from .._utils._colorbar import style_colorbar

        style_colorbar(cbar, record.style)


# EOF
