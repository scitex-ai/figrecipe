#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for caption-overlap bugs (PR #162 follow-up).

The first iteration of ``fr.subplots(caption=...)`` / ``fr.compose(caption=...)``
shipped three layered bugs:

  1) DOUBLE-RENDER: ``add_figure_caption`` drew the caption twice — once
     directly via ``mpl_fig.text(...)`` and once via
     ``caption_manager.add_figure_caption(...)``. Two ``fig.texts``
     entries stacked at the same y-anchor and overlapped each other.
  2) PANEL OVERLAP: ``mpl_fig.subplots_adjust(bottom=0.15)`` failed to
     move the bottom-row panels on mm-laid figures (the paper-figure
     default), so the caption text at y=0.02 landed on top of panels
     whose ``y0`` was still ≈0.05.
  3) MARKDOWN LEAKAGE: ``caption_manager`` rendered the formatted caption
     with raw ``**Figure N.**`` markers, which matplotlib renders
     literally as four asterisks rather than as bold text.

Tests are AAA-structured (STX-TQ002) with one assertion each
(STX-TQ007), one behaviour per test.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest


def _bbox_intersects(text_bbox, axes_bbox) -> bool:
    """Return True iff two figure-fraction Bboxes overlap."""
    return not (
        text_bbox.x1 <= axes_bbox.x0
        or axes_bbox.x1 <= text_bbox.x0
        or text_bbox.y1 <= axes_bbox.y0
        or axes_bbox.y1 <= text_bbox.y0
    )


def _text_bbox_in_fig_frac(mpl_fig, txt_artist):
    """Return text's bounding box in figure-fraction coords."""
    mpl_fig.canvas.draw()
    bb = txt_artist.get_window_extent(renderer=mpl_fig.canvas.get_renderer())
    return bb.transformed(mpl_fig.transFigure.inverted())


@pytest.fixture
def fig_with_long_caption():
    """A 2x2 fr.subplots with a long caption + one line per panel.

    Yields (mpl_fig, mpl_axes_list). Closes the figure on teardown.
    """
    import figrecipe as fr

    fig, axes = fr.subplots(
        nrows=2,
        ncols=2,
        figsize=(7, 5),
        caption=(
            "Figure Y. Long-ish caption that tests whether a multi-line "
            "wrapped caption with bbox can overlap the bottom row of panels "
            "in a small figure. PAC z-score comparison; n=15 patients."
        ),
    )
    axes_flat = np.asarray(axes).flatten().tolist()
    for i, ax in enumerate(axes_flat):
        raw = ax._ax if hasattr(ax, "_ax") else ax
        raw.plot(np.linspace(0, 1, 50), np.sin(np.linspace(0, 6, 50) + i))
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
    mpl_axes = [ax._ax if hasattr(ax, "_ax") else ax for ax in axes_flat]
    yield mpl_fig, mpl_axes
    plt.close(mpl_fig)


def test_caption_renders_exactly_one_figure_text():
    """Bug 1: caption must not be rendered twice on the same figure."""
    # Arrange
    import figrecipe as fr

    fig, _axes = fr.subplots(
        nrows=2,
        ncols=2,
        figsize=(7, 5),
        caption="Figure X. Single caption rendered exactly once.",
    )
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig

    # Act
    n_texts = len(mpl_fig.texts)

    # Assert
    assert n_texts == 1, (
        f"expected exactly 1 figure-level text artist, got {n_texts}: "
        f"{[t.get_text()[:40] for t in mpl_fig.texts]}"
    )
    plt.close(mpl_fig)


def test_caption_bbox_does_not_overlap_top_left_panel(fig_with_long_caption):
    """Bug 2: caption must not overlap top-left panel (axes index 0)."""
    # Arrange
    mpl_fig, mpl_axes = fig_with_long_caption

    # Act
    tbb = _text_bbox_in_fig_frac(mpl_fig, mpl_fig.texts[0])
    abb = mpl_axes[0].get_position()

    # Assert
    assert not _bbox_intersects(tbb, abb), (
        f"caption y=[{tbb.y0:.3f}..{tbb.y1:.3f}] overlaps "
        f"axes[0] y=[{abb.y0:.3f}..{abb.y1:.3f}]"
    )


