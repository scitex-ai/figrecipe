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
    save_to_file : bool
        Whether to also save caption to a separate file.
    file_path : str, optional
        Path for caption file.

    Returns
    -------
    str
        The rendered caption text (Markdown-stripped).
    """
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

    # Reserve room for the caption BEFORE rendering, by adjusting axes
    # positions when they encroach on the caption strip.  The previous
    # implementation called ``mpl_fig.subplots_adjust(bottom=0.15)`` and
    # trusted that to move the panels, but on figrecipe's mm-laid figures
    # (the paper-figure default) the bottom-row axes stayed near y0≈0.05
    # and the caption text at y=0.02 landed on top of them.  We now
    # nudge each axes via ``set_position`` so the fix is robust to the
    # mm-layout path AND the plain subplots_adjust path.
    reserved = 0.15  # caption strip height in figure-fraction
    pad = 0.02  # gap between caption and nearest axes
    if position == "bottom":
        mpl_fig.subplots_adjust(bottom=reserved)
        mpl_fig.canvas.draw()
        mpl_axes = [ax for ax in mpl_fig.axes if ax.get_visible()]
        if mpl_axes:
            lowest = min(ax.get_position().y0 for ax in mpl_axes)
            if lowest < reserved + pad:
                delta = (reserved + pad) - lowest
                for ax in mpl_axes:
                    pos = ax.get_position()
                    new_height = max(0.05, pos.height - delta)
                    ax.set_position([pos.x0, pos.y0 + delta, pos.width, new_height])
        y_pos, va = 0.02, "bottom"
    else:
        mpl_fig.subplots_adjust(top=1.0 - reserved)
        mpl_fig.canvas.draw()
        mpl_axes = [ax for ax in mpl_fig.axes if ax.get_visible()]
        if mpl_axes:
            highest = max(ax.get_position().y1 for ax in mpl_axes)
            if highest > 1.0 - reserved - pad:
                delta = highest - (1.0 - reserved - pad)
                for ax in mpl_axes:
                    pos = ax.get_position()
                    new_height = max(0.05, pos.height - delta)
                    ax.set_position([pos.x0, pos.y0, pos.width, new_height])
        y_pos, va = 0.98, "top"

    clean_caption = _strip_markdown(caption)

    # Persist caption in the recipe record for round-trip.
    if hasattr(fig, "record"):
        fig.record.caption = caption
        fig.record.figure_texts.append(
            {
                "x": 0.5,
                "y": y_pos,
                "s": clean_caption,
                "kwargs": {
                    "ha": "center",
                    "va": va,
                    "fontsize": font_size,
                    "wrap": True,
                    "bbox": dict(
                        boxstyle="round,pad=0.5", facecolor="white", alpha=0.8
                    ),
                },
            }
        )

    # Render the caption text — ONCE.  This is the single source of
    # visual truth; ``caption_manager.add_figure_caption`` below is
    # called with ``render=False`` so it only registers metadata
    # (numbering, registry, optional file save) and does NOT draw a
    # second copy of the caption (the previous double-render bug stacked
    # two captions on the same y-anchor and they overlapped each other).
    mpl_fig.text(
        0.5,
        y_pos,
        clean_caption,
        ha="center",
        va=va,
        fontsize=font_size,
        wrap=True,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.8),
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
