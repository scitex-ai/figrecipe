#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for ``scatter_labels`` decluttering against the figure background.

``scatter_labels`` repels labels off the data ink, which it finds by rasterizing
the figure. On a dark theme the raster used to classify the ENTIRE canvas as ink
(the background was assumed white), so no label could find a clear spot and every
one fell back onto its point -- decluttering degraded to nothing. These pin the
dark-theme path and the saturation guard that now refuses to fail quietly.
"""

import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

import figrecipe as fr  # noqa: E402

# Deliberately crowded: without decluttering these labels sit on top of one another.
_X = [1.0, 1.02, 1.04, 2.0, 2.02, 3.0, 3.01]
_Y = [1.0, 1.01, 1.03, 2.0, 2.01, 3.0, 3.02]
_LABELS = [f"P{i:02d}" for i in range(len(_X))]

_NO_CLEAR_SPOT = "no clear spot"
_SATURATED = "almost fully saturated"


def _label_a_dark_panel(facecolor="#1e1e1e"):
    """Label a crowded scatter on a dark panel; return the warnings raised."""
    fig, ax = fr.subplots(axes_width_mm=90, axes_height_mm=70)
    ax.scatter(_X, _Y)
    ax._ax.set_facecolor(facecolor)
    ax._ax.figure.set_facecolor(facecolor)
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            ax.scatter_labels(_X, _Y, _LABELS, declutter=True, avoid="ink")
        return [str(w.message) for w in caught]
    finally:
        plt.close(ax._ax.figure)


def test_dark_panel_labels_find_a_clear_spot():
    # Arrange: a dark figure, whose background the raster must recognise.
    facecolor = "#1e1e1e"
    # Act
    messages = _label_a_dark_panel(facecolor)
    # Assert: nothing fell back onto its point.
    assert not any(_NO_CLEAR_SPOT in m for m in messages)


def test_dark_panel_does_not_warn_about_saturation():
    # Arrange: a recognised dark background yields a mostly-empty raster.
    facecolor = "#1e1e1e"
    # Act
    messages = _label_a_dark_panel(facecolor)
    # Assert
    assert not any(_SATURATED in m for m in messages)


def test_saturated_ink_warns_instead_of_failing_quietly():
    # Arrange: a full-bleed image leaves genuinely no free space -- the solver
    # cannot help, and must SAY so rather than silently place nothing.
    fig, ax = fr.subplots(axes_width_mm=90, axes_height_mm=70)
    ax.imshow([[1, 2], [3, 4]])
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ax.scatter_labels([0, 1], [0, 1], ["A", "B"], declutter=True, avoid="ink")
    messages = [str(w.message) for w in caught]
    plt.close(ax._ax.figure)
    # Assert
    assert any(_SATURATED in m for m in messages)


def test_points_mode_skips_the_raster_entirely():
    # Arrange: avoid="points" is the documented escape hatch from the raster, so
    # it must never raise the saturation warning even on a full-bleed image.
    fig, ax = fr.subplots(axes_width_mm=90, axes_height_mm=70)
    ax.imshow([[1, 2], [3, 4]])
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ax.scatter_labels([0, 1], [0, 1], ["A", "B"], declutter=True, avoid="points")
    messages = [str(w.message) for w in caught]
    plt.close(ax._ax.figure)
    # Assert
    assert not any(_SATURATED in m for m in messages)


def test_mismatched_label_length_is_rejected():
    # Arrange
    fig, ax = fr.subplots(axes_width_mm=90, axes_height_mm=70)
    try:
        # Act
        # Assert
        with pytest.raises(ValueError, match="equal length"):
            ax.scatter_labels([0, 1], [0, 1], ["only-one"])
    finally:
        plt.close(ax._ax.figure)


# EOF
