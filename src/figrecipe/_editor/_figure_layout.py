#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figure-level layout handling for the editor.

Applies spacing and margin overrides to figure layout via subplots_adjust.
"""

from typing import Any, Dict, Optional

from matplotlib.figure import Figure

from .._utils._grid import parse_grid_id


def apply_figure_layout_overrides(
    fig: Figure, overrides: Dict[str, Any], record: Optional[Any] = None
) -> None:
    """Apply figure-level layout overrides (spacing, margins).

    Converts mm-based spacing and margin values to subplots_adjust parameters.

    Parameters
    ----------
    fig : Figure
        Matplotlib figure.
    overrides : dict
        Style overrides containing spacing_horizontal_mm, spacing_vertical_mm,
        margins_left_mm, margins_right_mm, margins_bottom_mm, margins_top_mm.
    record : FigureRecord, optional
        Recording record to get original layout and axes dimensions.
    """
    # Check if any layout overrides are present
    spacing_h = overrides.get("spacing_horizontal_mm")
    spacing_v = overrides.get("spacing_vertical_mm")
    margin_l = overrides.get("margins_left_mm")
    margin_r = overrides.get("margins_right_mm")
    margin_b = overrides.get("margins_bottom_mm")
    margin_t = overrides.get("margins_top_mm")

    has_layout_overrides = any(
        v is not None
        for v in [spacing_h, spacing_v, margin_l, margin_r, margin_b, margin_t]
    )

    if not has_layout_overrides:
        return

    # Skip if figure uses constrained_layout (incompatible with subplots_adjust)
    layout_engine = fig.get_layout_engine()
    if layout_engine is not None:
        layout_name = getattr(layout_engine, "__class__", type(layout_engine)).__name__
        if "Constrained" in layout_name:
            return

    # Get current figure size in inches
    fig_width_inch, fig_height_inch = fig.get_size_inches()

    # Convert to mm (1 inch = 25.4 mm)
    fig_width_mm = fig_width_inch * 25.4
    fig_height_mm = fig_height_inch * 25.4

    # Determine grid dimensions from axes
    axes_list = fig.get_axes()
    if not axes_list:
        return

    nrows, ncols = _get_grid_dimensions(record, axes_list)

    # Get current layout parameters
    current_params = fig.subplotpars
    current_left = current_params.left
    current_right = current_params.right
    current_bottom = current_params.bottom
    current_top = current_params.top
    current_wspace = current_params.wspace
    current_hspace = current_params.hspace

    # Calculate current mm values from figure layout
    current_ml_mm = current_left * fig_width_mm
    current_mr_mm = (1 - current_right) * fig_width_mm
    current_mb_mm = current_bottom * fig_height_mm
    current_mt_mm = (1 - current_top) * fig_height_mm

    # Calculate axes dimensions
    aw, ah = _calculate_axes_dimensions(
        fig_width_mm,
        fig_height_mm,
        current_ml_mm,
        current_mr_mm,
        current_mb_mm,
        current_mt_mm,
        current_wspace,
        current_hspace,
        nrows,
        ncols,
    )

    # Apply overrides (use current values as fallback)
    ml = margin_l if margin_l is not None else current_ml_mm
    mr = margin_r if margin_r is not None else current_mr_mm
    mb = margin_b if margin_b is not None else current_mb_mm
    mt = margin_t if margin_t is not None else current_mt_mm
    sw = (
        spacing_h
        if spacing_h is not None
        else (current_wspace * aw if ncols > 1 else 0)
    )
    sh = (
        spacing_v
        if spacing_v is not None
        else (current_hspace * ah if nrows > 1 else 0)
    )

    # Calculate new layout parameters
    left = ml / fig_width_mm
    right = 1 - (mr / fig_width_mm)
    bottom = mb / fig_height_mm
    top = 1 - (mt / fig_height_mm)

    # Calculate wspace/hspace as fraction of axes dimensions
    wspace = sw / aw if ncols > 1 and aw > 0 else 0
    hspace = sh / ah if nrows > 1 and ah > 0 else 0

    # Apply the layout (suppress warning about layout engine incompatibility
    # since we've already checked and skipped constrained_layout figures)
    import warnings

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", "This figure was using a layout engine")
        fig.subplots_adjust(
            left=left,
            right=right,
            bottom=bottom,
            top=top,
            wspace=wspace,
            hspace=hspace,
        )


def _get_grid_dimensions(record: Optional[Any], axes_list: list) -> tuple:
    """Get grid dimensions from record or infer from axes.

    Returns
    -------
    tuple
        (nrows, ncols)
    """
    nrows, ncols = 1, 1

    if record and hasattr(record, "axes"):
        for ax_key in record.axes.keys():
            parsed = parse_grid_id(ax_key)
            if parsed is not None:
                nrows = max(nrows, parsed[0] + 1)
                ncols = max(ncols, parsed[1] + 1)
    else:
        # Infer from axes count (assume square-ish grid)
        import math

        n_axes = len(axes_list)
        ncols = int(math.ceil(math.sqrt(n_axes)))
        nrows = int(math.ceil(n_axes / ncols))

    return nrows, ncols


def _calculate_axes_dimensions(
    fig_width_mm: float,
    fig_height_mm: float,
    ml_mm: float,
    mr_mm: float,
    mb_mm: float,
    mt_mm: float,
    wspace: float,
    hspace: float,
    nrows: int,
    ncols: int,
) -> tuple:
    """Calculate single axes dimensions from figure layout.

    Returns
    -------
    tuple
        (axes_width_mm, axes_height_mm)
    """
    content_width_mm = fig_width_mm - ml_mm - mr_mm
    content_height_mm = fig_height_mm - mb_mm - mt_mm

    # wspace/hspace are fractions of axes width/height
    # total_width = ncols * aw + (ncols-1) * sw = ncols * aw + (ncols-1) * wspace * aw
    # total_width = aw * (ncols + (ncols-1) * wspace)
    if ncols > 1:
        aw = (
            content_width_mm / (ncols + (ncols - 1) * wspace)
            if ncols > 0
            else content_width_mm
        )
    else:
        aw = content_width_mm

    if nrows > 1:
        ah = (
            content_height_mm / (nrows + (nrows - 1) * hspace)
            if nrows > 0
            else content_height_mm
        )
    else:
        ah = content_height_mm

    return aw, ah


__all__ = ["apply_figure_layout_overrides"]
