#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extracted method implementations for RecordingAxes.

This module contains the explicit method wrappers (pie, imshow, violinplot,
graph, joyplot, swarmplot, text, annotate, add_stat_annotation) that were
extracted from _axes.py to keep that file under the line limit.
"""

from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from .._recorder import Recorder


class RecordingAxesMethods:
    """Mixin providing explicit method wrappers for RecordingAxes.

    These methods are extracted from RecordingAxes to keep the main
    file under 512 lines.
    """

    # These will be set by the main class
    _ax: "Axes"
    _recorder: "Recorder"
    _position: tuple
    _track: bool
    _result_refs: Dict[int, str]
    _RESULT_REFERENCING_METHODS: set
    _RESULT_REFERENCEABLE_METHODS: set

    def pie(
        self,
        x,
        *,
        id: Optional[str] = None,
        track: bool = True,
        **kwargs,
    ):
        """Pie chart with automatic SCITEX styling."""
        from ._axes_plots import pie_plot

        return pie_plot(
            self._ax,
            x,
            self._recorder,
            self._position,
            self._track and track,
            id,
            **kwargs,
        )

    def imshow(
        self,
        X,
        *,
        id: Optional[str] = None,
        track: bool = True,
        **kwargs,
    ):
        """Display image with automatic SCITEX styling."""
        from ._axes_plots import imshow_plot

        return imshow_plot(
            self._ax,
            X,
            self._recorder,
            self._position,
            self._track and track,
            id,
            **kwargs,
        )

    def violinplot(
        self,
        dataset,
        positions=None,
        *,
        id: Optional[str] = None,
        track: bool = True,
        inner: Optional[str] = None,
        colors=None,
        **kwargs,
    ):
        """Violin plot with support for inner display options.

        Parameters
        ----------
        colors : list, optional
            Colors for each violin body. If provided, these colors will be
            applied and recorded for pixel-perfect reproduction.
        """
        from ._axes_plots import violinplot_plot

        return violinplot_plot(
            self._ax,
            dataset,
            positions,
            self._recorder,
            self._position,
            self._track and track,
            id,
            inner,
            colors,
            **kwargs,
        )

    def boxplot(
        self,
        x,
        *,
        id: Optional[str] = None,
        track: bool = True,
        **kwargs,
    ):
        """Boxplot with patch_artist=True by default for editor color selection."""
        from ._boxplot import boxplot_plot

        return boxplot_plot(
            self._ax,
            x,
            self._recorder,
            self._position,
            self._track and track,
            id,
            **kwargs,
        )

    def graph(
        self,
        G,
        *,
        preset: Optional[str] = None,
        layout: Optional[str] = None,
        pos=None,
        seed: int = 42,
        # Node styling
        node_size=None,
        node_color=None,
        node_alpha: Optional[float] = None,
        node_shape: Optional[str] = None,
        node_edgecolors: Optional[str] = None,
        node_linewidths: Optional[float] = None,
        # Edge styling
        edge_width=None,
        edge_color=None,
        edge_alpha: Optional[float] = None,
        edge_style: Optional[str] = None,
        arrows=None,
        arrowsize: Optional[float] = None,
        arrowstyle: Optional[str] = None,
        connectionstyle: Optional[str] = None,
        # Labels
        labels=None,
        font_size: Optional[float] = None,
        font_color: Optional[str] = None,
        font_weight: Optional[str] = None,
        font_family: Optional[str] = None,
        # Colormap
        colormap: Optional[str] = None,
        vmin=None,
        vmax=None,
        # Recording
        id: Optional[str] = None,
        track: bool = True,
        **layout_kwargs,
    ):
        """Draw a NetworkX graph with publication-quality styling.

        See _axes_graph.graph_plot for full parameter documentation.
        """
        try:
            from ._axes_graph import graph_plot
        except ImportError as e:
            if "networkx" in str(e):
                raise ImportError(
                    "Graph visualization requires networkx. Install with:\n"
                    "  pip install figrecipe[graph]\n"
                    "or:\n"
                    "  pip install networkx"
                ) from None
            raise

        return graph_plot(
            self._ax,
            G,
            self._recorder,
            self._position,
            self._track and track,
            id,
            preset=preset,
            pos=pos,
            seed=seed,
            layout=layout,
            node_size=node_size,
            node_color=node_color,
            node_alpha=node_alpha,
            node_shape=node_shape,
            node_edgecolors=node_edgecolors,
            node_linewidths=node_linewidths,
            edge_width=edge_width,
            edge_color=edge_color,
            edge_alpha=edge_alpha,
            edge_style=edge_style,
            arrows=arrows,
            arrowsize=arrowsize,
            arrowstyle=arrowstyle,
            connectionstyle=connectionstyle,
            labels=labels,
            font_size=font_size,
            font_color=font_color,
            font_weight=font_weight,
            font_family=font_family,
            colormap=colormap,
            vmin=vmin,
            vmax=vmax,
            **layout_kwargs,
        )

    def joyplot(
        self,
        arrays,
        *,
        overlap: float = 0.5,
        fill_alpha: float = 0.7,
        line_alpha: float = 1.0,
        colors=None,
        labels=None,
        id: Optional[str] = None,
        track: bool = True,
        **kwargs,
    ):
        """Create a joyplot (ridgeline plot) for distribution comparison."""
        from ._axes_plots import joyplot_plot

        return joyplot_plot(
            self._ax,
            self,
            arrays,
            self._recorder,
            self._position,
            self._track and track,
            id,
            overlap,
            fill_alpha,
            line_alpha,
            colors,
            labels,
            **kwargs,
        )

    def swarmplot(
        self,
        data,
        positions=None,
        *,
        size: float = None,
        color=None,
        alpha: float = 0.7,
        jitter: float = 0.3,
        id: Optional[str] = None,
        track: bool = True,
        **kwargs,
    ):
        """Create a swarm plot (beeswarm plot) showing individual data points."""
        from ._axes_plots import swarmplot_plot

        return swarmplot_plot(
            self._ax,
            data,
            positions,
            self._recorder,
            self._position,
            self._track and track,
            id,
            size,
            color,
            alpha,
            jitter,
            **kwargs,
        )

    def add_stat_annotation(self, x1: float, x2: float, **kwargs):
        """Add a statistical comparison annotation (bracket with stars/p-value).

        Pass ``stat=StatResult(...)`` to render the full six-stat doctrine
        annotation (n, CI, method, p, effect size, test statistic — italic symbols)
        instead of hand-typing the mathtext; pass ``p_value=`` for stars only.
        See ``_stat_annotation.record_stat_annotation`` for the full signature.
        """
        from ._stat_annotation import record_stat_annotation

        return record_stat_annotation(self, x1, x2, **kwargs)

    def _serialize_transform(self, transform) -> str:
        """Convert matplotlib transform to serializable marker."""
        if transform is None:
            return "data"

        if transform is self._ax.transAxes:
            return "axes"
        if transform is self._ax.transData:
            return "data"
        if hasattr(self._ax, "figure") and transform is self._ax.figure.transFigure:
            return "figure"

        transform_str = str(transform)
        if "transAxes" in transform_str:
            return "axes"
        if "transFigure" in transform_str:
            return "figure"

        return "data"

    def text(
        self,
        x,
        y,
        s,
        *,
        id: Optional[str] = None,
        track: bool = True,
        fontsize=None,
        **kwargs,
    ):
        """Add text to axes with style-aware default fontsize.

        When using a figrecipe style (e.g., SCITEX), the `annotation_pt` font size
        from the style is used as the default if `fontsize` is not specified.
        """
        from ..styles._internal import get_style

        if fontsize is None:
            style = get_style()
            if style:
                fontsize = style.get("fonts", {}).get("annotation_pt", None)

        text_kwargs = kwargs.copy()
        if fontsize is not None:
            text_kwargs["fontsize"] = fontsize

        result = self._ax.text(x, y, s, **text_kwargs)

        if self._track and track:
            record_kwargs = text_kwargs.copy()
            if "transform" in record_kwargs:
                record_kwargs["transform"] = self._serialize_transform(
                    record_kwargs["transform"]
                )
            from ._axes_helpers import record_call_with_color_capture

            record_call_with_color_capture(
                self._recorder,
                self._position,
                "text",
                (x, y, s),
                record_kwargs,
                result,
                id,
                self._result_refs,
                self._RESULT_REFERENCING_METHODS,
                self._RESULT_REFERENCEABLE_METHODS,
            )

        return result

    def annotate(
        self,
        text,
        xy,
        *,
        xytext=None,
        id: Optional[str] = None,
        track: bool = True,
        fontsize=None,
        **kwargs,
    ):
        """Add annotation to axes with style-aware default fontsize."""
        from ..styles._internal import get_style

        if fontsize is None:
            style = get_style()
            if style:
                fontsize = style.get("fonts", {}).get("annotation_pt", None)

        annotate_kwargs = kwargs.copy()
        if fontsize is not None:
            annotate_kwargs["fontsize"] = fontsize
        if xytext is not None:
            annotate_kwargs["xytext"] = xytext

        result = self._ax.annotate(text, xy, **annotate_kwargs)

        if self._track and track:
            record_kwargs = annotate_kwargs.copy()
            if "textcoords" in record_kwargs:
                record_kwargs["textcoords"] = (
                    self._serialize_transform(record_kwargs.get("textcoords"))
                    if not isinstance(record_kwargs["textcoords"], str)
                    else record_kwargs["textcoords"]
                )
            if "xycoords" in record_kwargs:
                record_kwargs["xycoords"] = (
                    self._serialize_transform(record_kwargs.get("xycoords"))
                    if not isinstance(record_kwargs["xycoords"], str)
                    else record_kwargs["xycoords"]
                )
            from ._axes_helpers import record_call_with_color_capture

            record_call_with_color_capture(
                self._recorder,
                self._position,
                "annotate",
                (text, xy),
                record_kwargs,
                result,
                id,
                self._result_refs,
                self._RESULT_REFERENCING_METHODS,
                self._RESULT_REFERENCEABLE_METHODS,
            )

        return result


__all__ = ["RecordingAxesMethods"]

# EOF
