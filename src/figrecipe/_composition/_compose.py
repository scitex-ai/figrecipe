#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main composition logic for combining multiple figures.

Supports two composition modes:
1. Grid-based: layout=(nrows, ncols) with sources={(row, col): path}
2. Mm-based: canvas_size_mm=(w, h) with sources={path: {"xy_mm": ..., "size_mm": ...}}

All layouts maintain matplotlib editability - no PIL image pasting.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from numpy.typing import NDArray

from .._recorder import FigureRecord
from .._utils._grid import grid_id, parse_grid_id
from .._wrappers import RecordingAxes, RecordingFigure
from ._crop_aware import _apply_source_style, panel_rel_bbox, replay_panel_suptitle
from ._source_parser import is_image_file as _is_image_file  # noqa: F401
from ._source_parser import parse_source_spec_with_key as _parse_source_spec_with_key
from ._source_parser import parse_source_spec_with_path as _parse_source_spec_with_path

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
    layout: Optional[Tuple[int, int]] = None,
    canvas_size_mm: Optional[Tuple[float, float]] = None,
    gap_mm: float = 2.0,
    dpi: int = DEFAULT_DPI,
    panel_labels: bool = False,
    label_style: str = "uppercase",
    caption: Optional[str] = None,
    panel_captions: Optional[List[str]] = None,
    **kwargs,
) -> Tuple[RecordingFigure, Union[RecordingAxes, NDArray, List[RecordingAxes]]]:
    """Compose a new figure from multiple sources (recipes or raw images).

    Supports two modes automatically detected from sources format:

    1. Grid-based: sources={(row, col): path}
       Uses layout=(nrows, ncols) for subplot grid.

    2. Mm-based: sources={path: {"xy_mm": (x, y), "size_mm": (w, h)}}
       Uses canvas_size_mm for precise positioning.

    Parameters
    ----------
    sources : dict
        Either:
        - Grid-based: {(row, col): source_path} mapping positions to sources
        - Mm-based: {source_path: {"xy_mm": (x, y), "size_mm": (w, h)}}
    layout : tuple, optional
        (nrows, ncols) for grid-based composition. Auto-detected if not provided.
    canvas_size_mm : tuple, optional
        (width_mm, height_mm) for mm-based composition. Required for mm-based mode.
    gap_mm : float
        Gap between panels in mm (for auto-layout modes like 'horizontal').
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
    """
    if _is_mm_based_sources(sources):
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
    # Suppress auto panel labels from global style; compose manages its own
    fig, axes = subplots(nrows=nrows, ncols=ncols, panel_labels=False, **kwargs)

    source_data_dirs = {}

    for (row, col), source_spec in sources.items():
        source_record, ax_key, source_path = _parse_source_spec_with_path(source_spec)
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

    # Render caption and panel captions for mm-based
    render_compose_captions(fig, axes_list, caption, panel_captions)

    return fig, axes_list


def _replay_axes_record_mm(
    mpl_ax,
    ax_record,
    fig_record: FigureRecord,
    idx: int,
    spec: Dict[str, Any],
) -> None:
    """Replay axes record for mm-based composition."""
    from .._reproducer._core import _replay_call

    result_cache: Dict[str, Any] = {}

    for call in ax_record.calls:
        result = _replay_call(mpl_ax, call, result_cache)
        if result is not None:
            result_cache[call.id] = result

    for call in ax_record.decorations:
        result = _replay_call(mpl_ax, call, result_cache)
        if result is not None:
            result_cache[call.id] = result

    ax_key = f"ax_mm_{idx}"
    ax_record_copy = ax_record
    ax_record_copy.mm_position = spec
    fig_record.axes[ax_key] = ax_record_copy


def _panel_label_fontsize() -> float:
    """Resolve the panel-label font size from the active SCITEX_STYLE.

    Default: 10pt bold (Nature-style panel labels).  Reads ``fonts.panel_label_pt``
    from SCITEX_STYLE if set; otherwise falls back to 10pt.  ``title_pt`` is
    *not* used as a fallback because panel labels (A, B, C, ...) follow a
    different convention than axis titles.
    """
    try:
        from ..presets._scitex_style import SCITEX_STYLE

        if isinstance(SCITEX_STYLE, dict):
            fonts = SCITEX_STYLE.get("fonts") or {}
            if "panel_label_pt" in fonts:
                return float(fonts["panel_label_pt"])
    except Exception:
        pass
    return 10.0


def _add_panel_labels_grid(axes, nrows: int, ncols: int, style: str) -> None:
    """Add panel labels to grid-based composition."""
    labels = _get_panel_labels(nrows * ncols, style)
    fs = _panel_label_fontsize()
    idx = 0
    for row in range(nrows):
        for col in range(ncols):
            ax = _get_axes_at(axes, row, col, nrows, ncols)
            mpl_ax = ax._ax if hasattr(ax, "_ax") else ax
            mpl_ax.text(
                -0.1,
                1.1,
                labels[idx],
                transform=mpl_ax.transAxes,
                fontsize=fs,
                fontweight="bold",
                va="top",
                ha="right",
            )
            idx += 1


def _add_panel_labels_mm(fig, sources: Dict, canvas_size_mm: Tuple, style: str) -> None:
    """Add panel labels to mm-based composition."""
    labels = _get_panel_labels(len(sources), style)
    fs = _panel_label_fontsize()
    for idx, (_, spec) in enumerate(sources.items()):
        xy_mm = spec["xy_mm"]
        x_frac = xy_mm[0] / canvas_size_mm[0]
        y_frac = 1.0 - xy_mm[1] / canvas_size_mm[1]
        fig.text(
            x_frac - 0.02,
            y_frac + 0.02,
            labels[idx],
            fontsize=fs,
            fontweight="bold",
            va="bottom",
            ha="right",
        )


def _get_panel_labels(n: int, style: str) -> List[str]:
    """Generate panel labels based on style."""
    if style == "uppercase":
        return [chr(ord("A") + i) for i in range(n)]
    elif style == "lowercase":
        return [chr(ord("a") + i) for i in range(n)]
    else:
        return [str(i + 1) for i in range(n)]


def _get_axes_at(
    axes: Union[RecordingAxes, NDArray],
    row: int,
    col: int,
    nrows: int,
    ncols: int,
) -> RecordingAxes:
    """Get axes at position, handling different array shapes."""
    if nrows == 1 and ncols == 1:
        return axes
    elif nrows == 1:
        return axes[col]
    elif ncols == 1:
        return axes[row]
    else:
        return axes[row, col]


def _replay_axes_record(
    target_ax: RecordingAxes,
    ax_record,
    fig_record: FigureRecord,
    row: int,
    col: int,
) -> None:
    """Replay all calls from ax_record onto target axes."""
    from .._reproducer._core import _replay_call

    mpl_ax = target_ax._ax if hasattr(target_ax, "_ax") else target_ax
    result_cache: Dict[str, Any] = {}

    for call in ax_record.calls:
        result = _replay_call(mpl_ax, call, result_cache)
        if result is not None:
            result_cache[call.id] = result

    for call in ax_record.decorations:
        result = _replay_call(mpl_ax, call, result_cache)
        if result is not None:
            result_cache[call.id] = result

    ax_key = grid_id(row, col)
    fig_record.axes[ax_key] = ax_record


__all__ = ["compose"]
