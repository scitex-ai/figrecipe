#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render caption text for figrecipe compose figures.

Wires fr.compose(caption=..., panel_captions=...) into the
add_figure_caption / add_panel_captions public API.
"""

from typing import List, Optional, Union

import numpy as np

from .._wrappers import RecordingAxes, RecordingFigure


def _strip_markdown(text: str) -> str:
    return text.replace("**", "").replace("*", "")


def _flatten_axes(
    axes: Union[RecordingAxes, np.ndarray, List[RecordingAxes]],
) -> List[RecordingAxes]:
    """Flatten axes into 1D list."""
    if isinstance(axes, RecordingAxes):
        return [axes]
    if isinstance(axes, np.ndarray):
        return list(axes.flat)
    if isinstance(axes, list):
        result = []
        for row in axes:
            if isinstance(row, RecordingAxes):
                result.append(row)
            elif isinstance(row, list):
                result.extend(row)
        return result
    return [axes]


def render_compose_captions(
    fig: RecordingFigure,
    axes: Union[RecordingAxes, np.ndarray, List[RecordingAxes]],
    caption: Optional[str],
    panel_captions: Optional[List[str]],
) -> None:
    """Render caption text onto a composed figure.

    Persist caption in fig.record and render as fig.text.
    """
    flat = _flatten_axes(axes)
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig

    # Persist in record for round-trip
    if caption is not None:
        fig.record.caption = caption
    if panel_captions:
        fig.record.figure_panel_captions = panel_captions

    # --- Per-panel captions: render label + text above each panel ---
    if panel_captions:
        import string

        n = len(flat)
        labels = list(string.ascii_uppercase[:n])

        for i, (ax, label, cap_text) in enumerate(zip(flat, labels, panel_captions)):
            raw = ax._ax if hasattr(ax, "_ax") else ax
            pos = raw.get_position()
            x_center = pos.x0 + pos.width / 2.0
            y_top = pos.y1
            text = f"({label}) {cap_text}"
            text_kwargs = {"fontsize": 8, "ha": "center", "va": "bottom"}
            mpl_fig.text(
                x_center,
                y_top + 0.02,
                text,
                transform=mpl_fig.transFigure,
                **text_kwargs,
            )
            # Record each per-panel caption as a figure-level text so it REPLAYS
            # on reproduce. figure_texts are re-rendered via fig.text(), whose
            # default transform is transFigure -- matching the absolute x/y
            # captured here. Without this the panel captions rendered live but
            # were dropped on reproduce (only the figure-level caption, which
            # routes through add_figure_caption, round-tripped).
            if hasattr(fig, "record"):
                fig.record.figure_texts.append(
                    {
                        "x": x_center,
                        "y": y_top + 0.02,
                        "s": text,
                        "kwargs": dict(text_kwargs),
                    }
                )

    # --- Figure-level caption ---
    if caption:
        from .._captions._public import add_figure_caption

        add_figure_caption(fig, caption, position="bottom")


__all__ = [
    "render_compose_captions",
]
