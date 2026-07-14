#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Spine visibility utilities for matplotlib axes."""

__all__ = [
    "hide_spines",
    "show_spines",
    "show_all_spines",
    "show_classic_spines",
    "toggle_spines",
]

from typing import Any, Optional

from ._base import get_axis_from_wrapper, validate_axis


def hide_spines(
    ax: Any,
    top: bool = True,
    bottom: bool = False,
    left: bool = False,
    right: bool = True,
    ticks: bool = False,
    labels: bool = False,
) -> Any:
    """Hide specified spines of a matplotlib Axes object.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axis for which spines will be hidden.
    top : bool
        If True, hides the top spine. Default: True.
    bottom : bool
        If True, hides the bottom spine. Default: False.
    left : bool
        If True, hides the left spine. Default: False.
    right : bool
        If True, hides the right spine. Default: True.
    ticks : bool
        If True, removes ticks from hidden spines. Default: False.
    labels : bool
        If True, removes labels from hidden spines. Default: False.

    Returns
    -------
    Axes
        The modified axis with specified spines hidden.

    Examples
    --------
    >>> import figrecipe as fr
    >>> fig, ax = fr.subplots()
    >>> ax.plot([1, 2, 3], [1, 2, 3])
    >>> fr.hide_spines(ax)  # Hides top and right spines (default)
    """
    validate_axis(ax)
    ax = get_axis_from_wrapper(ax)

    targets = []
    if top:
        targets.append("top")
    if bottom:
        targets.append("bottom")
    if left:
        targets.append("left")
    if right:
        targets.append("right")

    for target in targets:
        ax.spines[target].set_visible(False)

        if ticks:
            if target == "bottom":
                ax.xaxis.set_ticks_position("none")
            elif target == "left":
                ax.yaxis.set_ticks_position("none")

        if labels:
            # tick_params toggles label VISIBILITY; set_xticklabels([]) would
            # pin a NullFormatter on the axis instead, so a caller who later
            # set ticks would draw blanks and could never get them back.
            # show_spines() below restores these with labelbottom=True.
            if target == "bottom":
                ax.tick_params(labelbottom=False)
            elif target == "left":
                ax.tick_params(labelleft=False)

    return ax


def show_spines(
    ax: Any,
    top: bool = True,
    bottom: bool = True,
    left: bool = True,
    right: bool = True,
    ticks: bool = True,
    labels: bool = True,
    restore_defaults: bool = True,
    spine_width: Optional[float] = None,
    spine_color: Optional[str] = None,
) -> Any:
    """Show specified spines of a matplotlib Axes object.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The Axes object for which spines will be shown.
    top : bool
        If True, shows the top spine. Default: True.
    bottom : bool
        If True, shows the bottom spine. Default: True.
    left : bool
        If True, shows the left spine. Default: True.
    right : bool
        If True, shows the right spine. Default: True.
    ticks : bool
        If True, restores ticks on shown spines. Default: True.
    labels : bool
        If True, restores labels on shown spines. Default: True.
    restore_defaults : bool
        If True, restores default tick positions. Default: True.
    spine_width : float, optional
        Width of the spines to show.
    spine_color : str, optional
        Color of the spines to show.

    Returns
    -------
    Axes
        The modified Axes object.

    Examples
    --------
    >>> import figrecipe as fr
    >>> fig, ax = fr.subplots()
    >>> fr.show_spines(ax, top=False, right=False)  # Classic scientific style
    """
    validate_axis(ax)
    ax = get_axis_from_wrapper(ax)

    spine_settings = {"top": top, "bottom": bottom, "left": left, "right": right}

    for spine_name, should_show in spine_settings.items():
        ax.spines[spine_name].set_visible(should_show)

        if should_show:
            if spine_width is not None:
                ax.spines[spine_name].set_linewidth(spine_width)
            if spine_color is not None:
                ax.spines[spine_name].set_color(spine_color)

    # Restore ticks if requested
    if ticks and restore_defaults:
        if bottom and not top:
            ax.xaxis.set_ticks_position("bottom")
        elif top and not bottom:
            ax.xaxis.set_ticks_position("top")
        elif bottom and top:
            ax.xaxis.set_ticks_position("both")

        if left and not right:
            ax.yaxis.set_ticks_position("left")
        elif right and not left:
            ax.yaxis.set_ticks_position("right")
        elif left and right:
            ax.yaxis.set_ticks_position("both")

    # Restore labels if requested. Re-setting the tick LOCATIONS is not enough
    # to bring labels back: hide_spines turns label visibility OFF, and only
    # turning it back ON shows them again. (It used to blank labels with
    # set_xticklabels([]), which pinned a NullFormatter that no amount of
    # set_xticks could undo -- so this restore path never actually worked.)
    if labels and restore_defaults:
        if bottom or top:
            ax.tick_params(labelbottom=bottom, labeltop=top)
        if left or right:
            ax.tick_params(labelleft=left, labelright=right)

    return ax


def show_all_spines(
    ax: Any,
    spine_width: Optional[float] = None,
    spine_color: Optional[str] = None,
    ticks: bool = True,
    labels: bool = True,
) -> Any:
    """Show all four spines (box style).

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The Axes object to modify.
    spine_width : float, optional
        Width of all spines.
    spine_color : str, optional
        Color of all spines.
    ticks : bool
        Whether to show ticks. Default: True.
    labels : bool
        Whether to show labels. Default: True.

    Returns
    -------
    Axes
        The modified Axes object.
    """
    return show_spines(
        ax,
        top=True,
        bottom=True,
        left=True,
        right=True,
        ticks=ticks,
        labels=labels,
        spine_width=spine_width,
        spine_color=spine_color,
    )


def show_classic_spines(
    ax: Any,
    spine_width: Optional[float] = None,
    spine_color: Optional[str] = None,
    ticks: bool = True,
    labels: bool = True,
) -> Any:
    """Show only bottom and left spines (classic scientific plot style).

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The Axes object to modify.
    spine_width : float, optional
        Width of the spines.
    spine_color : str, optional
        Color of the spines.
    ticks : bool
        Whether to show ticks. Default: True.
    labels : bool
        Whether to show labels. Default: True.

    Returns
    -------
    Axes
        The modified Axes object.
    """
    return show_spines(
        ax,
        top=False,
        bottom=True,
        left=True,
        right=False,
        ticks=ticks,
        labels=labels,
        spine_width=spine_width,
        spine_color=spine_color,
    )


def toggle_spines(
    ax: Any,
    top: Optional[bool] = None,
    bottom: Optional[bool] = None,
    left: Optional[bool] = None,
    right: Optional[bool] = None,
) -> Any:
    """Toggle the visibility of spines.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The Axes object to modify.
    top : bool, optional
        If specified, sets top spine visibility. If None, toggles.
    bottom : bool, optional
        If specified, sets bottom spine visibility. If None, toggles.
    left : bool, optional
        If specified, sets left spine visibility. If None, toggles.
    right : bool, optional
        If specified, sets right spine visibility. If None, toggles.

    Returns
    -------
    Axes
        The modified Axes object.
    """
    validate_axis(ax)
    ax = get_axis_from_wrapper(ax)

    spine_names = ["top", "bottom", "left", "right"]
    spine_params = [top, bottom, left, right]

    for spine_name, param in zip(spine_names, spine_params):
        if param is None:
            current_state = ax.spines[spine_name].get_visible()
            ax.spines[spine_name].set_visible(not current_state)
        else:
            ax.spines[spine_name].set_visible(param)

    return ax


# EOF
