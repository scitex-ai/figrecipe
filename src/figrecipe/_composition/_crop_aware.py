#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Crop-aware panel placement for mm-based composition.

Maps a source axes into its panel rectangle using the *tight content box*
captured at save time (``FigureRecord.content_bbox`` +
``AxesRecord.bbox_uncropped``), so a composed panel reproduces the clean,
cropped standalone render instead of the padded ``figsize``. This is what makes
``fr.compose`` tile panels with no clipped tick labels and no dead space
between the panel label and the plot.

Falls back to the legacy cropped-fraction ``bbox`` (and finally to filling the
whole panel) when the crop-aware fields are absent, so recipes written by older
figrecipe versions still compose without error.
"""

from typing import Tuple


def panel_rel_bbox(source_record, ax_record) -> Tuple[float, float, float, float]:
    """Return an axes' (left, bottom, width, height) within its panel rectangle.

    The returned fractions are relative to the panel rectangle. When the caller
    sizes that rectangle to the source's ``content_size_mm`` (recommended; the
    neurovista/smart composer does), the axes reproduces the standalone layout
    1:1; with any other panel size the content simply scales to fit. Preference:

    1. Crop-aware -- ``bbox_uncropped`` expressed relative to the figure's tight
       ``content_bbox`` (panel == tight content; labels/marginals included).
    2. Legacy -- the cropped-fraction ``bbox`` (panel == cropped image).
    3. Fill the whole panel.

    Values are normally in [0, 1]; they may slightly exceed it when the source
    content overflowed its canvas (the panel is sized to include the overflow).
    """
    content_bbox = getattr(source_record, "content_bbox", None)
    ub = getattr(ax_record, "bbox_uncropped", None)
    if (
        content_bbox is not None
        and len(content_bbox) == 4
        and ub is not None
        and len(ub) == 4
    ):
        cx0, cy0, cw, ch = content_bbox
        if cw > 0 and ch > 0:
            return (ub[0] - cx0) / cw, (ub[1] - cy0) / ch, ub[2] / cw, ub[3] / ch

    bbox = getattr(ax_record, "bbox", None)
    if bbox is not None and len(bbox) == 4:
        return bbox[0], bbox[1], bbox[2], bbox[3]

    return 0.0, 0.0, 1.0, 1.0


def _apply_source_style(mpl_ax, source_record) -> None:
    """Apply a source panel's recorded style to its composed axes.

    The composed figure is created with a bare matplotlib figure, so without
    this the replayed text renders in matplotlib's default (wide) font instead
    of the panel's publication font -- which shifts text metrics and clips long
    tick labels. Re-applying the style (font family + sizes, spines, ticks) is
    exactly what ``fr.subplots`` does for a standalone panel, so a composed
    panel reproduces the standalone text metrics. Best-effort.
    """
    style = getattr(source_record, "style", None)
    if not style:
        try:
            from ..presets._scitex_style import SCITEX_STYLE

            style = SCITEX_STYLE if isinstance(SCITEX_STYLE, dict) else None
        except Exception:
            style = None
    if not style:
        return
    try:
        from ..styles._internal import apply_style_mm

        apply_style_mm(mpl_ax, style)
    except Exception:
        pass


def replay_panel_suptitle(mpl_fig, source_record, left, bottom, width, height) -> None:
    """Replay a source panel's figure ``suptitle`` as panel-local text.

    Compose does not replay figure-level suptitles, yet the tight
    ``content_bbox`` reserved space for it -- leaving an empty band above the
    panel. Re-drawing the suptitle centred at the top of the panel rectangle
    fills that band and preserves the panel's identity (e.g. "Patient #10")
    instead of a gap. Best-effort; only safe text kwargs are forwarded.
    """
    sup = getattr(source_record, "suptitle", None)
    if not sup or not sup.get("text"):
        return
    src_kw = sup.get("kwargs") or {}
    kw = {
        k: src_kw[k]
        for k in ("fontsize", "fontweight", "color", "family")
        if k in src_kw
    }
    try:
        mpl_fig.text(
            left + width / 2.0,
            bottom + height,
            sup["text"],
            ha="center",
            va="top",
            **kw,
        )
    except Exception:
        pass


__all__ = ["panel_rel_bbox", "_apply_source_style", "replay_panel_suptitle"]

# EOF
