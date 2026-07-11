#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Public caption API — clean, simple, no Markdown noise.

This module provides the figrecipe public caption surface:
- ``add_figure_caption(fig, text, position="bottom")``
- ``add_panel_captions(fig, axes, texts, position="top_left")``

The internal ``ScientificCaption`` class adds Markdown formatting
(e.g. ``**Figure 1.**``) which matplotlib cannot render.  This wrapper
strips it so users get what they typed.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from ._caption import caption_manager


def _strip_markdown(text: str) -> str:
    """Remove Markdown bold/italic markers from text."""
    return text.replace("**", "").replace("*", "")


class _NullRecord:
    """Stand-in record for a bare matplotlib Figure (no ``fig.record``).

    The band helpers mirror geometry into a record so the recipe round-trips;
    when there is nothing to round-trip (a plain ``Figure``), they harmlessly
    write to this throwaway object instead.
    """

    def __init__(self) -> None:
        self.figsize = None
        self.layout = None
        self.mm_layout = None
        self.figure_texts: list = []
        self.caption = None


def add_figure_caption(
    fig: Any,
    caption: str,
    *,
    figure_label: Optional[str] = None,
    style: str = "scientific",
    position: str = "bottom",
    width_ratio: float = 0.9,
    font_size: Union[str, int] = "small",
    wrap_width: int = 80,
    align: str = "justify",
    pad_mm: float = 2.0,
    save_to_file: bool = False,
    file_path: Optional[str] = None,
) -> str:
    """Add a figure caption.

    The caption text is stripped of Markdown formatting (bold/italic)
    so it renders cleanly in matplotlib.  The caption is also recorded
    on ``fig.record.caption`` so it survives save→reproduce round-trip.

    Parameters
    ----------
    fig : matplotlib.figure.Figure or RecordingFigure
        The figure to add caption to.
    caption : str
        The caption text (Markdown formatting is automatically stripped).
    figure_label : str, optional
        Custom figure label (e.g. "Figure 1").  Auto-generated if None.
    style : str
        Caption style: "scientific", "nature", "ieee", "apa".
    position : str
        Caption position: "bottom" (default) or "top".
    width_ratio : float
        Width of caption relative to figure width.
    font_size : str or int
        Font size for caption text.
    wrap_width : int
        Character width for text wrapping.
    align : str
        Caption alignment: "justify" (default), "left", or "center".
        "justify" spans the full content width with the last line
        left-aligned.
    pad_mm : float
        Gap (mm) between the caption band and the axes / figure edge.
    save_to_file : bool
        Whether to also save caption to a separate file.
    file_path : str, optional
        Path for caption file.

    Returns
    -------
    str
        The rendered caption text (Markdown-stripped).
    """
    # Fail loud on caption content that breaks downstream LaTeX (FR-CAP-001).
    from ._validate import check_caption_latex_safe

    check_caption_latex_safe(caption, "the figure caption")

    # Resolve the underlying matplotlib Figure (RecordingFigure wraps it).
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig

    # Manuscript mode: record the caption (canonical YAML + numbering/sidecar)
    # but do NOT reserve canvas space or draw it — LaTeX typesets the caption
    # from the emitted .tex sidecar, so baking it onto the PNG would double-
    # render. The image stays clean; the drawn copy is a derived view.
    from ._manuscript_mode import is_manuscript_mode

    if is_manuscript_mode():
        if hasattr(fig, "record"):
            fig.record.caption = caption
        caption_manager.add_figure_caption(
            fig,
            caption,
            figure_label=figure_label,
            style=style,
            position=position,
            width_ratio=width_ratio,
            font_size=font_size,
            wrap_width=wrap_width,
            save_to_file=save_to_file,
            file_path=file_path,
            render=False,
        )
        return _strip_markdown(caption)

    # ADDITIVE caption band: the figure GROWS by a caption band and the axes
    # keep their EXACT mm size/position (identical to the no-caption figure).
    # The previous implementation reserved space by SHRINKING the axes (a fixed
    # 0.15 strip + per-axes ``set_position``), which on figrecipe's mm-precise
    # figures grew the multi-line caption into the axes/xlabel and crowded the
    # ylabel. We never shrink axes now: ``extend_figure_for_caption`` enlarges
    # the canvas + rewrites subplotpars so the axes land at the same physical
    # place, and ``place_caption`` draws the caption into the freed band and
    # records every drawn fragment for verbatim save->reproduce replay.
    from ._band import (
        caption_band_inches,
        extend_figure_for_caption,
        place_caption,
        resolve_caption_font_pt,
        wrap_caption_lines,
    )

    clean_caption = _strip_markdown(caption)

    font_pt = resolve_caption_font_pt(font_size, mpl_fig)
    lines = wrap_caption_lines(clean_caption, wrap_width)
    band_in = caption_band_inches(len(lines), font_pt, pad_mm)

    # Persist the caption text itself for round-trip metadata.
    if hasattr(fig, "record"):
        fig.record.caption = caption

    record = fig.record if hasattr(fig, "record") else _NullRecord()

    extend_figure_for_caption(mpl_fig, record, band_in, position)
    # Render the caption text — ONCE. This is the single source of visual truth;
    # ``caption_manager.add_figure_caption`` below is called with render=False so
    # it only registers metadata and does NOT draw a second copy.
    place_caption(
        mpl_fig,
        record,
        lines,
        font_pt,
        position,
        align,
        band_in,
        width_ratio,
    )

    # Register with internal manager for numbering/export ONLY.
    caption_manager.add_figure_caption(
        fig,
        caption,
        figure_label=figure_label,
        style=style,
        position=position,
        width_ratio=width_ratio,
        font_size=font_size,
        wrap_width=wrap_width,
        save_to_file=save_to_file,
        file_path=file_path,
        render=False,
    )

    return clean_caption


def add_panel_captions(
    fig: Any,
    axes: Any,
    panel_captions: Union[List[str], Dict[str, str]],
    *,
    main_caption: str = "",
    figure_label: Optional[str] = None,
    panel_style: str = "letter_bold",
    position: str = "top_left",
    font_size: Union[str, int] = "medium",
    offset: Tuple[float, float] = (0.02, 0.98),
) -> Dict[str, str]:
    """Add panel captions (A, B, C, etc.) to subplot panels.

    Panel labels are rendered with Markdown-stripped text so they
    display cleanly in matplotlib.

    Parameters
    ----------
    fig : matplotlib.figure.Figure or RecordingFigure
        The figure containing panels.
    axes : Axes, list, or ndarray
        Axes objects for each panel.
    panel_captions : list or dict
        Caption text for each panel.
    main_caption : str
        Main figure caption (optional, auto-attached).
    figure_label : str, optional
        Figure label for the main caption.
    panel_style : str
        Panel label style: "letter_bold", "letter_italic", "number".
    position : str
        Panel label position: "top_left", "top_right", etc.
    font_size : str or int
        Font size for panel labels.
    offset : tuple
        Position offset for panel labels.

    Returns
    -------
    dict
        Dictionary mapping panel labels to full caption text.
    """
    return caption_manager.add_panel_captions(
        fig,
        axes,
        panel_captions,
        main_caption=main_caption,
        figure_label=figure_label,
        panel_style=panel_style,
        position=position,
        font_size=font_size,
        offset=offset,
    )


__all__ = [
    "add_figure_caption",
    "add_panel_captions",
]