def test_caption_bbox_does_not_overlap_top_right_panel(fig_with_long_caption):
    """Bug 2: caption must not overlap top-right panel (axes index 1)."""
    # Arrange
    mpl_fig, mpl_axes = fig_with_long_caption

    # Act
    tbb = _text_bbox_in_fig_frac(mpl_fig, mpl_fig.texts[0])
    abb = mpl_axes[1].get_position()

    # Assert
    assert not _bbox_intersects(tbb, abb), (
        f"caption y=[{tbb.y0:.3f}..{tbb.y1:.3f}] overlaps "
        f"axes[1] y=[{abb.y0:.3f}..{abb.y1:.3f}]"
    )


def test_caption_bbox_does_not_overlap_bottom_left_panel(
    fig_with_long_caption,
):
    """Bug 2 (the originally-failing case): caption must not overlap
    bottom-left panel (axes index 2). This is where the pre-fix bug
    landed — bottom-row axes y0≈0.04, caption y=0.02..0.08.
    """
    # Arrange
    mpl_fig, mpl_axes = fig_with_long_caption

    # Act
    tbb = _text_bbox_in_fig_frac(mpl_fig, mpl_fig.texts[0])
    abb = mpl_axes[2].get_position()

    # Assert
    assert not _bbox_intersects(tbb, abb), (
        f"caption y=[{tbb.y0:.3f}..{tbb.y1:.3f}] overlaps "
        f"axes[2] (bottom-left) y=[{abb.y0:.3f}..{abb.y1:.3f}]"
    )


def test_caption_bbox_does_not_overlap_bottom_right_panel(
    fig_with_long_caption,
):
    """Bug 2 (the originally-failing case): caption must not overlap
    bottom-right panel (axes index 3).
    """
    # Arrange
    mpl_fig, mpl_axes = fig_with_long_caption

    # Act
    tbb = _text_bbox_in_fig_frac(mpl_fig, mpl_fig.texts[0])
    abb = mpl_axes[3].get_position()

    # Assert
    assert not _bbox_intersects(tbb, abb), (
        f"caption y=[{tbb.y0:.3f}..{tbb.y1:.3f}] overlaps "
        f"axes[3] (bottom-right) y=[{abb.y0:.3f}..{abb.y1:.3f}]"
    )


def test_rendered_caption_strips_double_asterisks():
    """Bug 3: ``**`` bold markers must not appear in rendered caption."""
    # Arrange
    import figrecipe as fr

    fig, _axes = fr.subplots(
        nrows=2,
        ncols=2,
        figsize=(7, 5),
        caption="Figure Z. Caption with **bold** markers.",
    )
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig

    # Act
    rendered = mpl_fig.texts[0].get_text()

    # Assert
    assert (
        "**" not in rendered
    ), f"raw '**' markdown leaked into rendered caption: {rendered!r}"
    plt.close(mpl_fig)


def test_rendered_caption_strips_single_asterisks():
    """Bug 3: single-``*`` italic markers must not appear in rendered caption."""
    # Arrange
    import figrecipe as fr

    fig, _axes = fr.subplots(
        nrows=2,
        ncols=2,
        figsize=(7, 5),
        caption="Figure Z. Caption with *italic* markers.",
    )
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig

    # Act
    rendered = mpl_fig.texts[0].get_text()

    # Assert
    assert (
        "*" not in rendered
    ), f"raw '*' markdown leaked into rendered caption: {rendered!r}"
    plt.close(mpl_fig)


def test_caption_manager_does_not_render_when_render_false():
    """``caption_manager.add_figure_caption(render=False)`` must not draw."""
    # Arrange
    import matplotlib.pyplot as _plt

    from figrecipe._captions._caption import ScientificCaption

    mgr = ScientificCaption()
    fig, _ax = _plt.subplots()
    n_before = len(fig.texts)

    # Act
    mgr.add_figure_caption(fig, "Test caption — should not draw.", render=False)

    # Assert
    assert len(fig.texts) == n_before, (
        f"render=False must not add any fig.text; "
        f"texts grew from {n_before} to {len(fig.texts)}"
    )
    _plt.close(fig)


def test_caption_manager_renders_by_default():
    """``caption_manager.add_figure_caption`` (default render=True) DOES draw."""
    # Arrange
    import matplotlib.pyplot as _plt

    from figrecipe._captions._caption import ScientificCaption

    mgr = ScientificCaption()
    fig, _ax = _plt.subplots()
    n_before = len(fig.texts)

    # Act
    mgr.add_figure_caption(fig, "Test caption — should draw exactly one.")

    # Assert
    assert len(fig.texts) == n_before + 1, (
        f"default render=True must add exactly one fig.text; "
        f"texts grew from {n_before} to {len(fig.texts)}"
    )
    _plt.close(fig)
