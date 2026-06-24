#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recording logic for ``RecordingFigure.colorbar`` (manual colorbar calls).

A manual ``fig.colorbar(...)`` / ``plt.colorbar(...)`` is recorded so it survives
a recipe round-trip: the recorder appends a ``colorbars`` entry (mirroring the
structure the AUTO path -- ``_maybe_add_colorbar`` -> ``RecordingFigure.colorbar``
-- already writes) and stashes the live ``Colorbar`` handle in ``live_colorbars``
so the save path can capture its resolved ``cax`` geometry
(``_capture_colorbar_geometry``) for an exact replay.

Two call forms beyond the basic ``ax=`` steal are handled here:

* Explicit ``cax=<axes>`` -- the colorbar is drawn into a caller-provided axes
  (e.g. a gridspec slot). ``cbar.ax`` IS that axes, so its settled geometry is
  captured at save and the reproducer pins it; no steal-set is needed.
* A STANDALONE ``ScalarMappable`` (``cm.ScalarMappable(cmap=, norm=)`` with no
  ``.axes`` -- the NeuroVista shared-comodulogram pattern). Such a mappable is
  NOT a recorded plot call, so replay cannot recover it from a plot result; we
  record a ``mappable_spec`` (cmap + clim) so the reproducer can rebuild it.

Extracted from ``_figure.py`` to keep that module within the per-file line
budget while keeping the colorbar recording rules in one cohesive place.
"""

from typing import TYPE_CHECKING, Any, List, Optional

from .._utils._grid import grid_id

if TYPE_CHECKING:
    from ._figure import RecordingFigure


def _key_for_axes(wrapped_fig: "RecordingFigure", mpl_ax) -> Optional[str]:
    """Return the grid id of the panel whose raw axes is ``mpl_ax`` (or None)."""
    if mpl_ax is None:
        return None
    for row in wrapped_fig._axes:
        for rec_ax in row:
            if rec_ax._ax is mpl_ax:
                return grid_id(rec_ax._position[0], rec_ax._position[1])
    return None


def _mappable_spec(mappable) -> Optional[dict]:
    """Capture cmap + clim so a STANDALONE ScalarMappable can be rebuilt on replay.

    Returns ``None`` when the mappable is tied to an axes (the reproducer then
    recovers it from that axes' recorded plot call) or when nothing useful can
    be read. Best-effort: a partial spec (cmap only) is still enough to rebuild.
    """
    if getattr(mappable, "axes", None) is not None:
        # Belongs to a panel -> replay finds it via that panel's plot call.
        return None
    spec: dict = {}
    try:
        cmap = mappable.get_cmap()
        name = getattr(cmap, "name", None)
        if name:
            spec["cmap"] = name
    except Exception:
        pass
    try:
        vmin, vmax = mappable.get_clim()
        if vmin is not None and vmax is not None:
            spec["vmin"] = float(vmin)
            spec["vmax"] = float(vmax)
    except Exception:
        pass
    return spec or None


def record_colorbar(wrapped_fig: "RecordingFigure", mappable, ax=None, **kwargs) -> Any:
    """Add a colorbar to ``wrapped_fig`` and record it for reproduction.

    Mirrors the colorbar entry the auto path writes so AUTO and MANUAL colorbars
    round-trip identically. See the module docstring for the ``cax=`` and
    standalone-``ScalarMappable`` cases.
    """
    # Normalize ``ax`` to a flat list of raw matplotlib axes, unwrapping any
    # RecordingAxes. Build the matching grid keys in the same order.
    if isinstance(ax, (list, tuple)):
        ax_seq = list(ax)
    elif hasattr(ax, "ravel") and not hasattr(ax, "_ax"):
        # numpy array of axes
        ax_seq = list(ax.ravel())
    elif ax is None:
        ax_seq = []
    else:
        ax_seq = [ax]

    mpl_axes = [getattr(a, "_ax", a) for a in ax_seq]

    ax_keys: List[str] = []
    for mpl_ax in mpl_axes:
        key = _key_for_axes(wrapped_fig, mpl_ax)
        if key is not None:
            ax_keys.append(key)

    # Identify the axes that OWNS the mappable (``mappable.axes``). With a
    # shared colorbar over a list of panels, the mappable belongs to ONE
    # specific panel (e.g. the last ``imshow``); its clim drives the colorbar
    # ticks. Recording this key lets replay pick the SAME mappable (hence the
    # same clim/ticks) rather than guessing the first panel. A standalone
    # ScalarMappable has no ``.axes`` -> this stays None.
    owner_ax = getattr(mappable, "axes", None)
    mappable_ax_key = _key_for_axes(wrapped_fig, owner_ax)

    # Explicit ``cax=<axes>``: the colorbar is drawn INTO this axes (unwrap a
    # RecordingAxes wrapper before handing it to matplotlib). Its settled
    # geometry is captured at save from the live handle, so we only need to keep
    # the raw axes; record its grid key too on the rare chance it IS a panel.
    cax = kwargs.pop("cax", None)
    cax_mpl = getattr(cax, "_ax", cax) if cax is not None else None
    cax_key = _key_for_axes(wrapped_fig, cax_mpl)

    # First matched key locates the mappable on replay (back-compat field).
    ax_key = mappable_ax_key or (ax_keys[0] if ax_keys else None)

    ser_kw = {
        k: v
        for k, v in kwargs.items()
        if isinstance(v, (str, int, float, bool, list, type(None)))
    }
    record = {"ax_key": ax_key, "kwargs": ser_kw}
    if ax_keys:
        record["ax_keys"] = ax_keys
    if mappable_ax_key is not None:
        record["mappable_ax_key"] = mappable_ax_key
    if cax_key is not None:
        record["cax_key"] = cax_key
    # Standalone mappable -> record enough to rebuild it on replay.
    spec = _mappable_spec(mappable)
    if spec is not None:
        record["mappable_spec"] = spec
    wrapped_fig._recorder.figure_record.colorbars.append(record)

    # ``fig.colorbar`` accepts a single axes, a sequence, or ``cax=`` -- pass the
    # unwrapped forms so matplotlib never sees a RecordingAxes wrapper.
    if cax_mpl is not None:
        cbar = wrapped_fig._fig.colorbar(mappable, cax=cax_mpl, **kwargs)
    else:
        cbar_ax = mpl_axes if len(mpl_axes) > 1 else (mpl_axes[0] if mpl_axes else None)
        cbar = wrapped_fig._fig.colorbar(mappable, ax=cbar_ax, **kwargs)
    # Stash the live colorbar so the save path can read its resolved cax
    # position (index-aligned with ``colorbars``).
    wrapped_fig._recorder.figure_record.live_colorbars.append(cbar)
    return cbar


__all__ = ["record_colorbar"]

# EOF
