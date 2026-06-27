#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Heal legacy mismatched tick recipes on reproduce.

figrecipe < 0.29.4 could serialize tick POSITIONS with a different count than
the labels (e.g. positions ``[0, 1]`` vs labels ``['8','16','24']``), so on
replay matplotlib raises "The number of FixedLocator locations (N) ... does not
match the number of labels (M)" and the axis renders garbled. These helpers
truncate/pin to the common length and WARN loudly instead of hard-failing.

This is a heal for ALREADY-SAVED recipes — current figrecipe records ticks
faithfully (positions paired with labels). Re-save a recipe with a current
figrecipe for a faithful round-trip.
"""

import warnings
from typing import Any, Dict, Tuple


def heal_tick_call(
    ax: Any, method_name: str, args: Tuple, kwargs: Dict[str, Any]
) -> Tuple[Tuple, Dict[str, Any]]:
    """Return (args, kwargs) with tick positions/labels reconciled in length."""
    if method_name in ("set_xticks", "set_yticks") and "labels" in kwargs:
        pos = args[0] if args else None
        labels = kwargs.get("labels")
        if pos is not None and labels is not None and len(pos) != len(labels):
            n = min(len(pos), len(labels))
            warnings.warn(
                f"figrecipe: healing {method_name} on load: positions "
                f"({len(pos)}) != labels ({len(labels)}) in this recipe; "
                f"truncating both to {n}. Re-save with a current figrecipe "
                f"for a faithful round-trip."
            )
            args = (list(pos)[:n],) + tuple(args[1:])
            kwargs = {**kwargs, "labels": list(labels)[:n]}
    elif method_name in ("set_xticklabels", "set_yticklabels") and args:
        labels = args[0]
        axis = method_name[4]  # 'x' or 'y'
        cur = list(getattr(ax, f"get_{axis}ticks")())
        if labels is not None and len(labels) != len(cur):
            warnings.warn(
                f"figrecipe: healing {method_name} on load: labels "
                f"({len(labels)}) != current tick positions ({len(cur)}); "
                f"pinning positions to match. Re-save with a current figrecipe "
                f"for fidelity."
            )
            getattr(ax, f"set_{axis}ticks")(cur)
            args = (list(labels)[: len(cur)],) + tuple(args[1:])
    return args, kwargs
