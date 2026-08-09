#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Record-time guards: refuse to SAVE a tick recipe that cannot round-trip.

The doctrine (figrecipe-record-replay-completeness): there must be no
"drawn but not reproducible" state. If the recorder cannot faithfully replay
something that was drawn, say so AT SAVE TIME rather than emit a recipe that
quietly reproduces a different figure.

Two guards, covering the two ways a tick recipe goes wrong:

``FR-FAITHFUL-TICKS`` — per call.
    ``set_[xy]ticks(positions, labels=...)`` carrying a different number of
    positions than labels. Replay would raise "FixedLocator locations != labels".

``FR-FAITHFUL-TICKLABELS`` — across calls within one axes.
    ``set_[xy]ticklabels(labels)`` whose count disagrees with the positions the
    SAME axes pinned earlier via ``set_[xy]ticks``. Nothing raises on replay
    here — the labels simply cannot be placed, and figrecipe drops them (see
    ``_reproducer/_tick_heal``) rather than pinning them onto matplotlib's
    automatic positions and mislabeling the axis. Dropping is the right
    behaviour on LOAD, but a recipe that will need it is one we should not have
    written, and at save time we still know it is wrong.

DELIBERATELY NOT GUARDED: a ``set_[xy]ticklabels`` with NO recorded
``set_[xy]ticks`` for that axis. The label placement then depends on tick state
some PLOTTER established (a bar chart's categorical positions, imshow's
extent), which is legitimate and extremely common. Raising there would reject
correct recipes — a false positive multiplied by every stored figure — and the
count comparison available here cannot tell that case from a broken one. It
needs the live axis state at record time, not a count across calls.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

#: Axis letter for each tick-setting function, e.g. "set_xticks" -> "x".
_TICK_FUNCS = {"set_xticks": "x", "set_yticks": "y"}
_TICKLABEL_FUNCS = {"set_xticklabels": "x", "set_yticklabels": "y"}


def _seq_len(arg: Any) -> Optional[int]:
    """Length of a serialized sequence arg, or None if not determinable.

    Recorded args arrive as dicts carrying either a live ``_array`` (recording
    in memory) or serialized ``data`` (loaded from YAML). Anything else — a
    scalar, a reference, a shape this function does not recognise — returns
    None, and every caller treats None as "cannot tell" rather than guessing.
    """
    if isinstance(arg, dict):
        if "_array" in arg:
            try:
                return len(arg["_array"])
            except TypeError:
                return None
        data = arg.get("data")
        if isinstance(data, list):
            return len(data)
        return None
    if isinstance(arg, (list, tuple)):
        return len(arg)
    return None


def assert_tick_call_faithful(call: Dict[str, Any]) -> None:
    """FR-FAITHFUL-TICKS: positions and labels must agree in count."""
    if call.get("function") not in _TICK_FUNCS:
        return
    labels = call.get("kwargs", {}).get("labels")
    args = call.get("args", [])
    if labels is None or not args:
        return
    n_pos = _seq_len(args[0])
    if n_pos is None:
        return  # positions length not determinable here; skip
    if n_pos != len(labels):
        raise ValueError(
            f"figrecipe [FR-FAITHFUL-TICKS]: {call.get('function')} recorded "
            f"{n_pos} tick positions but {len(labels)} labels (call "
            f"{call.get('id')}). This recipe would not round-trip (replay would "
            f"raise FixedLocator count != labels) -- indicates a recording/"
            f"serialization bug. Not shipping a mismatched recipe."
        )


def assert_ticklabel_calls_faithful(call_list: List[Dict[str, Any]]) -> None:
    """FR-FAITHFUL-TICKLABELS: labels must fit the positions the axes pinned.

    Scans one axes' calls IN ORDER, remembering the position count from each
    ``set_[xy]ticks``, and checks every later ``set_[xy]ticklabels`` on the same
    axis against it. Only the unambiguous case raises — see the module docstring
    for the case that is deliberately left alone.
    """
    pinned: Dict[str, int] = {}
    for call in call_list:
        func = call.get("function")

        axis = _TICK_FUNCS.get(func)
        if axis is not None:
            args = call.get("args", [])
            n_pos = _seq_len(args[0]) if args else None
            if n_pos is not None:
                pinned[axis] = n_pos
            continue

        axis = _TICKLABEL_FUNCS.get(func)
        if axis is None:
            continue
        args = call.get("args", [])
        n_labels = _seq_len(args[0]) if args else None
        n_pos = pinned.get(axis)
        # No recorded set_[xy]ticks for this axis, or a count we cannot read:
        # not our case. Say nothing rather than guess.
        if n_labels is None or n_pos is None or n_labels == n_pos:
            continue
        raise ValueError(
            f"figrecipe [FR-FAITHFUL-TICKLABELS]: {func} records {n_labels} "
            f"labels but this axes pinned {n_pos} tick position(s) via "
            f"set_{axis}ticks (call {call.get('id')}). Those labels cannot be "
            f"placed on replay, so the axis would lose them -- a figure that "
            f"draws now and reproduces WITHOUT its {axis}-axis labels. Fix the "
            f"recording (pass labels to set_{axis}ticks, which keeps positions "
            f"and labels paired) rather than shipping a recipe that needs "
            f"healing on load."
        )


__all__ = [
    "assert_tick_call_faithful",
    "assert_ticklabel_calls_faithful",
]

# EOF
