#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Panel visibility management for composition feature."""

from typing import Tuple

from .._utils._grid import grid_id
from .._wrappers import RecordingFigure


def hide_panel(fig: RecordingFigure, position: Tuple[int, int]) -> None:
    """Hide a panel (visually drop it without deleting data).

    The panel data is preserved in the recipe but not rendered.
    Use show_panel() to restore visibility.

    Parameters
    ----------
    fig : RecordingFigure
        The figure containing the panel.
    position : tuple
        (row, col) position of the panel to hide.

    Examples
    --------
    >>> import figrecipe as fr
    >>> fig, axes = fr.subplots(1, 2)
    >>> axes[0].plot([1, 2], [1, 2])
    >>> fr.hide_panel(fig, (0, 1))  # Hide empty second panel
    """
    ax_key = grid_id(position[0], position[1])
    if ax_key in fig.record.axes:
        fig.record.axes[ax_key].visible = False
        _set_axes_visible(fig, position, False)


def show_panel(fig: RecordingFigure, position: Tuple[int, int]) -> None:
    """Show a previously hidden panel.

    Parameters
    ----------
    fig : RecordingFigure
        The figure containing the panel.
    position : tuple
        (row, col) position of the panel to show.

    Examples
    --------
    >>> import figrecipe as fr
    >>> fig, axes = fr.subplots(1, 2)
    >>> fr.hide_panel(fig, (0, 1))
    >>> fr.show_panel(fig, (0, 1))  # Restore visibility
    """
    ax_key = grid_id(position[0], position[1])
    if ax_key in fig.record.axes:
        fig.record.axes[ax_key].visible = True
        _set_axes_visible(fig, position, True)


def toggle_panel(fig: RecordingFigure, position: Tuple[int, int]) -> bool:
    """Toggle panel visibility.

    Parameters
    ----------
    fig : RecordingFigure
        The figure containing the panel.
    position : tuple
        (row, col) position of the panel.

    Returns
    -------
    bool
        New visibility state (True = visible, False = hidden).

    Examples
    --------
    >>> import figrecipe as fr
    >>> fig, ax = fr.subplots()
    >>> fr.toggle_panel(fig, (0, 0))  # Returns False (now hidden)
    >>> fr.toggle_panel(fig, (0, 0))  # Returns True (now visible)
    """
    ax_key = grid_id(position[0], position[1])
    if ax_key in fig.record.axes:
        current = fig.record.axes[ax_key].visible
        if current:
            hide_panel(fig, position)
        else:
            show_panel(fig, position)
        return not current
    return False


def _set_axes_visible(
    fig: RecordingFigure,
    position: Tuple[int, int],
    visible: bool,
) -> None:
    """Set matplotlib axes visibility.

    Parameters
    ----------
    fig : RecordingFigure
        The figure.
    position : tuple
        (row, col) position.
    visible : bool
        Whether to make visible or hidden.
    """
    row, col = position
    try:
        axes = fig._axes
        if isinstance(axes, list):
            if isinstance(axes[0], list):
                ax = axes[row][col]
            else:
                ax = axes[max(row, col)]
        else:
            ax = axes[row, col]

        mpl_ax = ax._ax if hasattr(ax, "_ax") else ax
        mpl_ax.set_visible(visible)
    except (IndexError, AttributeError, KeyError):
        pass


__all__ = ["hide_panel", "show_panel", "toggle_panel"]
