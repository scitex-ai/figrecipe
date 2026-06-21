#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-apply recorded axis limits after replay so they always win (NeuroVista Ask 2).

A recipe records ``set_xlim`` / ``set_ylim`` as decorations, which already replay
after the plotting calls. But operations replayed *after* the decorations -- a
later ``set_xscale`` decoration that autoscales, inset sub-panels, colorbars, or
the tick/locator finalizers -- can re-engage matplotlib autoscaling and widen the
view away from the explicitly recorded limits.

To make the recorded limits authoritative, this module re-applies, once everything
else is done, the axes' FINAL rendered view limits captured at save time
(``AxesRecord.final_xlim`` / ``final_ylim``) when present. Those are the true
last-rendered state, so they win over autoscale AND faithfully reproduce a
legitimate later change -- e.g. ``rotate_labels`` re-runs the tick locator and
snaps ``set_ylim(0, 24)`` out to ``(0, 25)``; replaying only the ``set_ylim``
*args* would wrongly revert that. Legacy recipes (saved before final limits were
captured) fall back to the LAST recorded ``set_xlim`` / ``set_ylim`` args, which
"last wins" mirrors matplotlib's own behaviour when a user calls the setter more
than once. Only axes that recorded a final limit (or an explicit setter) are
touched, so auto-scaled axes keep their auto behaviour.
"""

from typing import Any, List, Optional

from ._axis_coerce import coerce_axis_value


def _last_limit_args(
    ax_record, method_name: str, calls: Optional[List[str]]
) -> Optional[list]:
    """Return the args of the last recorded ``method_name`` decoration, or None.

    Honors the ``calls`` id-filter: a limit decoration excluded from replay must
    not be re-applied either.
    """
    last = None
    for call in ax_record.decorations:
        if call.function != method_name:
            continue
        if calls is not None and call.id not in calls:
            continue
        last = call
    if last is None:
        return None

    from ._reconstruct import reconstruct_value

    return [coerce_axis_value(reconstruct_value(a, {})) for a in last.args]


def reapply_recorded_limits(ax, ax_record, calls: Optional[List[str]] = None) -> None:
    """Re-apply this axes' recorded final view limits so they override autoscale.

    Prefers the FINAL rendered limits captured at save time
    (``final_xlim`` / ``final_ylim``) -- the true last-rendered state, which both
    beats autoscale and reproduces a legitimate later change (e.g. rotate_labels
    snapping the view to the outermost tick). Falls back to the LAST recorded
    ``set_xlim`` / ``set_ylim`` args for legacy recipes that lack final limits.

    Parameters
    ----------
    ax :
        Target matplotlib axes (already fully replayed + finalized).
    ax_record : AxesRecord
        The recorded axes whose final limits / limit decorations should win.
    calls : list of str, optional
        If given, only re-apply limit decorations whose id is in this list
        (mirrors the same filter ``replay_axes_calls`` applies during replay).
        Captured final limits reflect the FULL render, so they are used only when
        no ``calls`` filter is active; a filtered replay uses the decoration args.
    """
    # The captured final limits describe the whole-figure render, so honor them
    # only for an unfiltered reproduce; a partial (calls-filtered) replay must
    # defer to the per-decoration args, which respect the same id filter.
    use_final = calls is None
    final_xlim = getattr(ax_record, "final_xlim", None) if use_final else None
    final_ylim = getattr(ax_record, "final_ylim", None) if use_final else None

    xlim = (
        list(final_xlim)
        if final_xlim is not None
        else _last_limit_args(ax_record, "set_xlim", calls)
    )
    if xlim:
        _safe_set_lim(ax.set_xlim, xlim)

    ylim = (
        list(final_ylim)
        if final_ylim is not None
        else _last_limit_args(ax_record, "set_ylim", calls)
    )
    if ylim:
        _safe_set_lim(ax.set_ylim, ylim)


def _safe_set_lim(setter, args: list) -> Any:
    """Apply a limit setter, warning (not crashing) if matplotlib rejects it."""
    try:
        return setter(*args)
    except Exception as e:
        import warnings

        warnings.warn(f"Failed to re-apply recorded limits via {setter!r}: {e}")
        return None


__all__ = ["reapply_recorded_limits"]

# EOF
