#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wrapped Figure that manages recording."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple, Union

from matplotlib.figure import Figure

from ._axes import RecordingAxes
from ._figure_registry import register_recording_figure
from ._figure_text import FigureTextMixin

if TYPE_CHECKING:
    from .._recorder import FigureRecord, Recorder


class RecordingFigure(FigureTextMixin):
    """Wrapper around matplotlib Figure that manages recording.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The underlying matplotlib figure.
    recorder : Recorder
        The recorder instance.
    axes : list of RecordingAxes
        Wrapped axes objects.

    Examples
    --------
    >>> import figrecipe as ps
    >>> fig, ax = ps.subplots()
    >>> ax.plot([1, 2, 3], [4, 5, 6])
    >>> ps.save(fig, "my_figure.yaml")
    """

    def __init__(
        self,
        fig: Figure,
        recorder: "Recorder",
        axes: Union[RecordingAxes, List[RecordingAxes]],
    ):
        self._fig = fig
        self._recorder = recorder

        # Normalize axes to list
        if isinstance(axes, RecordingAxes):
            self._axes = [[axes]]
        elif isinstance(axes, list):
            if axes and isinstance(axes[0], list):
                self._axes = axes
            else:
                self._axes = [axes]
        else:
            self._axes = [[axes]]

        # Run finalize_ticks / finalize_special_plots on every draw
        # event — not just at fr.save() time. Without this hook, the
        # inline notebook backend renders before finalize is reached,
        # so MaxNLocator nice-tick logic never applies and matplotlib
        # AutoLocator defaults win.
        self._figrecipe_finalize_in_progress = False
        try:
            self._fig.canvas.mpl_connect("draw_event", self._on_draw_finalize)
        except AttributeError:
            pass  # headless / mock canvas (e.g. some test fixtures)

        # Register raw-figure -> wrapper so the module-level
        # ``figrecipe.pyplot.colorbar`` can route a manual ``plt.colorbar(...)``
        # back through ``self.colorbar`` (recording it for round-trip).
        register_recording_figure(self._fig, self)

    def _on_draw_finalize(self, event):
        """Apply figrecipe finalize hooks once per figure lifetime.

        Run-once: setting a new locator marks the canvas stale, which
        on the inline notebook backend triggers another draw and a
        SECOND inline render of the same figure. We only need to
        finalize once per figure — cache the flag and short-circuit
        on subsequent draws.

        Re-entrancy guard: finalize_ticks may swap a locator, which on
        some backends triggers another draw and would recurse. The
        flag breaks the loop.
        """
        if getattr(self, "_figrecipe_finalize_in_progress", False):
            return
        if getattr(self, "_figrecipe_finalized", False):
            return  # already finalized — avoid the inline re-render cascade
        self._figrecipe_finalize_in_progress = True
        try:
            from ..styles._finalize import (
                finalize_special_plots,
                finalize_ticks,
            )

            for ax in self._fig.get_axes():
                try:
                    finalize_ticks(ax)
                    finalize_special_plots(ax)
                except Exception:
                    pass  # never break a render on a finalize bug
        finally:
            self._figrecipe_finalize_in_progress = False
            self._figrecipe_finalized = True

    @property
    def fig(self) -> Figure:
        """Get the underlying matplotlib figure."""
        return self._fig

    @property
    def axes(self) -> List[List[RecordingAxes]]:
        """Get axes as 2D array."""
        return self._axes

    @property
    def dpi(self):
        """Proxy dpi to underlying figure.

        Needed as a class-level descriptor so matplotlib's _setattr_cm
        can do getattr(type(obj), 'dpi') during savefig/print_figure.
        """
        return self._fig.dpi

    @dpi.setter
    def dpi(self, value):
        self._fig.dpi = value

    def draw(self, renderer):
        """Proxy draw to underlying figure.

        Needed as a class-level method so matplotlib's _setattr_cm
        can do getattr(type(obj), 'draw') during _get_renderer.
        """
        return self._fig.draw(renderer)

    @property
    def flat(self) -> List[RecordingAxes]:
        """Get flattened list of all axes."""
        result = []
        for row in self._axes:
            for ax in row:
                result.append(ax)
        return result

    @property
    def record(self) -> "FigureRecord":
        """Get the figure record."""
        return self._recorder.figure_record

    def _get_style_fontsize(self, key: str, default: float) -> float:
        """Get fontsize from loaded style."""
        try:
            from ..styles._style_loader import _STYLE_CACHE

            if _STYLE_CACHE is not None:
                fonts = getattr(_STYLE_CACHE, "fonts", None)
                if fonts is not None:
                    return getattr(fonts, key, default)
        except Exception:
            pass
        return default

    def _get_theme_text_color(self, default: str = "black") -> str:
        """Get text color from loaded style's theme settings."""
        try:
            from ..styles._style_loader import _STYLE_CACHE

            if _STYLE_CACHE is not None:
                theme = getattr(_STYLE_CACHE, "theme", None)
                if theme is not None:
                    mode = getattr(theme, "mode", "light")
                    theme_colors = getattr(theme, mode, None)
                    if theme_colors is not None:
                        return getattr(theme_colors, "text", default)
        except Exception:
            pass
        return default

    # suptitle / supxlabel / supylabel / text live in FigureTextMixin
    # (._figure_text); the suptitle there inherits SCITEX_STYLE (size +
    # non-bold weight).

    def colorbar(self, mappable, ax=None, **kwargs) -> Any:
        """Add a colorbar and record it for reproduction.

        ``ax`` may be a single axes OR a list/array of axes (a shared colorbar
        that steals space from several panels, e.g.
        ``fig.colorbar(im, ax=axes.ravel().tolist())``). An explicit
        ``cax=<axes>`` (the colorbar is drawn into a caller-provided axes) and a
        standalone ``ScalarMappable`` are also handled. Every source axes is
        recorded in ``ax_keys``; the colorbar's resolved geometry is captured
        later at SAVE time (see ``_capture_colorbar_geometry``) so reproduction
        can pin it exactly. Recording logic lives in ``_figure_colorbar`` to keep
        this module within the per-file line budget.
        """
        from ._figure_colorbar import record_colorbar

        return record_colorbar(self, mappable, ax=ax, **kwargs)

    def add_panel_labels(
        self,
        labels: Optional[List[str]] = None,
        loc: str = "upper left",
        offset: Tuple[float, float] = (-0.1, 1.05),
        fontsize: Optional[float] = None,
        fontweight: str = "bold",
        **kwargs,
    ) -> List[Any]:
        """Add panel labels (A, B, C, D, etc.) to multi-panel figures.

        Parameters
        ----------
        labels : list of str, optional
            Custom labels. If None, uses uppercase letters (A, B, C, ...).
        loc : str
            Location hint: 'upper left' (default), 'upper right', 'lower left', 'lower right'.
        offset : tuple of float
            (x, y) offset in axes coordinates from the corner.
            Default is (-0.1, 1.05) for upper left positioning.
        fontsize : float, optional
            Font size in points. If None, uses style's title_pt or 10.
        fontweight : str
            Font weight (default: 'bold').
        **kwargs
            Additional arguments passed to ax.text().

        Returns
        -------
        list of Text
            The matplotlib Text objects created.

        Examples
        --------
        >>> fig, axes = fr.subplots(2, 2)
        >>> fig.add_panel_labels()  # Adds A, B, C, D
        >>> fig.add_panel_labels(['i', 'ii', 'iii', 'iv'])  # Custom labels
        >>> fig.add_panel_labels(loc='upper right', offset=(1.05, 1.05))
        """
        from ._panel_labels import add_panel_labels as _add_panel_labels

        # Get fontsize from style if not specified
        if fontsize is None:
            fontsize = self._get_style_fontsize("title_pt", 10)

        # Get theme text color (unless user provided 'color' in kwargs)
        if "color" not in kwargs:
            text_color = self._get_theme_text_color()
        else:
            text_color = kwargs.pop("color")

        def record_callback(info):
            self._recorder.figure_record.panel_labels = info

        return _add_panel_labels(
            all_axes=self.flat,
            labels=labels,
            loc=loc,
            offset=offset,
            fontsize=fontsize,
            fontweight=fontweight,
            text_color=text_color,
            record_callback=record_callback,
            **kwargs,
        )

    def set_title_metadata(self, title: str) -> "RecordingFigure":
        """Set figure title metadata (not rendered, stored in recipe).

        This is for storing a publication/reference title for the figure,
        separate from suptitle which is rendered on the figure.

        Parameters
        ----------
        title : str
            The figure title for publication/reference.

        Returns
        -------
        RecordingFigure
            Self for method chaining.

        Examples
        --------
        >>> fig, ax = fr.subplots()
        >>> fig.set_title_metadata("Effect of temperature on reaction rate")
        >>> fig.set_caption("Figure 1. Reaction rates measured at various temperatures.")
        """
        self._recorder.figure_record.title_metadata = title
        return self

    def set_caption(self, caption: str) -> "RecordingFigure":
        """Set figure caption metadata (not rendered, stored in recipe).

        This is for storing a publication caption for the figure,
        typically used in scientific papers (e.g., "Fig. 1. Description...").

        Parameters
        ----------
        caption : str
            The figure caption text.

        Returns
        -------
        RecordingFigure
            Self for method chaining.

        Examples
        --------
        >>> fig, ax = fr.subplots()
        >>> fig.set_caption("Figure 1. Temperature dependence of reaction rates.")
        """
        self._recorder.figure_record.caption = caption
        return self

    @property
    def title_metadata(self) -> Optional[str]:
        """Get the figure title metadata."""
        return self._recorder.figure_record.title_metadata

    @property
    def caption(self) -> Optional[str]:
        """Get the figure caption metadata."""
        return self._recorder.figure_record.caption

    def set_stats(self, stats: Dict[str, Any]) -> "RecordingFigure":
        """Set figure-level statistics metadata (not rendered, stored in recipe).

        Parameters
        ----------
        stats : dict
            Statistics dictionary (comparisons, summary, correction_method, alpha).
        """
        self._recorder.figure_record.stats = stats
        return self

    @property
    def stats(self) -> Optional[Dict[str, Any]]:
        """Get the figure-level statistics metadata."""
        return self._recorder.figure_record.stats

    def generate_caption(self, style: str = "publication", template: str = None) -> str:
        """Generate caption from stored stats. Styles: publication, brief, detailed."""
        from ._caption_generator import generate_figure_caption

        panels = [ax.caption for ax in self.flat if ax.caption]
        return generate_figure_caption(
            self.title_metadata, panels, self.stats, style, template
        )

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to underlying figure."""
        return getattr(self._fig, name)

    def savefig(
        self,
        fname,
        save_recipe: bool = True,
        include_data: bool = True,
        data_format: Literal["csv", "npz", "inline"] = "csv",
        csv_format: Literal["single", "separate"] = "separate",
        validate: bool = True,
        validate_mse_threshold: float = 100.0,
        validate_error_level: str = "error",
        verbose: bool = True,
        dpi: Optional[int] = None,
        image_format: Optional[str] = None,
        facecolor: Optional[str] = None,
        save_hitmap: bool = False,
        **kwargs,
    ):
        """Save figure — equivalent to fr.save(). Same DPI, crop, recipe.

        Returns (image_path, yaml_path, result).
        ``**kwargs`` passed to matplotlib savefig for file-like objects.
        """
        # Handle file-like objects (BytesIO, etc.) - direct matplotlib save
        if hasattr(fname, "write"):
            save_kwargs = dict(kwargs)
            if dpi is not None:
                save_kwargs["dpi"] = dpi
            if facecolor is not None:
                save_kwargs["facecolor"] = facecolor
            self._fig.savefig(fname, **save_kwargs)
            return fname, None, None

        from .._api._save import save_figure

        return save_figure(
            self,
            fname,
            save_recipe=save_recipe,
            include_data=include_data,
            data_format=data_format,
            csv_format=csv_format,
            validate=validate,
            validate_mse_threshold=validate_mse_threshold,
            validate_error_level=validate_error_level,
            verbose=verbose,
            dpi=dpi,
            image_format=image_format,
            facecolor=facecolor,
            save_hitmap=save_hitmap,
        )

    # set_supxyt / set_supxytc live in FigureTextMixin (._figure_text).

    def save_recipe(
        self,
        path: Union[str, Path],
        include_data: bool = True,
        data_format: Literal["csv", "npz", "inline"] = "csv",
        csv_format: Literal["single", "separate"] = "separate",
    ) -> Path:
        """Save the recording recipe to YAML.

        Parameters
        ----------
        path : str or Path
            Output path for the recipe file.
        include_data : bool
            If True, save array data alongside recipe.
        data_format : str
            Format for data files: 'csv' (default), 'npz', or 'inline'.
        csv_format : str
            CSV structure: 'separate' (default) or 'single' (scitex-compatible).
        """
        from .._serializer import save_recipe

        return save_recipe(
            self._recorder.figure_record, path, include_data, data_format, csv_format
        )


# Backward compat: create_recording_subplots moved to _subplots.py
from ._subplots import create_recording_subplots  # noqa: E402, F401
