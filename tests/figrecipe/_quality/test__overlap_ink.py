#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the data-ink raster's background resolution.

The ink mask calls a pixel "ink" when it differs from the BACKGROUND, so
misreading the background poisons the whole mask. A caller with no style dict
(the declutter solver) used to fall straight through to white, which made every
pixel of a dark-theme figure read as ink: the mask saturated to 100%, the label
solver found no free space anywhere, and decluttering silently did nothing.
These pin the background down to the figure itself.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

from figrecipe._quality._overlap_ink import (  # noqa: E402
    _parse_bg_color,
    _render_ink_mask,
)

# A near-empty panel: a handful of markers cover a tiny sliver of the canvas, so
# a correctly-resolved background leaves the mask overwhelmingly EMPTY.
_SPARSE_INK = 0.30


@pytest.fixture
def dark_figure():
    fig, ax = plt.subplots()
    fig.set_facecolor("#1e1e1e")  # figrecipe's own dark theme figure_bg
    ax.set_facecolor("#1e1e1e")
    ax.plot([0, 1, 2], [0, 1, 0])
    yield fig
    plt.close(fig)


def test_dark_figure_does_not_saturate_the_ink_mask(dark_figure):
    # Arrange: no style dict -- the case the declutter solver actually hits.
    # Act
    ink, _height = _render_ink_mask(dark_figure, None)
    # Assert: the panel is mostly empty, not wall-to-wall ink.
    assert float(ink.mean()) < _SPARSE_INK


def test_figure_facecolor_resolves_background_without_a_style(dark_figure):
    # Arrange: style declares nothing, so the figure is the only ground truth.
    # Act
    rgb = _parse_bg_color(None, dark_figure)
    # Assert
    assert rgb == (30, 30, 30)


def test_declared_style_beats_the_figure_facecolor(dark_figure):
    # Arrange: an explicit theme color is a deliberate statement; honour it over
    # whatever the figure happens to be painted.
    style = {"theme_colors": {"axes_bg": "#252526"}}
    # Act
    rgb = _parse_bg_color(style, dark_figure)
    # Assert
    assert rgb == (37, 37, 38)


def test_transparent_figure_face_falls_back_to_white():
    # Arrange: a transparent face still rasterizes onto a WHITE canvas, so
    # reporting its (0,0,0,0) as black would invert the whole mask.
    fig = plt.figure()
    fig.patch.set_alpha(0.0)
    try:
        # Act
        rgb = _parse_bg_color(None, fig)
    finally:
        plt.close(fig)
    # Assert
    assert rgb == (255, 255, 255)


def test_light_figure_background_still_resolves_white():
    # Arrange: the default path must not regress.
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    try:
        # Act
        rgb = _parse_bg_color(None, fig)
    finally:
        plt.close(fig)
    # Assert
    assert rgb == (255, 255, 255)


# EOF
