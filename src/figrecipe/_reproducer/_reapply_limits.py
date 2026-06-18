#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-apply recorded axis limits after replay so they always win (NeuroVista Ask 2).

A recipe records ``set_xlim`` / ``set_ylim`` as decorations, which already replay
after the plotting calls. But operations replayed *after* the decorations -- a
later ``set_xscale`` decoration that autoscales, inset sub-panels, colorbars, or
the tick/locator finalizers -- can re-engage matplotlib autoscaling and widen the
view away from the explicitly recorded limits.

To make the recorded limits authoritative, this module re-applies the LAST
recorded ``set_xlim`` / ``set_ylim`` for each axes once everything else is done.
"last wins" mirrors matplotlib's own behaviour when a user calls the setter more
than once. Only axes that actually recorded an explicit limit are touched, so
auto-scaled axes keep their auto behaviour.
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
    """Re-apply this axes' recorded set_xlim / set_ylim so they override autoscale.

    Parameters
    ----------
    ax :
        Target matplotlib axes (already fully replayed + finalized).
    ax_record : AxesRecord
        The recorded axes whose limit decorations should win.
    calls : list of str, optional
        If given, only re-apply limit decorations whose id is in this list
        (mirrors the same filter ``replay_axes_calls`` applies during replay).
    """
    xlim_args = _last_limit_args(ax_record, "set_xlim", calls)
    if xlim_args:
        _safe_set_lim(ax.set_xlim, xlim_args)

    ylim_args = _last_limit_args(ax_record, "set_ylim", calls)
    if ylim_args:
        _safe_set_lim(ax.set_ylim, ylim_args)


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
