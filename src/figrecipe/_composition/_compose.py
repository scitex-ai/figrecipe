#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main composition logic for combining multiple figures.

Supports three composition modes:
1. Grid-based: layout=(nrows, ncols) with sources={(row, col): path}
2. Mm-based: canvas_size_mm=(w, h) with sources={path: {"xy_mm": ..., "size_mm": ...}}
3. Tiled: layout=[["A","B"],["C"]] with sources={"A": path, ...} (row-justified,
   aspect-preserving, whitespace-free) -- see ``_tile.py``.

All layouts maintain matplotlib editability - no PIL image pasting.
"""

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
from ._source_parser import is_image_file as _is_image_file  # noqa: F401
from ._source_parser import parse_source_spec_with_key as _parse_source_spec_with_key
from ._source_parser import parse_source_spec_with_path as _parse_source_spec_with_path
from ._tile import _is_tiled_layout, build_tiled_sources

# Default DPI for mm-based composition
DEFAULT_DPI = 300


def _is_mm_based_sources(sources: Dict) -> bool:
    """Check if sources dict uses mm-based positioning."""
    if not sources:
        return False
    first_key = next(iter(sources.keys()))
    if isinstance(first_key, tuple):
        return False
    first_value = sources[first_key]
    return isinstance(first_value, dict) and "xy_mm" in first_value


def _mm_to_inch(mm: float) -> float:
    """Convert millimeters to inches."""
    return mm / 25.4


def compose(
    sources: Dict[Any, Any],
    layout: Optional[Union[Tuple[int, int], str, List[List[str]]]] = None,
    canvas_size_mm: Optional[Tuple[float, float]] = None,
    width_mm: Optional[float] = None,
    gap_mm: float = 2.0,
    dpi: int = DEFAULT_DPI,
    panel_labels: bool = False,
    label_style: str = "uppercase",
    caption: Optional[str] = None,
    panel_captions: Optional[List[str]] = None,
    **kwargs,
) -> Tuple[RecordingFigure, Union[RecordingAxes, NDArray, List[RecordingAxes]]]:
    """Compose a new figure from multiple sources (recipes or raw images).

    Supports three modes automatically detected from sources/layout format:

    1. Grid-based: sources={(row, col): path}
       Uses layout=(nrows, ncols) for subplot grid.

    2. Mm-based: sources={path: {"xy_mm": (x, y), "size_mm": (w, h)}}
       Uses canvas_size_mm for precise positioning.

    3. Tiled (row-justified, whitespace-free): layout=[["A","B","C"],["D"]]
       (or the multiline string "A B C\\nD") with sources={"A": path, ...}.
       Each panel keeps its true aspect ratio; within a row all panels share
       one common height and sit edge-to-edge (only ``gap_mm`` between) so
       there is no whitespace, and every row spans the same width so the
       right edge is never ragged. The first layout row is rendered on top.

    Parameters
    ----------
    sources : dict
        One of:
        - Grid-based: {(row, col): source_path} mapping positions to sources
        - Mm-based: {source_path: {"xy_mm": (x, y), "size_mm": (w, h)}}
        - Tiled: {label: source} keyed by the string labels used in ``layout``
    layout : tuple, str, or list of list of str, optional
        - (nrows, ncols) for grid-based composition (auto-detected if omitted).
        - list of rows of labels (``[["A","B"],["C"]]``) or a multiline string
          (``"A B\\nC"``) for tiled composition.
    canvas_size_mm : tuple, optional
        (width_mm, height_mm) for mm-based composition. Required for mm-based mode.
    width_mm : float, optional
        Overall content width (mm) for TILED composition. When omitted the
        default width is the widest row at its true content size, i.e.
        ``max over rows of (sum of true panel widths + (k-1)*gap_mm)``.
        Ignored by grid/mm modes.
    gap_mm : float
        Gap between panels in mm (gutter; tiled mode uses it as the edge-to-edge
        spacing, and ``gap_mm=0`` makes panels share edges exactly).
    dpi : int
        DPI for the output figure.
    panel_labels : bool
        If True, add panel labels (A, B, C...) to each panel.
    label_style : str
        'uppercase', 'lowercase', or 'numeric'.
    caption : str, optional
        Figure-level caption text.  Rendered on the figure and persisted
        in the recipe so it survives save→reproduce.
    panel_captions : list of str, optional
        Per-panel caption texts.  When provided, panel labels (A, B, C...)
        are placed with the corresponding caption text on each panel.
    **kwargs
        Additional arguments passed to figure creation.

    Returns
    -------
    fig : RecordingFigure
        Composed figure (editable, recordable).
    axes : RecordingAxes, ndarray, or list
        Axes of the composed figure.

    Examples
    --------
    Grid-based composition:

    >>> fig, axes = fr.compose(
    ...     layout=(1, 2),
    ...     sources={
    ...         (0, 0): "panel_a.yaml",
    ...         (0, 1): "panel_b.yaml",
    ...     }
    ... )

    Composition with figure-level caption:

    >>> fig, axes = fr.compose(
    ...     layout=(2, 2),
    ...     sources={
    ...         (0, 0): "a.yaml", (0, 1): "b.yaml",
    ...         (1, 0): "c.yaml", (1, 1): "d.yaml",
    ...     },
    ...     caption="Figure 1. Four-condition comparison (n=3).",
    ... )

    Mm-based free-form composition:

    >>> fig, axes = fr.compose(
    ...     canvas_size_mm=(180, 120),
    ...     sources={
    ...         "panel_a.yaml": {"xy_mm": (0, 0), "size_mm": (85, 55)},
    ...         "panel_b.yaml": {"xy_mm": (90, 0), "size_mm": (85, 55)},
    ...         "panel_c.yaml": {"xy_mm": (0, 60), "size_mm": (175, 55)},
    ...     }
    ... )

    Tiled (row-justified, whitespace-free) composition:

    >>> fig, axes = fr.compose(
    ...     layout=[["A", "B", "C"], ["D"]],
    ...     sources={"A": "a.yaml", "B": "b.yaml",
    ...              "C": "c.yaml", "D": "d.yaml"},
    ...     width_mm=180, gap_mm=1.0,
    ... )
    """
    if _is_tiled_layout(layout, sources):
        sources_mm, computed_canvas = _tiled_to_mm_sources(
            layout,
            sources,
            width_mm=width_mm,
            canvas_size_mm=canvas_size_mm,
            gap_mm=gap_mm,
        )
        return _compose_mm_based(
            sources_mm,
            computed_canvas,
            dpi,
            panel_labels,
            label_style,
            caption=caption,
            panel_captions=panel_captions,
            **kwargs,
        )
    elif _is_mm_based_sources(sources):
        return _compose_mm_based(
            sources,
            canvas_size_mm,
            dpi,
            panel_labels,
            label_style,
            caption=caption,
            panel_captions=panel_captions,
            **kwargs,
        )
    else:
        return _compose_grid_based(
            sources,
            layout,
            panel_labels,
            label_style,
            caption=caption,
            panel_captions=panel_captions,
            **kwargs,
        )


def _tiled_to_mm_sources(
    layout: Union[str, List[List[str]]],
    sources: Dict[str, Any],
    width_mm: Optional[float],
    canvas_size_mm: Optional[Tuple[float, float]],
    gap_mm: float,
) -> Tuple[Dict[str, Dict[str, Any]], Tuple[float, float]]:
    """Adapter over ``_tile.build_tiled_sources`` (the whitespace-free,
    aspect-preserving algorithm). ``canvas_size_mm[0]`` supplies the width when
    ``width_mm`` is omitted; the dispatcher then delegates to ``_compose_mm_based``.
    """
    effective_width = width_mm
    if effective_width is None and canvas_size_mm is not None:
        effective_width = canvas_size_mm[0]
    return build_tiled_sources(layout, sources, width_mm=effective_width, gap_mm=gap_mm)


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


__all__ = ["compose"]
