#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for client-side path/region geometry extraction."""

import matplotlib

matplotlib.use("Agg")

import figrecipe.pyplot as fplt
from figrecipe._hitmap._path_extraction import (
    extract_path_data,
    extract_selectable_regions,
)


def _line_figure():
    fig, ax = fplt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6], id="line1")
    return fig


def test_extract_path_data_includes_figure_section():
    # Arrange
    fig = _line_figure()
    # Act
    data = extract_path_data(fig)
    # Assert
    assert "figure" in data
    fplt.close(fig)


def test_extract_path_data_includes_axes_section():
    # Arrange
    fig = _line_figure()
    # Act
    data = extract_path_data(fig)
    # Assert
    assert "axes" in data
    fplt.close(fig)


def test_extract_path_data_axes_count_matches_figure():
    # Arrange
    fig, axes = fplt.subplots(1, 2)
    # Act
    data = extract_path_data(fig)
    # Assert
    assert len(data["axes"]) == 2
    fplt.close(fig)


def test_extract_path_data_includes_artists_section():
    # Arrange
    fig = _line_figure()
    # Act
    data = extract_path_data(fig)
    # Assert
    assert "artists" in data
    fplt.close(fig)


def test_extract_selectable_regions_returns_axes_key():
    # Arrange
    fig = _line_figure()
    # Act
    regions = extract_selectable_regions(fig)
    # Assert
    assert "axes" in regions
    fplt.close(fig)


# EOF
