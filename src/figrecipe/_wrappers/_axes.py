#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wrapped Axes that records all plotting calls."""

from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

import numpy as np
from matplotlib.axes import Axes

from ._axes_diagram import DiagramMixin
from ._axes_methods import RecordingAxesMethods
from ._axes_scitex import SciTexMixin
from ._axes_style_mixin import AxesStyleMixin

if TYPE_CHECKING:
    from .._recorder import Recorder


class RecordingAxes(RecordingAxesMethods, AxesStyleMixin, SciTexMixin, DiagramMixin):
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

        # If it's a plotting or decoration method, wrap it
        if callable(attr) and name in (
            self._recorder.PLOTTING_METHODS | self._recorder.DECORATION_METHODS
        ):
            return self._create_recording_wrapper(name, attr)

        # For other methods/attributes, return as-is
        return attr

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
                record_call_with_color_capture(
                    self._recorder,
                    self._position,
                    method_name,
                    args,
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
        """Create wrapper for legend() that applies frame styling and records the call."""
        from ..styles import load_style

        original_legend = self._ax.legend

        def wrapper(
            *args,
            id: Optional[str] = None,
            track: bool = True,
            **kwargs,
        ):
            # Catch the common anti-pattern `ax.legend('upper right')`
            # — matplotlib interprets a single positional string as
            # the handles arg and iterates it into per-character labels.
            # If the only positional looks like a known loc string,
            # route it to the `loc=` kwarg.
            _KNOWN_MPL_LOCS = {
                'best', 'upper right', 'upper left', 'lower right',
                'lower left', 'right', 'center left', 'center right',
                'lower center', 'upper center', 'center',
            }
            if (
                len(args) == 1
                and isinstance(args[0], str)
                and 'loc' not in kwargs
            ):
                _norm0 = ' '.join(args[0].lower().split())
                # Will be filled below; just check the prefix here.
                if _norm0 in _KNOWN_MPL_LOCS or _norm0.startswith('outer') or _norm0 == 'separate':
                    kwargs['loc'] = args[0]
                    args = ()

            # Resolve figrecipe-extended `loc` strings BEFORE matplotlib
            # sees them. Twelve canonical outer placements cover every
            # corner / edge of the axes. The user passes any "outer …"
            # string and we translate it to a (loc, bbox_to_anchor) pair
            # so they don't have to remember the bbox_to_anchor
            # incantation.
            #
            # Cardinal (4):
            #   outer right / left / top / bottom    — anchored to mid-edge
            # Corners (4 × 2 alias forms each):
            #   outer upper right, outer right upper — top-right corner
            #   outer upper left,  outer left upper  — top-left corner
            #   outer lower right, outer right lower — bottom-right corner
            #   outer lower left,  outer left lower  — bottom-bottom corner
            # Edge centers (2):
            #   outer upper center / outer lower center
            #
            # When neither `loc` nor `bbox_to_anchor` is specified, default
            # to 'outer right' — inside-axes legends frequently occlude
            # the data they describe.
            _OUTER_VARIANTS = {
                # Cardinal edges (mid-anchored)
                "outer right": {"loc": "center left", "bbox_to_anchor": (1.02, 0.5)},
                "outer left": {"loc": "center right", "bbox_to_anchor": (-0.02, 0.5)},
                "outer top": {"loc": "lower center", "bbox_to_anchor": (0.5, 1.02)},
                "outer bottom": {"loc": "upper center", "bbox_to_anchor": (0.5, -0.05)},
                # Corner anchored, right side
                "outer upper right": {
                    "loc": "upper left",
                    "bbox_to_anchor": (1.02, 1.0),
                },
                "outer lower right": {
                    "loc": "lower left",
                    "bbox_to_anchor": (1.02, 0.0),
                },
                # Corner anchored, left side
                "outer upper left": {
                    "loc": "upper right",
                    "bbox_to_anchor": (-0.02, 1.0),
                },
                "outer lower left": {
                    "loc": "lower right",
                    "bbox_to_anchor": (-0.02, 0.0),
                },
                # Edge-centered above/below (synonyms of outer top / outer bottom)
                "outer upper center": {
                    "loc": "lower center",
                    "bbox_to_anchor": (0.5, 1.02),
                },
                "outer lower center": {
                    "loc": "upper center",
                    "bbox_to_anchor": (0.5, -0.05),
                },
            }
            # Order-insensitive aliases — accept "outer right upper" etc.
            _OUTER_ALIASES = {
                "outer right upper": "outer upper right",
                "outer right lower": "outer lower right",
                "outer left upper": "outer upper left",
                "outer left lower": "outer lower left",
                "outer center upper": "outer upper center",
                "outer center lower": "outer lower center",
            }
            user_loc = kwargs.get("loc")
            if isinstance(user_loc, str):
                # Normalise: collapse runs of whitespace + lowercase.
                norm = " ".join(user_loc.lower().split())
                norm = _OUTER_ALIASES.get(norm, norm)
                if norm in _OUTER_VARIANTS:
                    if "bbox_to_anchor" not in kwargs:
                        kwargs["bbox_to_anchor"] = _OUTER_VARIANTS[norm][
                            "bbox_to_anchor"
                        ]
                    kwargs["loc"] = _OUTER_VARIANTS[norm]["loc"]
                    kwargs.setdefault("borderaxespad", 0.0)
                elif norm == "separate":
                    h_kw = kwargs.pop("handles", None)
                    l_kw = kwargs.pop("labels", None)
                    if h_kw is None or l_kw is None:
                        h_a, l_a = self._ax.get_legend_handles_labels()
                        h_kw = h_kw if h_kw is not None else h_a
                        l_kw = l_kw if l_kw is not None else l_a
                    sep_kw = {
                        k: v
                        for k, v in kwargs.items()
                        if k not in {"loc", "bbox_to_anchor", "borderaxespad"}
                    }
                    fig = self._ax.get_figure()
                    if not hasattr(fig, "_separate_legend_params"):
                        fig._separate_legend_params = []
                    fig._separate_legend_params.append(
                        {
                            "handles": list(h_kw),
                            "labels": list(l_kw),
                            "axis_id": getattr(self._ax, "_id", None) or hash(self._ax),
                            "figsize": sep_kw.pop("figsize", (4, 2)),
                            "frameon": sep_kw.pop("frameon", True),
                            "fancybox": sep_kw.pop("fancybox", False),
                            "shadow": sep_kw.pop("shadow", False),
                            "kwargs": sep_kw,
                        }
                    )
                    outer = _OUTER_VARIANTS["outer right"]
                    kwargs["loc"] = outer["loc"]
                    kwargs["bbox_to_anchor"] = outer["bbox_to_anchor"]
                    kwargs.setdefault("borderaxespad", 0.0)
            elif "loc" not in kwargs and "bbox_to_anchor" not in kwargs:
                # Silent default: matplotlib's 'best' auto-pick.
                # Earlier figrecipe defaulted to outer right; that
                # consistently shrank wide plots via constrained_layout.
                # Now defer to matplotlib and let the caller opt in
                # to outer placement explicitly via loc='outer …'.
                kwargs["loc"] = "best"

            legend = original_legend(*args, **kwargs)

            # Apply SCITEX style frame settings
            if legend is not None:
                style = load_style()
                legend_config = style.get("legend", {})

                frameon = legend_config.get("frameon", True)
                edge_mm = legend_config.get("edge_mm", 0.2)
                edgecolor = legend_config.get("edgecolor", "black")

                if frameon and edge_mm:
                    frame = legend.get_frame()
                    frame.set_linewidth(edge_mm * 72 / 25.4)  # mm to points
                    if edgecolor:
                        frame.set_edgecolor(edgecolor)

            # Record the legend call for reproduction
            if self._track and track:
                record_kwargs = kwargs.copy()
                # Handle custom handles - extract color/label info for serialization
                if "handles" in record_kwargs:
                    handles = record_kwargs.pop("handles")
                    handle_specs = []
                    for h in handles:
                        spec = {"label": h.get_label()}
                        if hasattr(h, "get_facecolor"):
                            spec["facecolor"] = list(h.get_facecolor())
                        if hasattr(h, "get_edgecolor"):
                            spec["edgecolor"] = list(h.get_edgecolor())
                        handle_specs.append(spec)
                    record_kwargs["_handle_specs"] = handle_specs

                self._recorder.record_call(
                    ax_position=self._position,
                    method_name="legend",
                    args=args,
                    kwargs=record_kwargs,
                    call_id=id,
                )

            return legend

        return wrapper

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
