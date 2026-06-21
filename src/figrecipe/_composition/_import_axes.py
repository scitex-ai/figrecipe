#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Import axes from external recipes into existing figures."""

from pathlib import Path
from typing import Tuple, Union

from .._recorder import FigureRecord
from .._serializer import load_recipe
from .._utils._grid import grid_id, parse_grid_id
from .._wrappers import RecordingAxes, RecordingFigure
from ._compose import _replay_axes_record


def import_axes(
    fig: RecordingFigure,
    target_position: Tuple[int, int],
    source: Union[str, Path, FigureRecord],
    source_axes: str = grid_id(0, 0),
) -> RecordingAxes:
    """Import axes from another recipe into an existing figure.

    This function copies all plotting calls and decorations from a source
    axes (in a recipe file or FigureRecord) to a target position in an
    existing figure. The target axes is cleared before import.

    Parameters
    ----------
    fig : RecordingFigure
        Target figure to import into.
    target_position : tuple
        (row, col) position in target figure.
    source : str, Path, or FigureRecord
        Source recipe file path or FigureRecord object.
    source_axes : str, optional
        Key of axes to import from source (default: "r0c0"). Legacy
        "ax_0_0" keys are also accepted.

    Returns
    -------
    RecordingAxes
        The target axes after import.

    Raises
    ------
    ValueError
        If source_axes key not found in source.
    TypeError
        If source is not a valid type.

    Examples
    --------
    >>> import figrecipe as fr
    >>> fig, axes = fr.subplots(1, 2)
    >>> axes[0].plot([1, 2, 3], [1, 4, 9])
    >>> fr.import_axes(fig, (0, 1), "analysis.yaml")
    """
    # Load source if path
    if isinstance(source, (str, Path)):
        source_record = load_recipe(source)
    elif isinstance(source, FigureRecord):
        source_record = source
    else:
        raise TypeError(f"Invalid source type: {type(source)}")

    # Get source axes record (accept "rRcC" or legacy "ax_R_C" key forms)
    ax_record = source_record.axes.get(source_axes)
    if ax_record is None:
        parsed = parse_grid_id(source_axes)
        if parsed is not None:
            for cand in (grid_id(*parsed), f"ax_{parsed[0]}_{parsed[1]}"):
                ax_record = source_record.axes.get(cand)
                if ax_record is not None:
                    break
    if ax_record is None:
        available = list(source_record.axes.keys())
        raise ValueError(
            f"Axes '{source_axes}' not found in source. Available: {available}"
        )

    # Get target axes
    row, col = target_position
    target_ax = _get_target_axes(fig, row, col)

    # Clear existing content
    mpl_ax = target_ax._ax if hasattr(target_ax, "_ax") else target_ax
    mpl_ax.clear()

    # Replay source calls onto target
    _replay_axes_record(target_ax, ax_record, fig.record, row, col)

    return target_ax


def _get_target_axes(
    fig: RecordingFigure,
    row: int,
    col: int,
) -> RecordingAxes:
    """Get target axes from figure at position.

    Parameters
    ----------
    fig : RecordingFigure
        The figure.
    row, col : int
        Target position.

    Returns
    -------
    RecordingAxes
        Axes at position.

    Raises
    ------
    IndexError
        If position is out of range.
    """
    if not hasattr(fig, "_axes"):
        raise ValueError("Figure must have _axes attribute")

    axes = fig._axes
    try:
        # Handle different axes array structures
        if isinstance(axes, list):
            if isinstance(axes[0], list):
                return axes[row][col]
            else:
                return axes[max(row, col)]
        else:
            return axes[row, col]
    except (IndexError, KeyError) as e:
        raise IndexError(f"Position ({row}, {col}) out of range for figure axes") from e


__all__ = ["import_axes"]
