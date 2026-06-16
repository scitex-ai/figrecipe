#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figure-level super-text methods for RecordingFigure.

Extracted from ``_figure.py`` to keep that module focused. ``FigureTextMixin``
provides the figure-wide text helpers (suptitle / supxlabel / supylabel /
text / set_supxyt / set_supxytc). The mixin relies on attributes and helpers
supplied by ``RecordingFigure``: ``self._fig``, ``self._recorder``,
``self._get_style_fontsize`` and ``self.set_caption``.
"""

from typing import Any, Optional


class FigureTextMixin:
    """Super-text (suptitle / supxlabel / supylabel / text) methods."""

    def suptitle(self, t: str, **kwargs) -> Any:
        """Set super title for the figure and record it.

        Parameters
        ----------
        t : str
            The super title text.
        **kwargs
            Additional arguments passed to matplotlib's suptitle().

        Returns
        -------
        Text
            The matplotlib Text object.

        Notes
        -----
        When the caller does not specify them explicitly, the font size is
        inherited from the active SCITEX_STYLE (``fonts.suptitle_pt``, ~7 pt)
        and the font weight defaults to ``"normal"`` (not bold), so a bare
        ``fig.suptitle("...")`` matches the style rather than matplotlib's
        bold suptitle default. Either matplotlib alias (``size`` /
        ``weight``) is respected when supplied.
        """
        # Auto-apply fontsize from style if not specified (accept the ``size``
        # alias too, so an explicit caller value always wins).
        if "fontsize" not in kwargs and "size" not in kwargs:
            kwargs["fontsize"] = self._get_style_fontsize("suptitle_pt", 7)
        # Default to non-bold so the suptitle inherits the style rather than
        # matplotlib's bold default. Respect either alias if provided.
        if "fontweight" not in kwargs and "weight" not in kwargs:
            kwargs["fontweight"] = "normal"
        # Record the suptitle call
        self._recorder.figure_record.suptitle = {"text": t, "kwargs": kwargs}
        # Call the underlying figure's suptitle
        return self._fig.suptitle(t, **kwargs)

    def supxlabel(self, t: str, **kwargs) -> Any:
        """Set super x-label for the figure and record it.

        Parameters
        ----------
        t : str
            The super x-label text.
        **kwargs
            Additional arguments passed to matplotlib's supxlabel().

        Returns
        -------
        Text
            The matplotlib Text object.
        """
        # Auto-apply fontsize from style if not specified
        if "fontsize" not in kwargs:
            kwargs["fontsize"] = self._get_style_fontsize("supxlabel_pt", 8)
        # Record the supxlabel call
        self._recorder.figure_record.supxlabel = {"text": t, "kwargs": kwargs}
        # Call the underlying figure's supxlabel
        return self._fig.supxlabel(t, **kwargs)

    def supylabel(self, t: str, **kwargs) -> Any:
        """Set super y-label for the figure and record it.

        Parameters
        ----------
        t : str
            The super y-label text.
        **kwargs
            Additional arguments passed to matplotlib's supylabel().

        Returns
        -------
        Text
            The matplotlib Text object.
        """
        # Auto-apply fontsize from style if not specified
        if "fontsize" not in kwargs:
            kwargs["fontsize"] = self._get_style_fontsize("supylabel_pt", 8)
        # Record the supylabel call
        self._recorder.figure_record.supylabel = {"text": t, "kwargs": kwargs}
        # Call the underlying figure's supylabel
        return self._fig.supylabel(t, **kwargs)

    def text(self, x: float, y: float, s: str, **kwargs) -> Any:
        """Place text on the figure and record it.

        Proxy for ``matplotlib.figure.Figure.text`` that also captures the
        call in the recipe so ``reproduce()`` can replay it. Without this,
        ``fig.text`` annotations would be rendered in the original figure
        but missing from the reproduction, leading to dimension mismatches
        during reproducibility validation.

        Parameters
        ----------
        x, y : float
            Position in figure coordinates.
        s : str
            The text string.
        **kwargs
            Additional arguments passed to matplotlib's fig.text().

        Returns
        -------
        Text
            The matplotlib Text object.
        """
        serializable_kwargs = {
            k: v
            for k, v in kwargs.items()
            if isinstance(v, (str, int, float, bool, list, tuple, type(None)))
        }
        self._recorder.figure_record.figure_texts.append(
            {"x": x, "y": y, "s": s, "kwargs": serializable_kwargs}
        )
        return self._fig.text(x, y, s, **kwargs)

    def set_supxyt(
        self,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs,
    ) -> "FigureTextMixin":
        """Set supxlabel, supylabel, and suptitle in one call.

        Parameters
        ----------
        xlabel : str, optional
        ylabel : str, optional
        title : str, optional
        **kwargs : dict
            Passed to the underlying methods.

        Examples
        --------
        >>> fig.set_supxyt('Time (s)', 'Amplitude', 'All Channels')
        """
        if xlabel is not None:
            self.supxlabel(xlabel, **kwargs)
        if ylabel is not None:
            self.supylabel(ylabel, **kwargs)
        if title is not None:
            self.suptitle(title, **kwargs)
        return self

    def set_supxytc(
        self,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        title: Optional[str] = None,
        caption: Optional[str] = None,
        **kwargs,
    ) -> "FigureTextMixin":
        """Set supxlabel, supylabel, suptitle, and caption in one call.

        Parameters
        ----------
        xlabel : str, optional
        ylabel : str, optional
        title : str, optional
        caption : str, optional
            Figure caption metadata (stored in recipe, not rendered).
        **kwargs : dict
            Passed to the underlying methods.

        Examples
        --------
        >>> fig.set_supxytc('Time', 'Voltage', 'Neural Data',
        ...                 'Figure 1. Overview of neural recordings.')
        """
        self.set_supxyt(xlabel, ylabel, title, **kwargs)
        if caption is not None:
            self.set_caption(caption)
        return self


# EOF
