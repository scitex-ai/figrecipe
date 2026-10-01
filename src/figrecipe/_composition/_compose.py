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
from ._compose_builders import _compose_grid_based, _compose_mm_based

# Compatibility re-exports: these were reachable via ._compose before the
# builders were split out, and _import_axes imports _replay_axes_record from
# here. Kept so the split stays behaviour-neutral for importers.
from ._replay_record import (  # noqa: F401
    _replay_axes_record,
    _replay_axes_record_mm,
)
from ._source_parser import is_image_file as _is_image_file  # noqa: F401
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
    max_whitespace_frac: Optional[float] = None,
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
    max_whitespace_frac : float, optional
        Refuse the composite when more than this fraction of the canvas is
        blank — e.g. ``0.4`` raises above 40% whitespace, naming the measured
        figure and the largest empty regions. Omitted (the default) measures
        without enforcing: a composite over half blank warns, nothing raises.
        Enforcement is opt-in because a raising default would break every
        existing sparse composite at once.
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
        fig, axes = _compose_mm_based(
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
        fig, axes = _compose_mm_based(
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
        fig, axes = _compose_grid_based(
            sources,
            layout,
            panel_labels,
            label_style,
            caption=caption,
            panel_captions=panel_captions,
            **kwargs,
        )

    # Single exit so every composition mode is checked by one call. Two
    # compose-time quality checks live here:
    #  - width: an over-wide composite is not rejected downstream, it is
    #    silently shrunk by \resizebox along with its text.
    #  - whitespace: a mostly-blank composite wastes page and usually means the
    #    panels were sized for a different layout than the one they landed in.
    # Reading the finished figure covers all three composition modes without
    # per-mode geometry arithmetic.
    from .._quality._compose_whitespace import check_compose_whitespace
    from .._quality._compose_width import check_compose_width

    check_compose_width(fig, dpi=dpi)
    check_compose_whitespace(fig, max_whitespace_frac=max_whitespace_frac)
    return fig, axes


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




__all__ = ["compose"]
