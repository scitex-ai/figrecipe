#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The two composition BUILDERS, extracted from ``_compose.py``.

``_compose_grid_based`` lays panels out on a subplot grid; ``_compose_mm_based``
positions them by explicit millimetre boxes via ``add_axes`` (and is what the
tiled mode lowers to). Both are private to the composition package and are
called only by ``_compose.compose``.

Split out 2026-08-09: ``_compose.py`` had reached 513 lines, one over the repo
ceiling, so nothing further could be added to the public entry point. These two
are the bulk of the file and share nothing with the dispatcher but a call.

NOTE for ``_compose_mm_based``: ``xy_mm`` treats **y=0 as the TOP**, increasing
downward — see ``_tile.py``, which relies on that convention.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

from numpy.typing import NDArray

from .._utils._grid import grid_id, parse_grid_id
from .._wrappers import RecordingAxes, RecordingFigure
from ._caption_carry import auto_panel_captions_grid, auto_panel_captions_seq
from ._crop_aware import _apply_source_style, panel_rel_bbox, replay_panel_suptitle
from ._panel_labels import (
    _add_panel_labels_grid,
    _add_panel_labels_mm,
    _get_axes_at,
)
from ._replay_record import _replay_axes_record, _replay_axes_record_mm
from ._source_parser import parse_source_spec_with_key as _parse_source_spec_with_key
from ._source_parser import parse_source_spec_with_path as _parse_source_spec_with_path


def _mm_to_inch(mm: float) -> float:
    """Convert millimeters to inches."""
    return mm / 25.4


def _compose_grid_based(
    sources: Dict[Tuple[int, int], Any],
    layout: Optional[Tuple[int, int]],
    panel_labels: bool,
    label_style: str,
    caption: Optional[str],
    panel_captions: Optional[List[str]],
    **kwargs,
) -> Tuple[RecordingFigure, Union[RecordingAxes, NDArray]]:
    """Grid-based composition using subplots."""
    from .. import subplots
    from ._caption_render import render_compose_captions

    # Auto-detect layout from source positions
    if layout is None:
        if not sources:
            raise ValueError("sources cannot be empty")
        max_row = max(pos[0] for pos in sources.keys()) + 1
        max_col = max(pos[1] for pos in sources.keys()) + 1
        layout = (max_row, max_col)

    nrows, ncols = layout

    # No silent blanks: warn when the grid is under-filled (cells with no source
    # render empty). The agent-facing fr.empty_cells / fr.layout_report expose the
    # same info programmatically; the warning nudges toward a tiled layout.
    from ._layout_report import empty_cells

    _blanks = empty_cells((nrows, ncols), sources)
    if _blanks:
        import warnings

        warnings.warn(
            f"figrecipe.compose: grid {nrows}x{ncols} has {len(_blanks)} empty "
            f"cell(s) {_blanks} that will render blank. For tight page use, pass a "
            f"tiled layout=[[...],[...]] (whitespace-free), or fr.layout_report(fig) "
            f"/ fr.empty_cells(layout, sources) to inspect the blank regions."
        )

    # Suppress auto panel labels from global style; compose manages its own
    fig, axes = subplots(nrows=nrows, ncols=ncols, panel_labels=False, **kwargs)

    source_data_dirs = {}
    # Collect each source panel's own caption so compose can carry them forward
    # into the composed figure (see _auto_panel_captions below). Keyed by grid
    # position so the assembled list lines up with the row-major axes order.
    source_captions: Dict[Tuple[int, int], Optional[str]] = {}

    for (row, col), source_spec in sources.items():
        source_record, ax_key, source_path = _parse_source_spec_with_path(source_spec)
        source_captions[(row, col)] = getattr(source_record, "caption", None)
        # Accept either "rRcC" or legacy "ax_R_C" regardless of which form the
        # source record uses for its keys.
        ax_record = source_record.axes.get(ax_key)
        if ax_record is None:
            parsed_key = parse_grid_id(ax_key)
            if parsed_key is not None:
                for cand in (
                    grid_id(*parsed_key),
                    f"ax_{parsed_key[0]}_{parsed_key[1]}",
                ):
                    ax_record = source_record.axes.get(cand)
                    if ax_record is not None:
                        ax_key = cand
                        break

        if ax_record is None:
            available = list(source_record.axes.keys())
            raise ValueError(
                f"Axes '{ax_key}' not found in source. Available: {available}"
            )

        target_ax = _get_axes_at(axes, row, col, nrows, ncols)
        _replay_axes_record(target_ax, ax_record, fig.record, row, col)

        if source_path is not None:
            data_dir = source_path.parent / f"{source_path.stem}_data"
            if data_dir.exists():
                target_ax_key = grid_id(row, col)
                source_data_dirs[target_ax_key] = data_dir

    if source_data_dirs:
        fig.record.source_data_dirs = source_data_dirs

    # Mark composition figure for auto-crop on save (1mm margin, all sides)
    fig._mm_layout = {
        "crop_margin_left_mm": 1,
        "crop_margin_right_mm": 1,
        "crop_margin_top_mm": 1,
        "crop_margin_bottom_mm": 1,
    }

    # Add panel labels if requested
    if panel_labels:
        _add_panel_labels_grid(axes, nrows, ncols, label_style)

    # Carry source panel captions forward when the caller didn't pass any:
    # each panel's own record.caption becomes its (A)/(B)/... entry. Without
    # this the composed figure silently drops panel captions (same gap class
    # as composed colorbars).
    if panel_captions is None:
        panel_captions = auto_panel_captions_grid(source_captions, nrows, ncols)

    # Render caption and panel captions
    render_compose_captions(fig, axes, caption, panel_captions)

    return fig, axes


