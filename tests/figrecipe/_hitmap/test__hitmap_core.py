#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the core ID-color hitmap renderers."""

import matplotlib

matplotlib.use("Agg")

import numpy as np

import figrecipe.pyplot as fplt
from figrecipe._hitmap._hitmap_core import (
    generate_hitmap_id_colors,
    generate_hitmap_with_bbox_tight,
)


def _line_figure():
    fig, ax = fplt.subplots()
    ax.plot([1, 2, 3], [4, 5, 6], id="line1")
    return fig


def test_generate_hitmap_id_colors_returns_ndarray():
    # Arrange
    fig = _line_figure()
    # Act
    hitmap, _ = generate_hitmap_id_colors(fig, dpi=72)
    # Assert
    assert isinstance(hitmap, np.ndarray)
    fplt.close(fig)


def test_generate_hitmap_id_colors_array_is_two_dimensional():
    # Arrange
    fig = _line_figure()
    # Act
    hitmap, _ = generate_hitmap_id_colors(fig, dpi=72)
    # Assert
    assert hitmap.ndim == 2
    fplt.close(fig)


def test_generate_hitmap_id_colors_array_is_uint32():
    # Arrange
    fig = _line_figure()
    # Act
    hitmap, _ = generate_hitmap_id_colors(fig, dpi=72)
    # Assert
    assert hitmap.dtype == np.uint32
    fplt.close(fig)


def test_generate_hitmap_id_colors_returns_color_map():
    # Arrange
    fig = _line_figure()
    # Act
    _, color_map = generate_hitmap_id_colors(fig, dpi=72)
    # Assert
    assert isinstance(color_map, dict)
    fplt.close(fig)


def test_generate_hitmap_with_bbox_tight_returns_image_with_size():
    # Arrange
    fig = _line_figure()
    # Act
    img, _ = generate_hitmap_with_bbox_tight(fig, dpi=72)
    # Assert
    assert img.size[0] > 0 and img.size[1] > 0
    fplt.close(fig)


# EOF
