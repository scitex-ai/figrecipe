#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for as_mpl_figure (RecordingFigure -> matplotlib Figure normalisation)."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.axes
import matplotlib.figure
import matplotlib.pyplot as plt

import figrecipe.pyplot as fplt
from figrecipe._hitmap._resolve import as_mpl_figure


def test_recording_figure_resolves_to_matplotlib_figure():
    # Arrange
    fig, ax = fplt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6], id="line1")
    # Act
    resolved = as_mpl_figure(fig)
    # Assert
    assert isinstance(resolved, matplotlib.figure.Figure)
    fplt.close(fig)


def test_raw_matplotlib_figure_returned_unchanged():
    # Arrange
    fig, ax = plt.subplots()
    # Act
    resolved = as_mpl_figure(fig)
    # Assert
    assert resolved is fig
    plt.close(fig)


def test_resolved_figure_exposes_flat_list_of_axes():
    # Arrange
    fig, axes = fplt.subplots(2, 2)
    # Act
    resolved = as_mpl_figure(fig)
    # Assert
    assert all(isinstance(ax, matplotlib.axes.Axes) for ax in resolved.axes)
    fplt.close(fig)


def test_resolved_multi_panel_figure_has_expected_axes_count():
    # Arrange
    fig, axes = fplt.subplots(2, 2)
    # Act
    resolved = as_mpl_figure(fig)
    # Assert
    assert len(resolved.axes) == 4
    fplt.close(fig)


# EOF
