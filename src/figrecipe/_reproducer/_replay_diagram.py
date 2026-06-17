#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagram replay functionality for recipe reproduction.

Handles reconstructing diagrams from serialized recipe data
and redrawing them using the stored positions and styling.
"""

from typing import Any

from matplotlib.axes import Axes

from .._recorder import CallRecord


def replay_diagram_call(ax: Axes, call: CallRecord) -> Any:
    """Replay a diagram call from a recipe.

    Parameters
    ----------
    ax : Axes
        The matplotlib axes to draw on.
    call : CallRecord
        The diagram call record containing serialized diagram data.

    Returns
    -------
    dict
        Result containing renderer and positions.
    """
    from .._diagram._shared._native_render import DiagramRenderer

    kwargs = call.kwargs.copy()
    diagram_data = kwargs.pop("diagram_data", None)

    if diagram_data is None:
        import warnings

        warnings.warn("Diagram call missing diagram_data")
        return None

    # Reconstruct renderer from serialized data
    renderer = DiagramRenderer.from_dict(diagram_data)

    # Render to axes
    renderer._render_edges(ax)
    renderer._render_nodes(ax)

    # Configure axes
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")

    # Add title if specified
    if renderer.spec.title:
        from .._diagram._shared._styles_native import FONT_CONFIG

        ax.set_title(
            renderer.spec.title,
            fontsize=FONT_CONFIG["title_size"],
            fontweight="bold",
        )

    return {
        "renderer": renderer,
        "positions": renderer._positions,
    }


def replay_diagram_native_call(ax: Axes, call: CallRecord) -> Any:
    """Replay a diagram call from a recipe (Diagram class renderer).

    Handles both current ``diagram_data`` and legacy ``schematic_data`` keys.

    Parameters
    ----------
    ax : Axes
        The matplotlib axes to draw on.
    call : CallRecord
        The diagram call record containing serialized data.

    Returns
    -------
    tuple
        (figure, axes) after rendering.
    """
    from .._diagram._diagram._core import Diagram

    kwargs = call.kwargs.copy()
    diagram_data = kwargs.pop("diagram_data", None) or kwargs.pop(
        "schematic_data", None
    )
    figsize_in = kwargs.pop("figsize_in", None)

    if diagram_data is None:
        import warnings

        warnings.warn("Diagram call missing diagram_data")
        return None

    # Reconstruct diagram from serialized data
    info = Diagram.from_dict(diagram_data)

    single_axis = len(ax.figure.get_axes()) <= 1

    # Restore the EXACT figure size used at save time, BEFORE rendering. render()
    # lays out text/boxes against the current figure size and can widen info.xlim
    # to fit; at save the figure was sized before that, so rendering reproduce at
    # a different incoming size diverged in both width and the cropped height
    # (NeuroVista Fig 02 panel b SIZE mismatch). The recorder now stores the true
    # figsize; pin it first so save and reproduce render identically.
    if single_axis and figsize_in is not None:
        ax.figure.set_size_inches(float(figsize_in[0]), float(figsize_in[1]))

    # Render to provided axes
    fig, rendered_ax = info.render(ax=ax)

    # In composed figures (multiple axes), don't resize the figure
    # and use auto aspect so the diagram fills its grid cell properly.
    # Also set white background so diagram is visible on transparent renders.
    if len(fig.get_axes()) > 1:
        ax.set_aspect("auto")
        ax.set_facecolor("white")
    elif figsize_in is not None:
        # render() may have re-touched the figure size; re-pin to the saved size.
        fig.set_size_inches(float(figsize_in[0]), float(figsize_in[1]))
    else:
        x_range = info.xlim[1] - info.xlim[0]
        y_range = info.ylim[1] - info.ylim[0]
        fig.set_size_inches(x_range / 25.4, y_range / 25.4)

    # Standalone diagram: pin the axes to fill the figure, matching the recorder
    # (_wrappers/_axes_diagram). Default subplot margins differ between the save
    # figure and this rebuilt one, so with aspect="equal" the diagram would
    # letterbox at a different vertical offset -> different cropped height.
    if single_axis:
        rendered_ax.set_position((0.0, 0.0, 1.0, 1.0))

    return fig, rendered_ax


__all__ = ["replay_diagram_call", "replay_diagram_native_call"]
