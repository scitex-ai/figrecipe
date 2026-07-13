#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Statistical annotation drawing utilities for comparison brackets and stars."""

from typing import Any, Dict, List, Literal, Optional

from matplotlib.axes import Axes


def get_theme_text_color(default: str = "black") -> str:
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


def get_style_value(section: str, key: str, default: Any) -> Any:
    """Get a value from loaded style settings.

    Parameters
    ----------
    section : str
        Style section (e.g., 'fonts', 'lines', 'stat_annotation')
    key : str
        Key within the section (e.g., 'annotation_pt', 'bracket_mm')
    default : Any
        Default value if not found
    """
    try:
        from ..styles._style_loader import _STYLE_CACHE

        if _STYLE_CACHE is not None:
            section_obj = getattr(_STYLE_CACHE, section, None)
            if section_obj is not None:
                return getattr(section_obj, key, default)
    except Exception:
        pass
    return default


def p_to_stars(p_value: float, ns_symbol: bool = True) -> str:
    """Convert p-value to significance stars.

    Parameters
    ----------
    p_value : float
        The p-value to convert.
    ns_symbol : bool
        If True, return "n.s." for non-significant. If False, return "".

    Returns
    -------
    str
        Stars representation: "***" (p<0.001), "**" (p<0.01),
        "*" (p<0.05), "n.s." or "" (p>=0.05).
    """
    if p_value < 0.001:
        return "***"
    elif p_value < 0.01:
        return "**"
    elif p_value < 0.05:
        return "*"
    else:
        return "n.s." if ns_symbol else ""


def draw_stat_annotation(
    ax: Axes,
    x1: float,
    x2: float,
    y: Optional[float] = None,
    text: Optional[str] = None,
    p_value: Optional[float] = None,
    style: Literal["stars", "p_value", "both", "bracket_only"] = "stars",
    bracket_height: Optional[float] = None,
    text_offset: Optional[float] = None,
    color: Optional[str] = None,
    linewidth: Optional[float] = None,
    fontsize: Optional[float] = None,
    fontweight: Optional[str] = None,
    **kwargs,
) -> List[Any]:
    """Draw a statistical comparison bracket with annotation.

    Parameters
    ----------
    ax : Axes
        The matplotlib axes to draw on.
    x1, x2 : float
        X positions of the two groups being compared.
    y : float, optional
        Y position for the bracket. If None, auto-calculated from data.
    text : str, optional
        Custom text to display. Overrides p_value formatting.
    p_value : float, optional
        P-value for automatic star conversion.
    style : str
        Display style: "stars", "p_value", "both", "bracket_only".
    bracket_height : float
        Height of bracket tips as fraction of axes height.
    text_offset : float
        Offset of text above bracket as fraction of axes height.
    color : str
        Color for bracket and text.
    linewidth : float
        Line width for bracket.
    fontsize : float
        Font size for annotation text.
    **kwargs
        Additional kwargs passed to ax.text().

    Returns
    -------
    list
        List of matplotlib artists created (lines and text).
    """
    artists = []

    from .._utils._units import mm_to_pt

    # Resolve values from style if not explicitly provided
    if color is None:
        color = get_theme_text_color(default="black")
    if bracket_height is None:
        bracket_height = get_style_value("stat_annotation", "bracket_height", 0.03)
    if text_offset is None:
        text_offset = get_style_value("stat_annotation", "text_offset", 0.01)
    if linewidth is None:
        # Read mm value and convert to points
        linewidth_mm = get_style_value("stat_annotation", "linewidth_mm", 0.2)
        linewidth = mm_to_pt(linewidth_mm)

    # Font settings from style: both stars and p-values use same fontsize_pt
    # Stars are bold, p-values are normal weight
    annotation_fontsize = get_style_value("stat_annotation", "fontsize_pt", 6)
    stars_fontweight = get_style_value("stat_annotation", "stars_fontweight", "bold")

    # Get axes limits for relative positioning
    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0]

    # Auto-calculate y position if not provided
    if y is None:
        # Find max y value in the x range and add padding
        y = ylim[1] + y_range * 0.05

    # Calculate bracket dimensions in data coordinates
    tip_height = y_range * bracket_height
    text_y_offset = y_range * text_offset

    # Draw bracket: horizontal line with vertical tips
    # Left tip
    line1 = ax.plot(
        [x1, x1], [y - tip_height, y], color=color, linewidth=linewidth, clip_on=False
    )[0]
    artists.append(line1)

    # Horizontal bar
    line2 = ax.plot([x1, x2], [y, y], color=color, linewidth=linewidth, clip_on=False)[
        0
    ]
    artists.append(line2)

    # Right tip
    line3 = ax.plot(
        [x2, x2], [y, y - tip_height], color=color, linewidth=linewidth, clip_on=False
    )[0]
    artists.append(line3)

    # Determine annotation text and whether it's stars-only
    is_stars_only = False
    if text is None and style != "bracket_only":
        if p_value is not None:
            if style == "stars":
                text = p_to_stars(p_value)
                # Only bold for actual stars, not for n.s.
                is_stars_only = text not in ("n.s.", "")
            elif style == "p_value":
                # Use italic p with spaces around operators
                if p_value < 0.001:
                    text = r"$\it{p}$ < 0.001"
                else:
                    text = rf"$\it{{p}}$ = {p_value:.3f}"
            elif style == "both":
                stars = p_to_stars(p_value)
                # Use italic p with spaces around operators
                if p_value < 0.001:
                    text = rf"{stars} ($\it{{p}}$ < 0.001)"
                else:
                    text = rf"{stars} ($\it{{p}}$ = {p_value:.3f})"

    # Draw text if available
    if text and style != "bracket_only":
        text_x = (x1 + x2) / 2
        text_y = y + text_y_offset

        # Use same fontsize for stars and p-values, but stars are bold
        effective_fontsize = fontsize if fontsize is not None else annotation_fontsize
        if is_stars_only:
            effective_fontweight = (
                fontweight if fontweight is not None else stars_fontweight
            )
        else:
            effective_fontweight = fontweight if fontweight is not None else "normal"

        text_kwargs = {
            "ha": "center",
            "va": "bottom",
            "fontsize": effective_fontsize,
            "fontweight": effective_fontweight,
            "color": color,
        }
        text_kwargs.update(kwargs)
        txt = ax.text(text_x, text_y, text, **text_kwargs)
        artists.append(txt)

    return artists


