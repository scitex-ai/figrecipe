#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Additive caption band helpers.

These pure, testable helpers implement the *additive* in-image caption: the
figure GROWS by a caption band whose height is reserved by extending the
figure canvas, while the axes keep their EXACT mm size and position
(identical to the no-caption figure). The band is NEVER created by shrinking
the axes.

The flow (driven from ``_public.add_figure_caption``):

1. ``resolve_caption_font_pt``  -> caption font size in points.
2. ``wrap_caption_lines``       -> wrapped lines (>= 1, never empty).
3. ``caption_band_inches``      -> band height in inches.
4. ``extend_figure_for_caption`` -> grow the figure + rewrite subplotpars so
   the axes stay put; mirror the new geometry into ``record`` so it
   round-trips through save -> reproduce.
5. ``place_caption``            -> draw the caption text into the new band and
   append every drawn fragment to ``record.figure_texts`` (so the reproducer,
   which replays ``figure_texts`` verbatim, recreates it pixel-for-pixel —
   including justified word fragments).
"""

from typing import Any, Dict, List

from .._utils._units import inch_to_mm, mm_to_inch

__all__ = [
    "resolve_caption_font_pt",
    "wrap_caption_lines",
    "caption_band_inches",
    "extend_figure_for_caption",
    "place_caption",
]

# Matplotlib's relative font-size names scale off rcParams["font.size"].
# The factors below are matplotlib's standard relative scale (FontManager),
# expressed as the resulting points at the default base size of 10.0.
_RELATIVE_FONT_PT = {
    "xx-small": 5.79,
    "x-small": 6.94,
    "small": 8.33,
    "medium": 10.0,
    "large": 12.0,
    "x-large": 14.4,
    "xx-large": 17.28,
}

# Line-height multiple (caption line pitch = font_pt * this / 72 inch).
_LINE_HEIGHT = 1.35

# Caption white round bbox (kept identical to the historical look).
_CAPTION_BBOX = dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.8)


def resolve_caption_font_pt(font_size: Any, mpl_fig: Any) -> float:
    """Resolve a caption font size to absolute points.

    int -> used directly. Relative names ({"xx-small"..."xx-large"}) scale off
    ``matplotlib.rcParams["font.size"]`` (the table is expressed at base 10, so
    we rescale by base/10). Anything else is tried as ``float``; on failure we
    fall back to "small" (8.33pt).
    """
    if isinstance(font_size, bool):  # bool is an int subclass — reject early
        return _RELATIVE_FONT_PT["small"]
    if isinstance(font_size, int):
        return float(font_size)
    if isinstance(font_size, str):
        key = font_size.strip().lower()
        if key in _RELATIVE_FONT_PT:
            import matplotlib

            base = float(matplotlib.rcParams.get("font.size", 10.0))
            return _RELATIVE_FONT_PT[key] * base / 10.0
        try:
            return float(font_size)
        except (TypeError, ValueError):
            return _RELATIVE_FONT_PT["small"]
    try:
        return float(font_size)
    except (TypeError, ValueError):
        return _RELATIVE_FONT_PT["small"]


def wrap_caption_lines(text: str, wrap_width: int) -> List[str]:
    """Wrap caption text into lines via ``textwrap.wrap`` (>= 1 line)."""
    import textwrap

    lines = textwrap.wrap(text, width=max(1, int(wrap_width)))
    if not lines:
        # textwrap.wrap("") returns [] — never let the band collapse to 0 lines.
        return [text]
    return lines


def caption_band_inches(n_lines: int, font_pt: float, pad_mm: float) -> float:
    """Caption band height in inches for ``n_lines`` lines.

    Height = text block (n_lines * line pitch) + a ``pad_mm`` gap on BOTH the
    axes-facing side and the figure-edge-facing side.
    """
    text_in = max(1, int(n_lines)) * (font_pt * _LINE_HEIGHT / 72.0)
    return text_in + 2.0 * mm_to_inch(pad_mm)


def extend_figure_for_caption(
    mpl_fig: Any,
    record: Any,
    band_in: float,
    position: str,
) -> Dict[str, float]:
    """Grow the figure by ``band_in`` inches, keeping the axes mm-fixed.

    This is layout-engine-agnostic. figrecipe's SCITEX figures run a
    ConstrainedLayoutEngine, which OWNS the axes rectangle and silently ignores
    ``subplots_adjust`` — so naively renormalising subplotpars lets the engine
    re-expand the axes into the new canvas (axes size would change). Instead we:

      1. draw once so the live geometry is the engine's solved fixed point;
      2. snapshot every axes' ABSOLUTE position in inches;
      3. grow the canvas by ``band_in`` (band on the bottom or top);
      4. DETACH the layout engine and pin each axes back to its snapshot inch
         rect (shifted up by ``band_in`` for a bottom band) — so the axes keep
         their EXACT mm size/position regardless of the engine;
      5. mirror the resolved geometry into ``record`` (figsize + subplotpars +
         ``constrained_layout=False``) so save -> reproduce recreates the SAME
         pinned canvas via the non-constrained subplots_adjust path.

    Returns the resolved subplotpars dict.
    """
    # 1) Settle the engine so snapshots are the converged geometry. A single
    # draw leaves constrained_layout part-way (it solves iteratively), which
    # would make the snapshot — and therefore the pinned axes size — depend on
    # draw count. Settling makes the axes rect a pure function of the content.
    try:
        from .._api._save_layout import settle_constrained_layout

        settle_constrained_layout(mpl_fig)
    except Exception:
        mpl_fig.canvas.draw()

    w_in, h_in = mpl_fig.get_size_inches()
    new_h = h_in + band_in

    axes = [ax for ax in mpl_fig.axes if ax.get_visible()]
    # Snapshot absolute axes rects in INCHES (figure-fraction * size).
    snapshots = []
    for ax in axes:
        pos = ax.get_position()
        snapshots.append(
            (
                ax,
                pos.x0 * w_in,
                pos.y0 * h_in,
                pos.width * w_in,
                pos.height * h_in,
            )
        )

    y_shift_in = band_in if position != "top" else 0.0

    # 3) Grow the canvas, then 4) detach the engine and re-pin in new fractions.
    mpl_fig.set_size_inches(w_in, new_h)
    try:
        mpl_fig.set_layout_engine("none")
    except Exception:
        # Older matplotlib: clear constrained_layout the legacy way.
        try:
            mpl_fig.set_constrained_layout(False)
        except Exception:
            pass

    for ax, x0_in, y0_in, w0_in, h0_in in snapshots:
        ax.set_position(
            [
                x0_in / w_in,
                (y0_in + y_shift_in) / new_h,
                w0_in / w_in,
                h0_in / new_h,
            ]
        )

    # Resolved uniform subplotpars (for record.layout / reproduce). Derived from
    # the bounding rect of all pinned axes so the non-constrained reproduce path
    # lands them in the same place.
    xs0 = min(s[1] for s in snapshots) / w_in
    xs1 = max(s[1] + s[3] for s in snapshots) / w_in
    ys0 = (min(s[2] for s in snapshots) + y_shift_in) / new_h
    ys1 = (max(s[2] + s[4] for s in snapshots) + y_shift_in) / new_h
    sp = mpl_fig.subplotpars
    new_layout = {
        "left": float(xs0),
        "right": float(xs1),
        "bottom": float(ys0),
        "top": float(ys1),
        "wspace": float(sp.wspace),
        "hspace": float(sp.hspace),
    }

    # 5) Mirror into the record so save -> reproduce recreates the same canvas.
    if hasattr(record, "figsize"):
        record.figsize = (float(w_in), float(new_h))
    if hasattr(record, "layout"):
        record.layout = dict(new_layout)
    # The figure no longer runs constrained_layout (we pinned the axes), so the
    # reproducer must use the subplots_adjust path, not re-solve the engine.
    if hasattr(record, "constrained_layout"):
        record.constrained_layout = False

    # Keep mm_layout's reserved strip in sync so auto-crop does NOT crop the
    # band away. The mm_layout has no single "height" key; the figure height in
    # mm is margin_bottom_mm + nrows*axes_height_mm + (nrows-1)*space_h_mm +
    # margin_top_mm. We therefore grow the band-side INTERNAL margin by the band
    # height in mm, which both (a) enlarges the reserved canvas the crop keeps
    # and (b) matches where the band physically lives.
    mm_layout = getattr(record, "mm_layout", None)
    if isinstance(mm_layout, dict):
        band_mm = inch_to_mm(band_in)
        if position == "top" and "margin_top_mm" in mm_layout:
            mm_layout["margin_top_mm"] = mm_layout["margin_top_mm"] + band_mm
        elif "margin_bottom_mm" in mm_layout:
            mm_layout["margin_bottom_mm"] = mm_layout["margin_bottom_mm"] + band_mm

    return new_layout


def _record_text(record: Any, x: float, y: float, s: str, kwargs: Dict[str, Any]):
    """Append a drawn fragment to ``record.figure_texts`` for verbatim replay."""
    if hasattr(record, "figure_texts"):
        record.figure_texts.append(
            {"x": float(x), "y": float(y), "s": s, "kwargs": dict(kwargs)}
        )


def place_caption(
    mpl_fig: Any,
    record: Any,
    lines: List[str],
    font_pt: float,
    position: str,
    align: str,
    band_in: float,
    width_ratio: float,
) -> None:
    """Draw the caption into the reserved band and record every fragment.

    ``align`` in {"left", "center"} draws a single multi-line text. ``align``
    == "justify" (default) draws each non-last line word-by-word with the
    inter-word slack distributed evenly so the line spans the full content
    width; the LAST line is left-aligned. Every drawn ``mpl_fig.text`` is also
    appended to ``record.figure_texts`` so the reproducer recreates it exactly.
    """
    w_in, new_h = mpl_fig.get_size_inches()
    band_frac = band_in / new_h

    # Content x-extent = axes bounding rect (matches the pinned axes the band
    # sits under). ``record.layout`` holds the resolved left/right after extend;
    # fall back to live subplotpars for a bare Figure.
    layout = getattr(record, "layout", None)
    if isinstance(layout, dict) and "left" in layout and "right" in layout:
        left_margin = float(layout["left"])
        right_margin = float(layout["right"])
    else:
        left_margin = float(mpl_fig.subplotpars.left)
        right_margin = float(mpl_fig.subplotpars.right)

    if position == "top":
        y_center = 1.0 - band_frac / 2.0
    else:
        y_center = band_frac / 2.0

    fontsize = font_pt

    if align in ("left", "center"):
        if align == "center":
            x = 0.5
            ha = "center"
        else:
            x = left_margin
            ha = "left"
        kwargs = {
            "ha": ha,
            "va": "center",
            "fontsize": fontsize,
            "bbox": dict(_CAPTION_BBOX),
        }
        mpl_fig.text(x, y_center, "\n".join(lines), **kwargs)
        _record_text(record, x, y_center, "\n".join(lines), kwargs)
        return

    # align == "justify": full-width lines, last line left-aligned.
    mpl_fig.canvas.draw()
    renderer = mpl_fig.canvas.get_renderer()
    dpi = mpl_fig.dpi

    line_pitch_in = font_pt * _LINE_HEIGHT / 72.0
    line_pitch_frac = line_pitch_in / new_h
    n = len(lines)
    # Stack lines vertically, centred on the band centre.
    top_y = y_center + (n - 1) / 2.0 * line_pitch_frac

    content_left = left_margin
    content_right = right_margin

    for i, line in enumerate(lines):
        y = top_y - i * line_pitch_frac
        words = line.split()
        is_last = i == n - 1
        if is_last or len(words) <= 1:
            # Left-aligned (last line, or a single-word line cannot justify).
            kwargs = {
                "ha": "left",
                "va": "center",
                "fontsize": fontsize,
            }
            mpl_fig.text(content_left, y, line, **kwargs)
            _record_text(record, content_left, y, line, kwargs)
            continue

        # Measure each word's width as a figure fraction.
        word_fracs: List[float] = []
        for word in words:
            t = mpl_fig.text(0, 0, word, fontsize=fontsize)
            ext = t.get_window_extent(renderer)
            t.remove()
            word_fracs.append(ext.width / (dpi * w_in))

        total_words = sum(word_fracs)
        gaps = len(words) - 1
        span = content_right - content_left
        slack = span - total_words
        gap = slack / gaps if gaps > 0 else 0.0

        x = content_left
        for j, word in enumerate(words):
            kwargs = {
                "ha": "left",
                "va": "center",
                "fontsize": fontsize,
            }
            mpl_fig.text(x, y, word, **kwargs)
            _record_text(record, x, y, word, kwargs)
            x += word_fracs[j] + gap
