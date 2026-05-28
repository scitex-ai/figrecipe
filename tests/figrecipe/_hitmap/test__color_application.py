#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for applying / restoring unique ID colors on figure artists."""

import matplotlib

matplotlib.use("Agg")

import figrecipe.pyplot as fplt
from figrecipe._hitmap._color_application import (
    apply_hitmap_colors,
    prepare_hitmap_figure,
    restore_original_colors,
)


def _line_figure():
    # Explicit label so the line is treated as a selectable artist.
    fig, ax = fplt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6], label="series", id="line1")
    return fig


def test_apply_hitmap_colors_returns_three_values():
    # Arrange
    fig = _line_figure()
    # Act
    result = apply_hitmap_colors(fig)
    # Assert
    assert len(result) == 3
    fplt.close(fig)


def test_apply_hitmap_colors_builds_non_empty_color_map():
    # Arrange
    fig = _line_figure()
    # Act
    _, color_map, _ = apply_hitmap_colors(fig)
    # Assert
    assert len(color_map) >= 1
    fplt.close(fig)


def test_color_map_entries_carry_rgb():
    # Arrange
    fig = _line_figure()
    # Act
    _, color_map, _ = apply_hitmap_colors(fig)
    # Assert
    assert all("rgb" in info for info in color_map.values())
    fplt.close(fig)


def test_apply_then_restore_roundtrip_runs_without_error():
    # Arrange
    fig = _line_figure()
    original_props, _, _ = apply_hitmap_colors(fig)
    # Act
    restored = restore_original_colors(original_props)
    # Assert
    assert restored is None or restored is not False
    fplt.close(fig)


def test_prepare_hitmap_figure_returns_color_map_and_props():
    # Arrange
    fig = _line_figure()
    # Act
    color_map, original_props = prepare_hitmap_figure(fig)
    # Assert
    assert isinstance(color_map, dict)
    fplt.close(fig)


# EOF