def _compose_mm_based(
    sources: Dict[str, Dict[str, Any]],
    canvas_size_mm: Optional[Tuple[float, float]],
    dpi: int,
    panel_labels: bool,
    label_style: str,
    caption: Optional[str],
    panel_captions: Optional[List[str]],
    **kwargs,
) -> Tuple[RecordingFigure, List[RecordingAxes]]:
    """Mm-based composition using fig.add_axes() for precise positioning."""
    import matplotlib
    import matplotlib.pyplot

    from .._recorder import Recorder
    from .._wrappers import RecordingAxes as RA
    from .._wrappers import RecordingFigure as RF
    from ._caption_render import render_compose_captions

    if canvas_size_mm is None:
        max_x = 0
        max_y = 0
        for spec in sources.values():
            xy = spec["xy_mm"]
            size = spec["size_mm"]
            max_x = max(max_x, xy[0] + size[0])
            max_y = max(max_y, xy[1] + size[1])
        canvas_size_mm = (max_x + 5, max_y + 5)

    width_inch = _mm_to_inch(canvas_size_mm[0])
    height_inch = _mm_to_inch(canvas_size_mm[1])

    mpl_fig = matplotlib.pyplot.figure(figsize=(width_inch, height_inch), dpi=dpi)

    recorder = Recorder()
    recorder.start_figure(figsize=(width_inch, height_inch), dpi=dpi)
    recorder.figure_record.composition_mode = "mm"
    recorder.figure_record.canvas_size_mm = canvas_size_mm

    axes_list = []
    source_data_dirs = {}
    # Per-source captions + axes-counts for caption carry-forward (see below).
    mm_source_captions: List[Optional[str]] = []
    mm_axis_counts: List[int] = []

    sub_idx = 0  # global counter for ax_mm_* keys across all panels + subplots
    for source_path, spec in sources.items():
        xy_mm = spec["xy_mm"]
        size_mm = spec["size_mm"]

        # Panel rectangle in figure-fraction coords.
        panel_left = xy_mm[0] / canvas_size_mm[0]
        panel_bottom = 1.0 - (xy_mm[1] + size_mm[1]) / canvas_size_mm[1]
        panel_width = size_mm[0] / canvas_size_mm[0]
        panel_height = size_mm[1] / canvas_size_mm[1]

        source_record, ax_key, path, explicit_key = _parse_source_spec_with_key(
            source_path
        )

        # Carry the panels' publication style onto the composed record so
        # reproduce() applies the SAME fonts/spines that live compose applies
        # per-panel via _apply_source_style. Without it the composed recipe has
        # no figure.style, so reproduce renders tick/axis-label text in
        # matplotlib's default font -- shifting text metrics and ghosting every
        # label against the live render. Panels share one style; first wins.
        if recorder.figure_record.style is None:
            _src_style = getattr(source_record, "style", None)
            if _src_style:
                recorder.figure_record.style = _src_style

        # Decide which axes of the source recipe to place into this panel.
        # An explicit (source, ax_key) tuple selects a single axes; a plain
        # recipe/path replays ALL of its axes (so multi-subplot panels such as
        # the stacked raw-iEEG traces keep every subplot, not just the first).
        if explicit_key:
            selected = {ax_key: source_record.axes.get(ax_key)}
            if selected[ax_key] is None:
                available = list(source_record.axes.keys())
                raise ValueError(
                    f"Axes '{ax_key}' not found in source. Available: {available}"
                )
        else:
            selected = dict(source_record.axes)
            if not selected:
                raise ValueError(f"Source '{source_path}' has no axes to compose.")

        mm_source_captions.append(getattr(source_record, "caption", None))
        mm_axis_counts.append(len(selected))

        data_dir = None
        if path is not None:
            candidate = path.parent / f"{path.stem}_data"
            if candidate.exists():
                data_dir = candidate

        for src_key, ax_record in selected.items():
            # Place this source-axes inside the panel rectangle relative to the
            # source's tight content box (crop-aware), so the composed panel
            # matches the clean cropped standalone render. Falls back to the
            # legacy cropped-fraction bbox for older recipes.
            bx0, by0, bw, bh = panel_rel_bbox(source_record, ax_record)

            sub_left = panel_left + bx0 * panel_width
            sub_bottom = panel_bottom + by0 * panel_height
            sub_width = bw * panel_width
            sub_height = bh * panel_height

            mpl_ax = mpl_fig.add_axes([sub_left, sub_bottom, sub_width, sub_height])
            # Record the EXACT add_axes input so the reproducer rebuilds this
            # panel by the same construction (add_axes(compose_bbox) then replay).
            # ``bbox``/``bbox_uncropped`` are POST-replay (a divider plotter's
            # main axes is already shrunken there), so only this PRE-replay input
            # reproduces divider panels -- and every panel -- pixel-for-pixel.
            ax_record.compose_bbox = [sub_left, sub_bottom, sub_width, sub_height]
            # Match the panel's publication font/style so replayed text metrics
            # equal the standalone render (else long tick labels clip).
            _apply_source_style(mpl_ax, source_record)

            target_ax = RA(mpl_ax, recorder, position=(0, sub_idx))
            axes_list.append(target_ax)

            _replay_axes_record_mm(
                mpl_ax, ax_record, recorder.figure_record, sub_idx, spec
            )

            if data_dir is not None:
                source_data_dirs[f"ax_mm_{sub_idx}"] = data_dir

            sub_idx += 1
        replay_panel_suptitle(
            mpl_fig, source_record, panel_left, panel_bottom, panel_width, panel_height
        )

    fig = RF(mpl_fig, recorder, axes_list)

    if source_data_dirs:
        fig.record.source_data_dirs = source_data_dirs

    # Mark composition figure for auto-crop on save (1mm margin, all sides)
    fig._mm_layout = {
        "crop_margin_left_mm": 1,
        "crop_margin_right_mm": 1,
        "crop_margin_top_mm": 1,
        "crop_margin_bottom_mm": 1,
    }

    if panel_labels:
        _add_panel_labels_mm(mpl_fig, sources, canvas_size_mm, label_style)

    # Carry source panel captions forward when the caller didn't pass any
    # (only when each source contributed exactly one axes — see helper).
    if panel_captions is None:
        panel_captions = auto_panel_captions_seq(mm_source_captions, mm_axis_counts)

    # Render caption and panel captions for mm-based
    render_compose_captions(fig, axes_list, caption, panel_captions)

    return fig, axes_list


__all__ = ["_compose_grid_based", "_compose_mm_based"]

# EOF
