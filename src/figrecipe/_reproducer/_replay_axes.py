#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replay one recorded axes (its calls, decorations, and inset sub-panels).

Extracted from ``_reproducer/_core.reproduce_from_record`` so the per-axes
replay sequence lives in one place and the grid reproducer stays a thin
orchestrator. Imports of the call dispatcher and inset replayer are lazy to
avoid an import cycle with ``_core``.
"""

from typing import Any, Dict, List, Optional


def replay_axes_calls(
    ax,
    ax_record,
    calls: Optional[List[str]],
    skip_decorations: bool,
    result_cache: Dict[str, Any],
    style: Optional[Dict[str, Any]] = None,
) -> None:
    """Replay an axes record's plotting calls, decorations, and inset sub-panels.

    Parameters
    ----------
    ax :
        Target matplotlib axes.
    ax_record : AxesRecord
        The recorded axes to replay.
    calls : list of str or None
        If given, only replay calls whose id is in this list.
    skip_decorations : bool
        If True, skip decoration calls.
    result_cache : dict
        Shared cache mapping call_id -> result (for cross-call references).
    """
    from ._core import _replay_call
    from ._replay_insets import replay_subpanels

    for call in ax_record.calls:
        if calls is not None and call.id not in calls:
            continue
        result = _replay_call(ax, call, result_cache)
        if result is not None:
            result_cache[call.id] = result

    if not skip_decorations:
        for call in ax_record.decorations:
            if calls is not None and call.id not in calls:
                continue
            result = _replay_call(ax, call, result_cache)
            if result is not None:
                result_cache[call.id] = result

    # Managed inset sub-panels (ax.inset_axes) recorded under this axes.
    replay_subpanels(ax, ax_record, depth=0, style=style)


__all__ = ["replay_axes_calls"]
