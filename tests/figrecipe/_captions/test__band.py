#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Additive caption-band tests (operator-approved redesign).

``fr.add_figure_caption(fig, caption, position="bottom")`` must be ADDITIVE:
the figure GROWS by a caption band, the axes keep their EXACT mm size and
position, and the caption NEVER overlaps the axes. The default ``align`` is
"justify" (full-width lines, last line left-aligned), which records each word
fragment separately so the band reproduces verbatim through save -> reproduce.

Tests are AAA-structured (STX-TQ002) with one assertion each (STX-TQ007), one
behaviour per test, no mocks/monkeypatch (STX-TQ rules).
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

# A multi-line scientific caption that reproduces the neurovista overlap bug.
_NEUROVISTA_CAPTION = (
    "Prospective Sz-vs-IC prediction (Bayesian logistic, leakage-free "
    "expanding window; test = clinical Sz vs time-matched IC only). x = "
    "number of clinical seizures in training. Gray = clinical only; crimson "
    "= SLE added to training only. Bands = 95% bootstrap CI; faint = "
    "patients; in-plot counts = median training sizes."
)


def _neurovista_fig():
    """Build the neurovista repro figure with a bottom caption.

    Returns (fig, mpl_fig, mpl_ax).
    """
    import figrecipe as fr

    fr.load_style("SCITEX", background="white")
    fig, ax = fr.subplots(1, 1, axes_width_mm=120, axes_height_mm=68)
    raw = ax._ax if hasattr(ax, "_ax") else ax
    raw.plot(
        [0, 1, 2, 3, 4, 5],
        [0.59, 0.66, 0.65, 0.66, 0.71, 0.80],
        marker="o",
        label="x",
    )
    raw.set_xlabel("number of clinical seizures n in training")
    raw.set_ylabel("prospective AUC")
    raw.legend(frameon=False)
    fr.add_figure_caption(fig, _NEUROVISTA_CAPTION, position="bottom")
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
    return fig, mpl_fig, raw


def test_caption_band_never_overlaps_axes():
    # Arrange
    _fig, mpl_fig, raw_ax = _neurovista_fig()
    mpl_fig.canvas.draw()
    renderer = mpl_fig.canvas.get_renderer()
    inv = mpl_fig.transFigure.inverted()
    caption_top = max(
        t.get_window_extent(renderer).transformed(inv).y1 for t in mpl_fig.texts
    )
    axes_bottom = raw_ax.get_position().y0

    # Act
    no_overlap = caption_top <= axes_bottom + 1e-9

    # Assert
    assert no_overlap
    plt.close(mpl_fig)


def test_caption_is_additive_grows_figure_height():
    # Arrange
    import figrecipe as fr

    fr.load_style("SCITEX", background="white")
    fig, ax = fr.subplots(1, 1, axes_width_mm=120, axes_height_mm=68)
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
    height_before = mpl_fig.get_size_inches()[1]

    # Act
    fr.add_figure_caption(fig, _NEUROVISTA_CAPTION, position="bottom")
    height_after = mpl_fig.get_size_inches()[1]

    # Assert
    assert height_after > height_before
    plt.close(mpl_fig)


def test_caption_preserves_axes_size_in_inches():
    # Arrange
    import figrecipe as fr
    from figrecipe._api._save_layout import settle_constrained_layout

    fr.load_style("SCITEX", background="white")
    fig, ax = fr.subplots(1, 1, axes_width_mm=120, axes_height_mm=68)
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
    raw = ax._ax if hasattr(ax, "_ax") else ax
    # Settle the layout engine so the axes rect is its converged fixed point
    # (the no-caption baseline); the additive band must leave THIS rect intact.
    settle_constrained_layout(mpl_fig)
    w0, h0 = mpl_fig.get_size_inches()
    pos0 = raw.get_position()
    ax_w_in_before = pos0.width * w0
    ax_h_in_before = pos0.height * h0

    # Act
    fr.add_figure_caption(fig, _NEUROVISTA_CAPTION, position="bottom")
    mpl_fig.canvas.draw()
    w1, h1 = mpl_fig.get_size_inches()
    pos1 = raw.get_position()
    ax_size_in_after = (pos1.width * w1, pos1.height * h1)

    # Assert
    assert ax_size_in_after == pytest.approx((ax_w_in_before, ax_h_in_before), abs=1e-6)
    plt.close(mpl_fig)


