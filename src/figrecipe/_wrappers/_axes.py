#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wrapped Axes that records all plotting calls."""

from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

import numpy as np
from matplotlib.axes import Axes

from ._axes_diagram import DiagramMixin
from ._axes_methods import RecordingAxesMethods
from ._axes_scatter_labels import ScatterLabelsMixin
from ._axes_scitex import SciTexMixin
from ._axes_style_mixin import AxesStyleMixin

if TYPE_CHECKING:
    from .._recorder import Recorder


class RecordingAxes(
    RecordingAxesMethods,
    AxesStyleMixin,
    SciTexMixin,
    DiagramMixin,
    ScatterLabelsMixin,
):
    """Wrapper around matplotlib Axes that records all calls.

    This wrapper intercepts calls to plotting methods and records them
    for later reproduction.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The underlying matplotlib axes.
    recorder : Recorder
        The recorder instance to log calls to.
    position : tuple
        (row, col) position in the figure grid.

    Examples
    --------
    >>> import figrecipe as ps
    >>> fig, ax = ps.subplots()
    >>> ax.plot([1, 2, 3], [4, 5, 6], color='red', id='my_line')
    >>> # The call is recorded automatically
    """

    # Internal: Methods whose results can be referenced by other methods
    _RESULT_REFERENCEABLE_METHODS = {"contour", "contourf"}
    # Internal: Methods that take results from other methods as arguments
    _RESULT_REFERENCING_METHODS = {"clabel"}

    def __init__(
        self,
        ax: Axes,
        recorder: "Recorder",
        position: Tuple[int, int] = (0, 0),
    ):
        self._ax = ax
        self._recorder = recorder
        self._position = position
        self._track = True
        # Map matplotlib result objects (by id) to their source call_id
        self._result_refs: Dict[int, str] = {}

    @property
    def ax(self) -> Axes:
        """Get the underlying matplotlib axes."""
        return self._ax

    @property
    def position(self) -> Tuple[int, int]:
        """Get axes position in grid."""
        return self._position

    def __getattr__(self, name: str) -> Any:
        """Intercept attribute access to wrap methods."""
        attr = getattr(self._ax, name)

        # Use custom wrappers for methods with special styling
        if callable(attr) and name == "bar":
            return self._create_bar_wrapper()

        # Route boxplot to wrapper that sets patch_artist=True
        if callable(attr) and name == "boxplot":
            return self._create_boxplot_wrapper()

        # Route legend to wrapper that applies frame styling
        if callable(attr) and name == "legend":
            return self._create_legend_wrapper()

        # Route stem to wrapper that handles color kwarg
        if callable(attr) and name == "stem":
            return self._create_stem_wrapper()

        # Route add_patch to a wrapper that records a serializable patch spec
        # (raw patches are objects that otherwise vanish on replay)
        if callable(attr) and name == "add_patch":
            from ._axes_patches import build_add_patch_wrapper

            return build_add_patch_wrapper(self)

        # Route inset_axes to a wrapper that records its content as a managed
        # sub-panel (raw inset axes are otherwise unrecorded and vanish on replay)
        if callable(attr) and name == "inset_axes":
            from ._axes_insets import build_inset_axes_wrapper

            return build_inset_axes_wrapper(self)

        # Route bar_label to a wrapper that freezes each label into a recorded
        # annotate (its live BarContainer arg is otherwise un-serializable).
        if callable(attr) and name == "bar_label":
            from ._axes_barlabel import build_bar_label_wrapper

            return build_bar_label_wrapper(self)

        # Route secondary_xaxis/secondary_yaxis to a wrapper that records the
        # plain-location case and warns when custom transform functions are given.
        if callable(attr) and name in ("secondary_xaxis", "secondary_yaxis"):
            from ._axes_barlabel import build_secondary_axis_wrapper

            return build_secondary_axis_wrapper(self, name)

        # If it's a plotting or decoration method, wrap it
        if callable(attr) and name in (
            self._recorder.PLOTTING_METHODS | self._recorder.DECORATION_METHODS
        ):
            return self._create_recording_wrapper(name, attr)

        # For other methods/attributes, return as-is
        return attr

    def embed(self, source, bounds=None, *, ax_key=None, track=True, id=None):
        """Embed a recipe or diagram as a managed sub-panel that round-trips.

        ``source`` may be a recipe path, image, FigureRecord, diagram recipe,
        composed multi-panel recipe, or ``(source, ax_key)``. ``bounds`` is an
        axes-fraction ``[x, y, w, h]`` (defaults to the whole axes). Returns the
        embedded inset RecordingAxes (or a list for a multi-panel source).
        """
        from ._axes_embed import embed_source

        return embed_source(self, source, bounds, ax_key=ax_key, track=track, id=id)

    def __dir__(self):
        """Return list of attributes for tab completion.

        Exposes all matplotlib plotting and decoration methods alongside
        figrecipe's custom methods and properties.
        """
        # Get base attributes (excluding private)
        base_attrs = [a for a in super().__dir__() if not a.startswith("_")]

        # Add all matplotlib plotting methods
        from .._params import DECORATION_METHODS, PLOTTING_METHODS

        matplotlib_methods = sorted(PLOTTING_METHODS | DECORATION_METHODS)

        # Combine and deduplicate
        return sorted(set(base_attrs + matplotlib_methods))

    def _create_recording_wrapper(self, method_name: str, method: callable):
        """Create a wrapper function that records the call."""
        from ._axes_helpers import (
            inject_clip_on_from_style,
            inject_method_defaults,
            record_call_with_color_capture,
        )

        def wrapper(
            *args,
            id: Optional[str] = None,
            track: bool = True,
            stats: Optional[Dict[str, Any]] = None,
            **kwargs,
        ):
            from ..styles._internal import resolve_colors_in_kwargs

            kwargs = resolve_colors_in_kwargs(kwargs)
            kwargs = inject_clip_on_from_style(kwargs, method_name)
            kwargs = inject_method_defaults(kwargs, method_name)

            result = method(*args, **kwargs)
            if self._track and track:
                record_kwargs = kwargs.copy()
                if stats is not None:
                    record_kwargs["stats"] = stats
                record_args = args
                if method_name in ("set_xticks", "set_yticks") and args:
                    # Read the tick POSITIONS back from the live axis after
                    # the call instead of recording the caller's raw arg.
                    # matplotlib happily accepts a range/tuple/generator for
                    # ``ticks``, none of which the generic arg serializer
                    # round-trips (a bare ``range(19)`` degrades to the
                    # literal string ``"range(0, 19)"`` and later fails to
                    # replay) — the live axis always holds a well-formed
                    # numeric array, so recording that is both simpler and
                    # self-consistent with whatever a later
                    # set_xticklabels() on this axis will see.
                    axis_letter = "x" if method_name == "set_xticks" else "y"
                    live_ticks = list(getattr(self._ax, f"get_{axis_letter}ticks")())
                    record_args = (live_ticks,) + tuple(args[1:])
                record_call_with_color_capture(
                    self._recorder,
                    self._position,
                    method_name,
                    record_args,
                    record_kwargs,
                    result,
                    id,
                    self._result_refs,
                    self._RESULT_REFERENCING_METHODS,
                    self._RESULT_REFERENCEABLE_METHODS,
                )
            return result

        return wrapper

    def _create_bar_wrapper(self):
        """Create wrapper for bar() with SCITEX error bar styling."""
        from ._axes_plots import bar_plot

        def wrapper(
            *args,
            id: Optional[str] = None,
            track: bool = True,
            stats: Optional[Dict[str, Any]] = None,
            **kwargs,
        ):
            if stats is not None:
                kwargs["stats"] = stats

            return bar_plot(
                self._ax,
                args,
                kwargs,
                self._recorder,
                self._position,
                track=self._track and track,
                call_id=id,
            )

        return wrapper

    def _create_boxplot_wrapper(self):
        """Create wrapper for boxplot() with patch_artist=True default."""
        from ._boxplot import boxplot_plot

        def wrapper(
            *args,
            id: Optional[str] = None,
            track: bool = True,
            **kwargs,
        ):
            # Handle positional x argument
            x = args[0] if args else kwargs.pop("x", None)
            if x is None:
                raise ValueError("boxplot requires data argument")

            return boxplot_plot(
                self._ax,
                x,
                self._recorder,
                self._position,
                track=self._track and track,
                call_id=id,
                **kwargs,
            )

        return wrapper

    def _create_stem_wrapper(self):
        """Create wrapper for stem() that accepts color kwarg."""
        original_stem = self._ax.stem

        def wrapper(
            *args,
            id: Optional[str] = None,
            track: bool = True,
            color=None,
            **kwargs,
        ):
            # Call original stem
            container = original_stem(*args, **kwargs)

            # Apply color if provided (stem doesn't accept color kwarg natively)
            if color is not None:
                import matplotlib.colors as mcolors

                color_val = mcolors.to_rgba(color)
                container.markerline.set_color(color_val)
                container.stemlines.set_color(color_val)
                container.baseline.set_color(color_val)

            # Record the call with color
            if self._track and track:
                record_kwargs = kwargs.copy()
                # Capture the actual color (either provided or from cycle)
                if color is not None:
                    import matplotlib.colors as mcolors

                    record_kwargs["color"] = mcolors.to_hex(color)
                else:
                    # Capture from result
                    try:
                        import matplotlib.colors as mcolors

                        c = container.markerline.get_color()
                        record_kwargs["color"] = mcolors.to_hex(c)
                    except Exception:
                        pass

                self._recorder.record_call(
                    ax_position=self._position,
                    method_name="stem",
                    args=args,
                    kwargs=record_kwargs,
                    call_id=id,
                )

            return container

        return wrapper

    def _create_legend_wrapper(self):
        """Build the legend() wrapper that handles SCITEX styling +
        figrecipe loc extensions + recording. Implementation lives
        in `_legend_wrapper.py` so this file stays focused.
        """
        from ._legend_wrapper import build_legend_wrapper

        return build_legend_wrapper(self)

    def set_caption(self, caption: str) -> "RecordingAxes":
        """Set panel caption metadata (not rendered, stored in recipe)."""
        ax_record = self._recorder.figure_record.get_or_create_axes(*self._position)
        ax_record.caption = caption
        return self

    @property
    def panel_caption(self) -> Optional[str]:
        """Get the panel caption metadata."""
        ax_record = self._recorder.figure_record.get_or_create_axes(*self._position)
        return ax_record.caption

    def set_stats(self, stats: Dict[str, Any]) -> "RecordingAxes":
        """Set panel-level statistics metadata (not rendered, stored in recipe)."""
        ax_record = self._recorder.figure_record.get_or_create_axes(*self._position)
        ax_record.stats = stats
        return self

    @property
    def stats(self) -> Optional[Dict[str, Any]]:
        """Get the panel-level statistics metadata."""
        ax_record = self._recorder.figure_record.get_or_create_axes(*self._position)
        return ax_record.stats

    def _no_record(self):
        """Context manager to temporarily disable recording (internal)."""
        return _NoRecordContext(self)

    def _record_seaborn_call(
        self,
        func_name: str,
        args: tuple,
        kwargs: Dict[str, Any],
        data_arrays: Dict[str, np.ndarray],
        call_id: Optional[str] = None,
    ) -> None:
        """Record a seaborn plotting call."""
        if not self._track:
            return

        from ._axes_seaborn import record_seaborn_call

        record_seaborn_call(
            self._recorder,
            self._position,
            func_name,
            args,
            kwargs,
            data_arrays,
            call_id,
        )

    # Expose common properties directly
    @property
    def figure(self):
        return self._ax.figure

    @property
    def xaxis(self):
        return self._ax.xaxis

    @property
    def yaxis(self):
        return self._ax.yaxis

    # Methods that should not be recorded
    def get_xlim(self):
        return self._ax.get_xlim()

    def get_ylim(self):
        return self._ax.get_ylim()

    def get_xlabel(self):
        return self._ax.get_xlabel()

    def get_ylabel(self):
        return self._ax.get_ylabel()

    def get_title(self):
        return self._ax.get_title()

    @property
    def caption(self) -> Optional[str]:
        """Get the panel caption metadata."""
        ax_record = self._recorder.figure_record.get_or_create_axes(*self._position)
        return ax_record.caption

    def generate_panel_caption(
        self, label: Optional[str] = None, style: str = "publication"
    ) -> str:
        """Generate a caption for this panel from stats metadata."""
        from ._caption_generator import generate_panel_caption

        return generate_panel_caption(label=label, stats=self.stats, style=style)


class _NoRecordContext:
    """Context manager to temporarily disable recording."""

    def __init__(self, axes: RecordingAxes):
        self._axes = axes
        self._original_track = axes._track

    def __enter__(self):
        self._axes._track = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._axes._track = self._original_track
        return False
