#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical row-major panel-letter derivation.

Single source of truth for "given a panel's (row, col) and the figure's
(nrows, ncols), what letter does the panel get?". This logic was inlined in
several places (panel-label rendering, CSV filename builder, separate-legend
filename builder) until 2026-06-15 — pulling it here ensures the figure
label, the legend-file label, and the data-file label all agree:

  panel A → top-left, row 0 col 0
  panel B → top row, second column
  …
  after the right-most column, wrap to the next row's left-most column.

For a 1x1 figure :func:`panel_label_for_position` returns ``None`` — single-
panel saves intentionally have no panel suffix on filenames and no panel
letter rendered on the figure (no clutter where the operator never thinks of
the figure as having "panels").

Panels beyond Z are not supported as letters; callers should fall back to a
numeric scheme if the figure grid is that large.
"""

from __future__ import annotations

from typing import Optional

__all__ = ["panel_label_for_position"]


def panel_label_for_position(
    row: int,
    col: int,
    nrows: Optional[int],
    ncols: Optional[int],
) -> Optional[str]:
    """Return the canonical panel letter for a panel at ``(row, col)``.

    Parameters
    ----------
    row, col : int
        Zero-based position of the panel in the figure grid.
    nrows, ncols : int or None
        Grid shape. ``None`` (legacy recipes from before nrows/ncols were
        recorded) is treated the same as a single-panel figure: returns
        ``None`` so callers strip the panel suffix.

    Returns
    -------
    str or None
        ``"A"``, ``"B"``, … for multi-panel figures. ``None`` for the 1x1
        case (or when the grid shape is unknown, or when the panel index
        exceeds Z).
    """
    if nrows is None or ncols is None:
        return None
    if nrows * ncols <= 1:
        return None
    idx = row * ncols + col
    if idx < 0 or idx >= 26:
        return None
    return chr(ord("A") + idx)


# EOF
