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


def finalize_imshow_axes(ax, ax_record, style: Optional[Dict[str, Any]]) -> None:
    """Reapply imshow tick/spine suppression so reproduce matches save.

    The live ``ax.imshow`` wrapper (``_wrappers/_axes_plots.imshow_plot``)
    hides ticks + spines for *any* ``imshow`` when the style's
    ``imshow.show_axes`` is False. On replay the recorded ``imshow`` runs as
    raw matplotlib (no wrapper) and ``finalize_special_plots`` skips
    suppression whenever the axes carries an axis label (its ``is_specgram``
    heuristic) -- so a *labelled* ``imshow`` (e.g. a comodulogram with
    ``set_xyt``) reproduced WITH the numeric ticks the original hid, failing
    reproducibility validation. The faithful discriminator is the recorded
    call name -- exactly what the live wrapper keys on -- so suppression runs
    only for an axes that actually has an ``imshow`` call, never for a genuine
    ``ax.specgram`` (which the live wrapper never touched).

    Crucially this must honour the live render's *order*. The live wrapper
    suppresses chrome DURING the imshow call, so a user ``set_xticks`` /
    ``set_yticks`` issued AFTER imshow overrides the suppression and DOES show
    in the saved figure (a comodulogram whose author deliberately labels the
    Hz bands). On replay those tick calls are decorations already replayed
    before this post-pass, so clearing unconditionally would wipe the user's
    explicit ticks -- live shows them, reproduce hid them, and the recipe then
    fails its own pixel validation. So suppress only the axis dimension the
    recipe did NOT explicitly tick; an explicit ``set_xticks([])`` likewise
    counts as user-controlled and is left exactly as the decoration set it.
    Spines are never restored by a tick decoration, so they follow
    ``show_axes`` regardless. Axis labels are left intact (any present were
    re-set by ``set_xlabel``/``set_ylabel`` decorations, matching the live
    figure).

    Parameters
    ----------
    ax :
        Target matplotlib axes (raw, post-replay).
    ax_record : AxesRecord
        The recorded axes -- inspected for an ``imshow`` call and for explicit
        tick decorations.
    style : dict or None
        The recipe's (flat) style. ``imshow_show_axes`` gates suppression.
    """
    has_imshow = any(c.function == "imshow" for c in ax_record.calls)
    if not has_imshow:
        return

    show_axes = (style or {}).get("imshow_show_axes", True)
    if show_axes:
        return

    decorations = ax_record.decorations
    if not any(c.function == "set_xticks" for c in decorations):
        ax.set_xticks([])
        ax.set_xticklabels([])
    if not any(c.function == "set_yticks" for c in decorations):
        ax.set_yticks([])
        ax.set_yticklabels([])
    for spine in ax.spines.values():
        spine.set_visible(False)


__all__ = ["replay_axes_calls", "finalize_imshow_axes"]
