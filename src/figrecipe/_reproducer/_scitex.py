#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replay for figrecipe's ``stx_*`` scitex-compat plot methods.

These methods (recorded as ``stx_scatter_hist``, ``stx_raster``, ...) are
implemented as *functions* that take a plain matplotlib ``Axes`` as the first
argument (see ``figrecipe._scitex_compat``).  On replay the target is a raw
matplotlib axes (e.g. the ``add_axes`` panel created by mm-composition), which
does NOT carry the ``stx_*`` methods that ``RecordingAxes`` exposes — so a
plain ``getattr(ax, "stx_scatter_hist")`` dispatch returns ``None`` and the
call is silently dropped.  This module dispatches such calls to the underlying
compat functions so the plot (and any marginal axes it creates internally via
``make_axes_locatable``) is faithfully reconstructed.
"""

from typing import Any, Callable, Dict, Optional

from matplotlib.axes import Axes

from .._recorder import CallRecord


def _resolve_stx_function(method_name: str) -> Optional[Callable]:
    """Return the compat function for an ``stx_*`` method name, or None."""
    # Import lazily so optional deps don't break import of this module.
    try:
        from .._scitex_compat import _heatmap, _scientific, _shaded_lines, _simple
    except Exception:
        return None

    registry: Dict[str, Callable] = {}
    for module in (_scientific, _shaded_lines, _simple, _heatmap):
        for name in dir(module):
            if name.startswith("stx_"):
                registry[name] = getattr(module, name)
    return registry.get(method_name)


def replay_stx_call(
    ax: Axes, call: CallRecord, result_cache: Optional[Dict[str, Any]] = None
) -> Any:
    """Replay an ``stx_*`` compat call on a (possibly raw) matplotlib axes.

    Parameters
    ----------
    ax : Axes
        Target matplotlib axes (raw or RecordingAxes-wrapped).
    call : CallRecord
        The recorded ``stx_*`` call.
    result_cache : dict, optional
        Cache mapping call_id -> result (for reference resolution).

    Returns
    -------
    Any
        Result of the compat function, or None if it could not be replayed.
    """
    from ._reconstruct import reconstruct_kwargs, reconstruct_value

    func = _resolve_stx_function(call.function)
    # Prefer a bound method when the axes already exposes it (RecordingAxes);
    # this keeps behaviour identical to direct reproduce for wrapped axes.
    bound = getattr(ax, call.function, None)

    if func is None and bound is None:
        return None

    args = []
    for arg_data in call.args:
        args.append(reconstruct_value(arg_data, result_cache))
    kwargs = reconstruct_kwargs(call.kwargs)

    try:
        if bound is not None and func is None:
            return bound(*args, **kwargs)
        # Compat functions take the raw mpl axes as the first positional arg.
        mpl_ax = ax._ax if hasattr(ax, "_ax") else ax
        return func(mpl_ax, *args, **kwargs)
    except Exception as e:
        import warnings

        warnings.warn(f"Failed to replay {call.function}: {e}")
        return None


__all__ = ["replay_stx_call"]

# EOF
