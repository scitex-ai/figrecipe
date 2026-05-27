#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: ./src/figrecipe/_utils/_grid.py

"""Single source of truth for grid (row, col) panel identifiers.

Both the YAML recipe ``axes:`` keys and the CSV column prefixes encode the
same concept — a panel's position in the subplot grid. To prevent the two
representations from drifting apart, both go through :func:`grid_id` here.

Canonical form::

    grid_id(0, 0) -> "r0c0"
    grid_id(1, 2) -> "r1c2"

Legacy form (still parsed for backward compatibility with old recipes)::

    ax_0_0, ax_1_2
"""

import re

__all__ = ["grid_id", "parse_grid_id"]

# Canonical: r{row}c{col}    Legacy: ax_{row}_{col}
_GRID_RE = re.compile(r"^r(\d+)c(\d+)$")
_LEGACY_RE = re.compile(r"^ax_(\d+)_(\d+)$")


def grid_id(row: int, col: int) -> str:
    """Return the canonical grid identifier for a panel position.

    Parameters
    ----------
    row : int
        Row position of the axes in the grid.
    col : int
        Column position of the axes in the grid.

    Returns
    -------
    str
        Canonical id like ``"r0c0"``.
    """
    return f"r{row}c{col}"


def parse_grid_id(key: str):
    """Parse a grid identifier into ``(row, col)``.

    Accepts BOTH the canonical ``r{row}c{col}`` form and the legacy
    ``ax_{row}_{col}`` form so old recipes keep loading.

    Parameters
    ----------
    key : str
        Grid identifier such as ``"r0c0"`` or ``"ax_0_0"``.

    Returns
    -------
    tuple[int, int] or None
        ``(row, col)`` if the key matched a known form, else ``None``.
    """
    if not key:
        return None
    match = _GRID_RE.match(key) or _LEGACY_RE.match(key)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None


# EOF
