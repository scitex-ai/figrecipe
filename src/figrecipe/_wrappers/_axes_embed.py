#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""``ax.embed(source, bounds)`` — embed a recipe or diagram as a managed sub-panel.

Builds directly on the inset substrate (``_axes_insets`` / ``_replay_insets``):
each axes of the parsed *source* is drawn into a managed inset placed at the
source axes' recorded position within ``bounds``, and the source's recorded
calls are attached to that inset's child recorder. Serialization and replay are
then handled by the inset substrate for free (live + loaded paths, finalize).

Supported sources (via ``_composition._source_parser``): a ``.yaml`` recipe, an
image (with companion recipe), a ``FigureRecord``, a diagram recipe (its axes
holds a ``diagram`` call), a composed multi-panel recipe (each panel embedded at
its recorded bbox), or ``(source, ax_key)`` to embed one panel.
"""

from typing import List, Optional


def embed_source(
    recording_axes,
    source,
    bounds: Optional[List[float]] = None,
    *,
    ax_key: Optional[str] = None,
    track: bool = True,
    id: Optional[str] = None,
):
    """Embed *source* into ``recording_axes`` within ``bounds`` (axes fraction)."""
    from .._composition._crop_aware import panel_rel_bbox
    from .._composition._source_parser import parse_source_spec_with_key

    if bounds is None:
        bounds = [0.0, 0.0, 1.0, 1.0]
    if ax_key is not None:
        source = (source, ax_key)

    record, sel_key, _path, explicit = parse_source_spec_with_key(source)
    if explicit:
        selected = {sel_key: record.axes[sel_key]}
    else:
        selected = dict(record.axes)
    if not selected:
        raise ValueError("ax.embed: source has no axes to embed")

    insets = []
    for src_ax_rec in selected.values():
        # Place this source axes at its recorded position, scaled into `bounds`.
        rel = panel_rel_bbox(record, src_ax_rec)
        inset_bounds = [
            bounds[0] + rel[0] * bounds[2],
            bounds[1] + rel[1] * bounds[3],
            rel[2] * bounds[2],
            rel[3] * bounds[3],
        ]
        inset_rax = recording_axes.inset_axes(inset_bounds, track=track, id=id)
        _draw_and_record_source(recording_axes, inset_rax, src_ax_rec)
        insets.append(inset_rax)

    return insets[0] if len(insets) == 1 else insets


def _draw_and_record_source(parent_rax, inset_rax, src_ax_rec) -> None:
    """Draw a source AxesRecord into the inset (live) and attach its recorded
    calls to the inset's child recorder so it round-trips via the inset substrate."""
    from .._reproducer._core import _replay_call
    from ..styles._style_applier import finalize_special_plots, finalize_ticks

    mpl_ax = inset_rax._ax
    cache: dict = {}
    for call in list(src_ax_rec.calls):
        result = _replay_call(mpl_ax, call, cache)
        if result is not None:
            cache[call.id] = result
    for call in list(src_ax_rec.decorations):
        result = _replay_call(mpl_ax, call, cache)
        if result is not None:
            cache[call.id] = result

    # Finalize with the PARENT figure's style — matches what replay_subpanels
    # applies on reproduce, so the live render and the replay agree.
    style = parent_rax._recorder.figure_record.style or {}
    finalize_ticks(mpl_ax)
    finalize_special_plots(mpl_ax, style)

    # Record: attach the source's CallRecords (already serialized) directly to the
    # inset's child recorder — NOT via record_call (which would re-serialize raw
    # args). The inset substrate serializes/replays these as the sub-panel.
    if inset_rax._track:
        child_axes = inset_rax._recorder.figure_record.axes
        child_ax_rec = next(iter(child_axes.values()), None)
        if child_ax_rec is None:
            child_ax_rec = inset_rax._recorder.figure_record.get_or_create_axes(0, 0)
        child_ax_rec.calls.extend(src_ax_rec.calls)
        child_ax_rec.decorations.extend(src_ax_rec.decorations)


__all__ = ["embed_source"]
