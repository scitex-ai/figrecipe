#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Reconcile legacy mismatched tick recipes on reproduce.

figrecipe < 0.29.4 could serialize tick POSITIONS with a different count than
the labels (e.g. positions ``[0, 1]`` vs labels ``['8','16','24']``), so on
replay matplotlib raises "The number of FixedLocator locations (N) ... does not
match the number of labels (M)" and the axis renders garbled.

Two mismatches are possible, and they are NOT the same problem:

``set_[xy]ticks(positions, labels=...)``
    Both sequences are authored and index-paired, so truncating to the common
    length keeps every surviving label on a position its author chose. Entries
    are lost from the tail; nothing is moved. Applied, with a warning.

``set_[xy]ticklabels(labels)``
    Only the labels are authored — the positions come from whatever the axis
    happens to carry at replay time, typically matplotlib's automatic ticks.
    Truncating the labels onto those positions yields an axis that is not
    degraded but WRONG, and that looks fine: 19 category labels become 10
    labels sitting on auto positions no one authored. For a scientific figure
    that is the worst outcome, because a blank axis reads as broken while a
    mislabeled axis reads as data. So the call is DROPPED and the axis keeps
    its default ticks — honest degradation instead of invented placement.

Re-save a recipe with a current figrecipe for a faithful round-trip; current
figrecipe pairs positions with labels and reaches neither branch.
"""

import warnings
from typing import Any, Dict, Tuple

from ._replay_action import ReplayArgs


def _warn(message: str) -> None:
    warnings.warn(message, UserWarning, stacklevel=3)


def heal_tick_call(
    ax: Any, method_name: str, args: Tuple, kwargs: Dict[str, Any]
) -> ReplayArgs:
    """Inspect one recorded tick call and say how to replay it.

    Returns a :class:`ReplayArgs`. Callers MUST honour ``action``: an ``APPLY``
    result carries the (possibly adjusted) arguments to call with, and a
    ``SKIP`` result means the call must not be made at all.
    """
    if method_name in ("set_xticks", "set_yticks") and "labels" in kwargs:
        pos = args[0] if args else None
        labels = kwargs.get("labels")
        if pos is not None and labels is not None and len(pos) != len(labels):
            n = min(len(pos), len(labels))
            dropped = max(len(pos), len(labels)) - n
            reason = (
                f"figrecipe: this recipe records {method_name} with "
                f"{len(pos)} tick positions but {len(labels)} labels. "
                f"Positions and labels are paired in order, so both are "
                f"truncated to {n} — every surviving label stays on a position "
                f"the recipe authored, and {dropped} trailing "
                f"{'entry is' if dropped == 1 else 'entries are'} dropped. "
                f"Re-save with a current figrecipe for a faithful round-trip."
            )
            _warn(reason)
            return ReplayArgs.apply(
                args=(list(pos)[:n],) + tuple(args[1:]),
                kwargs={**kwargs, "labels": list(labels)[:n]},
                reason=reason,
            )

    elif method_name in ("set_xticklabels", "set_yticklabels") and args:
        labels = args[0]
        axis = method_name[4]  # 'x' or 'y'
        cur = list(getattr(ax, f"get_{axis}ticks")())
        if labels is not None and len(labels) != len(cur):
            reason = (
                f"figrecipe: DROPPING {method_name} from this recipe. It "
                f"records {len(labels)} labels but the axis carries "
                f"{len(cur)} tick position(s) at replay, and the recipe does "
                f"not say where those labels belong. Placing them on the "
                f"current positions would MISLABEL the {axis} axis with values "
                f"no one authored, which looks correct and is not, so the axis "
                f"keeps its default ticks instead. Re-save with a current "
                f"figrecipe to restore the intended labels."
            )
            _warn(reason)
            return ReplayArgs.skip(args=args, kwargs=kwargs, reason=reason)

    return ReplayArgs.apply(args=args, kwargs=kwargs)


__all__ = [
    "heal_tick_call",
]
