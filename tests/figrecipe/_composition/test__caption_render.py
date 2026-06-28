#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Composed-figure caption-band tests (operator-approved redesign).

A composed figure's FIGURE-LEVEL caption routes through the same additive
``add_figure_caption`` as single figures, so it must obey the same rule: the
composed figure GROWS by a caption band and the caption NEVER overlaps the
panels (or the per-panel ``(A)/(B)`` labels, which are re-placed against the
post-band panel positions).

AAA-structured (STX-TQ002), one assertion each (STX-TQ007), no mocks.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

_COMPOSED_CAPTION = (
    "Prospective seizure-vs-interictal prediction across an expanding, "
    "leakage-free training window, comparing the clinical-only model against "
    "the SLE-augmented model. Panel A shows the learning curve; panel B shows "
    "the matched sample-size growth. Bands are 95% bootstrap confidence "
    "intervals; faint traces are individual patients."
)


def _two_source_recipes(tmp_path):
    """Save two single-axes recipes and return their paths."""
    import figrecipe as fr

    paths = []
    for i in range(2):
        fig, ax = fr.subplots(1, 1, axes_width_mm=60, axes_height_mm=45)
        ax.plot([0, 1, 2, 3], [0, 1, 4, 9])
        recipe = tmp_path / f"src{i}.yaml"
        fr.save(fig, str(recipe), validate=False, verbose=False)
        mpl = fig._fig if hasattr(fig, "_fig") else fig
        plt.close(mpl)
        paths.append(str(recipe))
    return paths


def _rects_overlap(a, b):
    """True when two (x0, y0, x1, y1) rectangles overlap with positive area."""
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def test_composed_caption_never_overlaps_any_panel(tmp_path):
    # Arrange
    import figrecipe as fr

    r0, r1 = _two_source_recipes(tmp_path)
    fig, _axes = fr.compose(
        layout=(1, 2),
        sources={(0, 0): r0, (0, 1): r1},
        caption=_COMPOSED_CAPTION,
    )
    mpl_fig = fig._fig if hasattr(fig, "_fig") else fig
    mpl_fig.canvas.draw()
    renderer = mpl_fig.canvas.get_renderer()
    inv = mpl_fig.transFigure.inverted()
    axes_rects = [
        (
            ax.get_position().x0,
            ax.get_position().y0,
            ax.get_position().x1,
            ax.get_position().y1,
        )
        for ax in mpl_fig.axes
        if ax.get_visible()
    ]
    text_rects = [
        (
            ext.x0,
            ext.y0,
            ext.x1,
            ext.y1,
        )
        for t in mpl_fig.texts
        for ext in [t.get_window_extent(renderer).transformed(inv)]
    ]

    # Act
    any_overlap = any(_rects_overlap(tr, ar) for tr in text_rects for ar in axes_rects)

    # Assert
    assert not any_overlap
    plt.close(mpl_fig)


def test_composed_caption_grows_figure_height(tmp_path):
    # Arrange
    import figrecipe as fr

    r0, r1 = _two_source_recipes(tmp_path)
    plain, _a = fr.compose(layout=(1, 2), sources={(0, 0): r0, (0, 1): r1})
    plain_mpl = plain._fig if hasattr(plain, "_fig") else plain
    height_plain = plain_mpl.get_size_inches()[1]
    plt.close(plain_mpl)

    # Act
    captioned, _b = fr.compose(
        layout=(1, 2),
        sources={(0, 0): r0, (0, 1): r1},
        caption=_COMPOSED_CAPTION,
    )
    captioned_mpl = captioned._fig if hasattr(captioned, "_fig") else captioned
    height_captioned = captioned_mpl.get_size_inches()[1]

    # Assert
    assert height_captioned > height_plain
    plt.close(captioned_mpl)
