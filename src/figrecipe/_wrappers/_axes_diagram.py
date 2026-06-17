#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagram visualization mixin for RecordingAxes."""

from typing import TYPE_CHECKING, Optional, Tuple

from matplotlib.figure import Figure

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from .._recorder import Recorder


class DiagramMixin:
    """Mixin providing diagram method for RecordingAxes."""

    # These will be set by the main class
    _ax: "Axes"
    _recorder: "Recorder"
    _position: tuple
    _track: bool

    def diagram(
        self,
        diagram,
        *,
        id: Optional[str] = None,
        track: bool = True,
        auto_fix: bool = False,
    ):
        """Draw a box-and-arrow diagram with native matplotlib rendering.

        Parameters
        ----------
        diagram : Diagram or dict
            The diagram to render. Can be:
            - Diagram instance (or legacy Diagram)
            - Dictionary with diagram specification
        id : str, optional
            Custom ID for this call.
        track : bool
            Whether to record this call for reproducibility.
        auto_fix : bool
            Auto-resolve layout violations before rendering.

        Returns
        -------
        tuple
            (figure, axes) after rendering.
        """
        return diagram_plot(
            self._ax,
            diagram,
            self._recorder,
            self._position,
            self._track and track,
            id,
            auto_fix=auto_fix,
        )


def diagram_plot(
    ax: "Axes",
    diagram,
    recorder: "Recorder",
    position: Tuple[int, int],
    track: bool,
    call_id: Optional[str],
    *,
    auto_fix: bool = False,
) -> Tuple[Figure, "Axes"]:
    """Draw a FigRecipe Diagram with native matplotlib rendering.

    Parameters
    ----------
    ax : Axes
        The matplotlib axes to draw on.
    diagram : Diagram or dict
        The diagram to render. Can be:
        - Diagram instance
        - Dictionary with diagram specification
    recorder : Recorder
        The recorder instance for tracking calls.
    position : tuple
        (row, col) position in the figure grid.
    track : bool
        Whether to record this call.
    call_id : str, optional
        Custom ID for this call.

    Returns
    -------
    tuple
        (figure, axes) after rendering.
    """

    from .._diagram._diagram._core import Diagram

    # Convert dict to Diagram if needed
    if isinstance(diagram, dict):
        info = Diagram.from_dict(diagram)
    elif isinstance(diagram, Diagram):
        info = diagram
    else:
        raise TypeError(f"diagram must be Diagram or dict, got {type(diagram)}")

    # Resolve auto-height before sizing the figure
    info._finalize_canvas_size()

    # Resize figure to match diagram's coordinate space BEFORE rendering
    fig = ax.figure
    x_range = info.xlim[1] - info.xlim[0]
    y_range = info.ylim[1] - info.ylim[0]
    fig.set_size_inches(x_range / 25.4, y_range / 25.4)

    # Render to the provided axes
    fig, rendered_ax = info.render(ax=ax, auto_fix=auto_fix)

    # For a standalone diagram (figure sized to the diagram), pin the axes to
    # fill the figure. The default subplot margins differ between the save figure
    # and the figure rebuilt by the reproducer, so with aspect="equal" the
    # diagram letterboxed at a different vertical offset -> different cropped
    # height (NeuroVista Fig 02 panel b). A fixed position makes save and
    # reproduce identical; _reproducer/_replay_diagram applies the same pin.
    if len(fig.get_axes()) == 1:
        rendered_ax.set_position((0.0, 0.0, 1.0, 1.0))

    # Post-render validations (skipped inside render() when ax is provided)
    # Errors are stored on the figure so fr.save() can save _FAILED figures
    from .._diagram._diagram import _validate as _sv

    try:
        _sv.validate_all(info, fig=fig, ax=rendered_ax)
    except ValueError as e:
        if not hasattr(fig, "_diagram_validation_errors"):
            fig._diagram_validation_errors = []
        fig._diagram_validation_errors.append(str(e))

    # Record for reproducibility. Capture the figure's ACTUAL size now -- this is
    # what savefig will use. render() can widen info.xlim to fit text content, but
    # the figure was already sized from the pre-widen extent and is not resized
    # again, so deriving the reproduce figsize from the recorded (post-widen) xlim
    # produced a larger figure than the original save -> figure-SIZE mismatch at
    # validate time (NeuroVista Fig 02 panel b). Recording the true figsize lets
    # the reproducer restore the exact saved size.
    if track:
        _fw, _fh = fig.get_size_inches()
        figsize_in = (float(_fw), float(_fh))
        _record_diagram_call(
            recorder,
            position,
            call_id,
            info,
            figsize_in,
        )

    return fig, rendered_ax


def _record_diagram_call(
    recorder: "Recorder",
    position: Tuple[int, int],
    call_id: Optional[str],
    info,
    figsize_in: Optional[Tuple[float, float]] = None,
) -> None:
    """Record diagram call for reproducibility."""
    from .._recorder import CallRecord

    final_id = call_id if call_id else recorder._generate_call_id("diagram")

    # Serialize diagram data for recipe
    diagram_data = info.to_dict()

    kwargs = {"diagram_data": diagram_data}
    if figsize_in is not None:
        kwargs["figsize_in"] = list(figsize_in)
    record = CallRecord(
        id=final_id,
        function="diagram",
        args=[],
        kwargs=kwargs,
        ax_position=position,
    )
    ax_record = recorder.figure_record.get_or_create_axes(*position)
    ax_record.add_call(record)


__all__ = ["DiagramMixin", "diagram_plot"]
