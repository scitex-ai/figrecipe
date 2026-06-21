#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for artist extraction + axes flattening on RecordingFigures."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.axes

import figrecipe.pyplot as fplt
from figrecipe._hitmap._artist_extraction import (
    _get_flat_axes,
    detect_logical_groups,
    get_all_artists,
    get_all_artists_with_groups,
)


def _line_figure():
    # An explicit matplotlib label makes the line "selectable" (unlabeled lines
    # get a "_"-prefixed label and are skipped as internal artists).
    fig, ax = fplt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6], label="series", id="line1")
    return fig


def test_get_flat_axes_returns_matplotlib_axes_for_recording_figure():
    # Arrange
    fig = _line_figure()
    # Act
    axes = _get_flat_axes(fig)
    # Assert
    assert all(isinstance(ax, matplotlib.axes.Axes) for ax in axes)
    fplt.close(fig)


def test_get_flat_axes_count_matches_subplot_grid():
    # Arrange
    fig, axes = fplt.subplots(2, 3)
    # Act
    flat = _get_flat_axes(fig)
    # Assert
    assert len(flat) == 6
    fplt.close(fig)


def test_get_all_artists_finds_plotted_line():
    # Arrange
    fig = _line_figure()
    # Act
    artists = get_all_artists(fig)
    # Assert
    assert len(artists) >= 1
    fplt.close(fig)


def test_get_all_artists_returns_triples():
    # Arrange
    fig = _line_figure()
    # Act
    artists = get_all_artists(fig)
    # Assert
    assert all(len(entry) == 3 for entry in artists)
    fplt.close(fig)


def test_get_all_artists_with_groups_returns_groups_dict():
    # Arrange
    fig = _line_figure()
    # Act
    artists, groups = get_all_artists_with_groups(fig)
    # Assert
    assert isinstance(groups, dict)
    fplt.close(fig)


def test_detect_logical_groups_returns_dict():
    # Arrange
    fig = _line_figure()
    # Act
    groups = detect_logical_groups(fig)
    # Assert
    assert isinstance(groups, dict)
    fplt.close(fig)


# EOF