def record_stat_annotation(
    recording_axes: Any,
    x1: float,
    x2: float,
    p_value: Optional[float] = None,
    text: Optional[str] = None,
    y: Optional[float] = None,
    style: Optional[str] = None,
    stat: Optional[Any] = None,
    require_complete: bool = True,
    sep: str = ", ",
    precision: int = 3,
    stars: bool = False,
    id: Optional[str] = None,
    track: bool = True,
    **kwargs,
) -> List[Any]:
    """Draw a stat annotation on a ``RecordingAxes`` and record it for replay.

    The recording half of ``RecordingAxes.add_stat_annotation`` — kept here, beside
    the drawing code it wraps, rather than in ``_axes_methods.py`` where it is only
    a method by accident of the mixin.

    A supplied ``stat`` (a :class:`figrecipe.StatResult`) is resolved to plain
    ``text`` + ``p_value`` *before* recording, so the recipe stores the rendered
    string and replays byte-identically without needing to re-import the producer's
    result object.

    Parameters
    ----------
    recording_axes : RecordingAxes
        The wrapper whose ``_ax`` is drawn on and whose recorder is updated.
    stat : StatResult, optional
        Completed test result. Under the default ``style="six_stat"`` its six
        doctrine fields are rendered inline with italic symbols.
    require_complete : bool
        Warn when ``stat`` is missing any of the six required fields.
    sep : str
        Separator between the six fields. Pass ``",\\n"`` to wrap the annotation
        onto two lines when a panel is too narrow for one. Ignored unless ``stat``
        is rendering the text.
    precision : int
        Decimal places on the p-value before it collapses to ``< 0.001``.
    stars : bool
        Prepend the significance stars above the six-stat line.
    """
    if style is None:
        style = "six_stat" if stat is not None else "stars"

    if stat is not None:
        if p_value is None:
            p_value = stat.p_value
        if text is None and style == "six_stat":
            text = stat.annotation(
                sep=sep,
                precision=precision,
                stars=stars,
                require_complete=require_complete,
            )

    draw_kwargs = {
        key: value
        for key, value in kwargs.items()
        if key
        not in (
            "bracket_height",
            "text_offset",
            "color",
            "linewidth",
            "fontsize",
            "fontweight",
        )
    }
    styling = {
        key: kwargs[key]
        for key in (
            "bracket_height",
            "text_offset",
            "color",
            "linewidth",
            "fontsize",
            "fontweight",
        )
        if key in kwargs
    }

    artists = draw_stat_annotation(
        recording_axes._ax,
        x1,
        x2,
        y=y,
        text=text,
        p_value=p_value,
        style=style,
        **styling,
        **draw_kwargs,
    )

    if recording_axes._track and track:
        recorder = recording_axes._recorder
        call_id = id if id else recorder._generate_call_id("stat_annotation")
        record_kwargs = {
            "x1": x1,
            "x2": x2,
            "p_value": p_value,
            "text": text,
            "y": y,
            "style": style,
        }
        record_kwargs.update(styling)
        record_kwargs.update(draw_kwargs)
        record_kwargs = {k: v for k, v in record_kwargs.items() if v is not None}

        from .._recorder import CallRecord

        record = CallRecord(
            id=call_id,
            function="stat_annotation",
            args=[],
            kwargs=record_kwargs,
            ax_position=recording_axes._position,
        )
        ax_record = recorder.figure_record.get_or_create_axes(*recording_axes._position)
        ax_record.add_decoration(record)

    return artists


def calculate_auto_y(
    ax: Axes,
    x1: float,
    x2: float,
    existing_annotations: List[Dict[str, Any]],
    padding: float = 0.05,
) -> float:
    """Calculate automatic y position for a new annotation.

    Avoids overlapping with existing annotations by stacking.

    Parameters
    ----------
    ax : Axes
        The matplotlib axes.
    x1, x2 : float
        X positions of the comparison.
    existing_annotations : list
        List of existing annotation info dicts with x1, x2, y keys.
    padding : float
        Padding as fraction of y range.

    Returns
    -------
    float
        Suggested y position for the new annotation.
    """
    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0]
    pad = y_range * padding

    # Start above the data
    y = ylim[1] + pad

    # Check for overlaps with existing annotations
    for ann in existing_annotations:
        ann_x1, ann_x2 = ann.get("x1", 0), ann.get("x2", 0)
        ann_y = ann.get("y", 0)

        # Check if x ranges overlap
        if not (x2 < ann_x1 or x1 > ann_x2):
            # Overlapping x range, need to stack
            y = max(y, ann_y + pad * 2)

    return y
