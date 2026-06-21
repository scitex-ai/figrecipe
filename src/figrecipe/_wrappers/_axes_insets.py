#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Record ``ax.inset_axes(...)`` so inset contents round-trip through a recipe.

The inset axes returned by this wrapper is itself a ``RecordingAxes`` backed by
a child ``Recorder``.  On ``fr.save()`` / ``fig.save_recipe()`` the child
recorder's calls are serialized into the parent ``AxesRecord.subpanels`` list.
On replay (``fr.reproduce()``) ``_replay_subpanels`` in the reproducer
reconstructs each inset and replays its calls.

Only ``inset_axes`` is supported here (PR-1).  ``embed(source)`` (PR-2) is a
separate feature and is not touched.

Depth guard: nested insets are written recursively by the reproducer but are
guarded at depth 5 (``_MAX_INSET_DEPTH``).  Creating nested insets during
recording is supported with no extra code — the child RecordingAxes returned
here can itself have ``inset_axes`` called on it.
"""

from typing import Any, Dict, List, Optional

_MAX_INSET_DEPTH = 5  # Hard cap for recursive replay; fail loud beyond this.

# Marker used when the caller passes no explicit transform (i.e., the default
# behaviour: bounds are fractions of the parent axes box → transAxes).
_DEFAULT_TRANSFORM_MARKER = "axes"


def _serialize_transform(transform, parent_ax) -> str:
    """Map a live matplotlib transform to a portable string marker.

    Parameters
    ----------
    transform :
        Live matplotlib transform, or ``None`` for the default.
    parent_ax :
        The underlying matplotlib axes the inset belongs to.

    Returns
    -------
    str
        ``"axes"`` | ``"data"`` | ``"figure"``.
    """
    if transform is None:
        return _DEFAULT_TRANSFORM_MARKER
    try:
        if transform is parent_ax.transAxes:
            return "axes"
        if transform is parent_ax.transData:
            return "data"
        fig = getattr(parent_ax, "figure", None)
        if fig is not None and transform is fig.transFigure:
            return "figure"
    except Exception:
        pass
    # Fallback: if the repr suggests axes-fraction, treat it as "axes".
    if "BboxTransformTo" in repr(transform):
        return "axes"
    return "axes"


def build_inset_axes_wrapper(recording_axes):
    """Return a wrapper for ``ax.inset_axes`` that records + returns a managed sub-panel.

    Parameters
    ----------
    recording_axes : RecordingAxes
        The parent recording axes on which ``inset_axes`` was called.

    Returns
    -------
    callable
        Replacement for ``ax.inset_axes`` that records the inset and returns
        a ``RecordingAxes`` so plots inside it are also captured.
    """

    def inset_axes(
        bounds: List[float],
        *,
        transform=None,
        id: Optional[str] = None,
        track: bool = True,
        **kwargs,
    ):
        """Create and record a managed inset axes.

        Parameters
        ----------
        bounds : list of float
            ``[x0, y0, width, height]`` in the coordinate frame set by
            ``transform`` (default: axes fraction).
        transform :
            Coordinate transform.  ``None`` means axes fraction (transAxes),
            matching matplotlib's default behaviour.
        id : str, optional
            Unused (kept for API symmetry with other wrappers).
        track : bool
            If ``False``, the inset is created but NOT recorded.
        **kwargs :
            Forwarded verbatim to ``matplotlib.axes.Axes.inset_axes``.

        Returns
        -------
        RecordingAxes
            Wrapped inset axes.  Plotting calls on it are captured and will
            be reproduced by ``fr.reproduce()``.
        """
        from .._recorder import Recorder
        from ._axes import RecordingAxes

        # Pass transform through to mpl only when explicitly given.
        mpl_kwargs: Dict[str, Any] = dict(kwargs)
        if transform is not None:
            mpl_kwargs["transform"] = transform

        inset_mpl = recording_axes._ax.inset_axes(bounds, **mpl_kwargs)

        # Always wrap in a RecordingAxes so the caller gets a consistent type.
        child_recorder = Recorder()
        child_recorder.start_figure()
        # Give the child a (0,0) position — it has exactly one axes.
        child_rax = RecordingAxes(inset_mpl, child_recorder, position=(0, 0))

        if recording_axes._track and track:
            transform_marker = _serialize_transform(transform, recording_axes._ax)
            parent_ax_rec = recording_axes._recorder.figure_record.get_or_create_axes(
                *recording_axes._position
            )
            parent_ax_rec.subpanel_recorders.append(
                {
                    "bounds": list(bounds),
                    "transform": transform_marker,
                    "recorder": child_recorder,
                }
            )

        return child_rax

    return inset_axes


__all__ = ["build_inset_axes_wrapper", "_MAX_INSET_DEPTH"]
