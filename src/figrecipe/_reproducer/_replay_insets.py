#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replay managed inset axes (sub-panels) recorded by ``ax.inset_axes``.

Counterpart to ``figrecipe/_wrappers/_axes_insets.py`` (the record side).

The entry point is ``replay_subpanels(parent_mpl_ax, axes_record, depth)``,
called from ``reproduce_from_record`` in ``_reproducer/_core.py`` after the
parent axes' own calls and decorations have been replayed.

Depth guard: we recurse for nested insets but hard-stop at
``_MAX_INSET_DEPTH`` (imported from the record-side module) and raise
``ValueError`` loudly so the author knows the limit was hit.
"""

from typing import Any, Dict

from .._wrappers._axes_insets import _MAX_INSET_DEPTH


def _resolve_transform(marker: str, ax):
    """Map a serialized transform marker back to a live mpl transform.

    Parameters
    ----------
    marker : str
        ``"axes"`` | ``"data"`` | ``"figure"``.
    ax :
        The matplotlib axes the inset lives inside.

    Returns
    -------
    matplotlib transform or ``None``
        ``None`` is returned for ``"axes"`` so that ``inset_axes`` uses its
        default (which is already transAxes — passing it explicitly is
        redundant and occasionally triggers deprecation warnings in some
        mpl builds).
    """
    if marker == "data":
        return ax.transData
    if marker == "figure":
        return ax.figure.transFigure
    # "axes" or anything else: let inset_axes use its default (transAxes).
    return None


def replay_subpanels(parent_mpl_ax, axes_record, depth: int = 0, style=None) -> None:
    """Replay all inset sub-panels recorded on *axes_record* onto *parent_mpl_ax*.

    Parameters
    ----------
    parent_mpl_ax :
        The (raw matplotlib) axes whose inset sub-panels need to be replayed.
    axes_record : AxesRecord
        The recorded parent axes, which may have a non-empty ``subpanels`` list.
    depth : int
        Current nesting depth.  Starts at 0 for top-level insets; incremented
        for each level of nesting.  Raises ``ValueError`` when it would exceed
        ``_MAX_INSET_DEPTH``.

    Raises
    ------
    ValueError
        When ``depth >= _MAX_INSET_DEPTH``.
    """
    if depth >= _MAX_INSET_DEPTH:
        raise ValueError(
            f"figrecipe inset nesting depth exceeded the limit of "
            f"{_MAX_INSET_DEPTH}. Flatten your inset hierarchy or raise "
            f"_MAX_INSET_DEPTH in _wrappers/_axes_insets.py."
        )

    # Gather sub-panels from EITHER the loaded form (`subpanels`, with rebuilt
    # AxesRecords) OR the live recording form (`subpanel_recorders`, holding live
    # child Recorders). The save-time validation reproduces from the LIVE record,
    # so both paths must be handled here.
    items = []
    loaded = getattr(axes_record, "subpanels", None)
    if loaded:
        for sp in loaded:
            items.append(
                (sp["bounds"], sp.get("transform", "axes"), sp.get("axes_record"))
            )
    else:
        for entry in getattr(axes_record, "subpanel_recorders", None) or []:
            child_axes = entry["recorder"].figure_record.axes
            items.append(
                (
                    entry["bounds"],
                    entry.get("transform", "axes"),
                    next(iter(child_axes.values()), None),
                )
            )
    if not items:
        return

    from ._core import _replay_call

    result_cache: Dict[str, Any] = {}

    for bounds, transform_marker, child_ax_rec in items:
        if child_ax_rec is None:
            continue

        # Reconstruct the inset with the stored transform.
        transform = _resolve_transform(transform_marker, parent_mpl_ax)
        inset_kwargs: Dict[str, Any] = {}
        if transform is not None:
            inset_kwargs["transform"] = transform

        inset_ax = parent_mpl_ax.inset_axes(bounds, **inset_kwargs)

        # Replay the inset's own plotting calls.
        for call in child_ax_rec.calls:
            result = _replay_call(inset_ax, call, result_cache)
            if result is not None:
                result_cache[call.id] = result

        # Replay the inset's decorations (set_xlabel, etc.).
        for call in child_ax_rec.decorations:
            result = _replay_call(inset_ax, call, result_cache)
            if result is not None:
                result_cache[call.id] = result

        # Apply the same per-axes finalization the grid reproducer uses, so an
        # inset's imshow/matrix tick styling matches the live (figrecipe-wrapped)
        # render. This is NOT apply_style_mm — insets keep their default full box;
        # only method-level finalization (e.g. matrix tick hiding) is applied.
        from ..styles._style_applier import finalize_special_plots, finalize_ticks

        finalize_ticks(inset_ax)
        finalize_special_plots(inset_ax, style or {})

        # Recurse for nested insets (depth guard prevents runaway recursion).
        replay_subpanels(inset_ax, child_ax_rec, depth=depth + 1, style=style)


__all__ = ["replay_subpanels"]