def test_justify_default_records_word_fragments():
    # Arrange
    import figrecipe as fr

    fr.load_style("SCITEX", background="white")
    fig, ax = fr.subplots(1, 1, axes_width_mm=120, axes_height_mm=68)

    # Act
    fr.add_figure_caption(fig, _NEUROVISTA_CAPTION, position="bottom")
    n_recorded = len(fig.record.figure_texts)

    # Assert: justify splits non-last lines into separate word fragments.
    assert n_recorded > 1
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
    plt.close(mpl_fig)


def test_caption_band_round_trips_figsize(tmp_path):
    # Arrange
    import figrecipe as fr

    fr.load_style("SCITEX", background="white")
    fig, ax = fr.subplots(1, 1, axes_width_mm=120, axes_height_mm=68)
    raw = ax._ax if hasattr(ax, "_ax") else ax
    raw.plot([0, 1, 2], [0, 1, 2])
    fr.add_figure_caption(fig, _NEUROVISTA_CAPTION, position="bottom")
    recorded_figsize = tuple(fig.record.figsize)
    recipe = tmp_path / "fig.png"
    fr.save(fig, str(recipe), verbose=False, validate=False)

    # Act
    rfig, _rax = fr.reproduce(str(recipe))
    reproduced_mpl = rfig._fig if hasattr(rfig, "_fig") else rfig
    reproduced_figsize = tuple(reproduced_mpl.get_size_inches())

    # Assert
    assert reproduced_figsize == pytest.approx(recorded_figsize, abs=1e-6)
    plt.close(reproduced_mpl)


def test_justify_left_aligns_sparse_lines_on_wide_figure():
    # Arrange
    import figrecipe as fr
    from figrecipe._captions._band import wrap_caption_lines

    fr.load_style("SCITEX", background="white")
    fig, ax = fr.subplots(1, 1, axes_width_mm=180, axes_height_mm=60)
    n_lines = len(wrap_caption_lines(_NEUROVISTA_CAPTION, 30))

    # Act: narrow char-wrap on a wide figure -> every line is physically sparse,
    # so the justify cap left-aligns them all (one recorded text per line, never
    # split into stretched word fragments).
    fr.add_figure_caption(
        fig, _NEUROVISTA_CAPTION, position="bottom", align="justify", wrap_width=30
    )
    n_recorded = len(fig.record.figure_texts)

    # Assert
    assert n_recorded == n_lines
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
    plt.close(mpl_fig)


def test_align_center_records_a_centered_text():
    # Arrange
    import figrecipe as fr

    fr.load_style("SCITEX", background="white")
    fig, ax = fr.subplots(1, 1, axes_width_mm=120, axes_height_mm=68)

    # Act
    fr.add_figure_caption(fig, _NEUROVISTA_CAPTION, position="bottom", align="center")
    has_centered = any(
        t.get("kwargs", {}).get("ha") == "center" for t in fig.record.figure_texts
    )

    # Assert
    assert has_centered
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
    plt.close(mpl_fig)


def test_align_left_records_only_left_text():
    # Arrange
    import figrecipe as fr

    fr.load_style("SCITEX", background="white")
    fig, ax = fr.subplots(1, 1, axes_width_mm=120, axes_height_mm=68)

    # Act
    fr.add_figure_caption(fig, _NEUROVISTA_CAPTION, position="bottom", align="left")
    only_left = all(
        t.get("kwargs", {}).get("ha") == "left" for t in fig.record.figure_texts
    )

    # Assert
    assert only_left
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
    plt.close(mpl_fig)


def test_top_position_places_caption_in_upper_band():
    # Arrange
    import figrecipe as fr

    fr.load_style("SCITEX", background="white")
    fig, ax = fr.subplots(1, 1, axes_width_mm=120, axes_height_mm=68)

    # Act
    fr.add_figure_caption(fig, _NEUROVISTA_CAPTION, position="top", align="left")
    min_caption_y = min((t["y"] for t in fig.record.figure_texts), default=0.0)

    # Assert
    assert min_caption_y > 0.5
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
    plt.close(mpl_fig)
