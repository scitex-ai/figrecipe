#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for hitmap neighborhood queries and PNG persistence."""

import matplotlib

matplotlib.use("Agg")

import numpy as np

from figrecipe._hitmap._query import query_hitmap_neighborhood, save_hitmap_png


def test_query_returns_element_within_radius():
    # Arrange
    hitmap = np.zeros((10, 10), dtype=np.uint32)
    hitmap[5, 5] = 42
    color_map = {42: {"type": "line"}}
    # Act
    found = query_hitmap_neighborhood(hitmap, x=5, y=5, color_map=color_map, radius=1)
    # Assert
    assert color_map[42] in found


def test_query_empty_neighborhood_returns_empty_list():
    # Arrange
    hitmap = np.zeros((10, 10), dtype=np.uint32)
    color_map = {42: {"type": "line"}}
    # Act
    found = query_hitmap_neighborhood(hitmap, x=2, y=2, color_map=color_map, radius=1)
    # Assert
    assert found == []


def test_query_ignores_ids_absent_from_color_map():
    # Arrange
    hitmap = np.zeros((10, 10), dtype=np.uint32)
    hitmap[3, 3] = 99
    color_map = {42: {"type": "line"}}
    # Act
    found = query_hitmap_neighborhood(hitmap, x=3, y=3, color_map=color_map, radius=1)
    # Assert
    assert found == []


def test_save_hitmap_png_writes_file(tmp_path):
    # Arrange
    hitmap = np.zeros((4, 4), dtype=np.uint32)
    hitmap[1, 1] = 0x010203
    out = tmp_path / "hm.png"
    # Act
    save_hitmap_png(hitmap, str(out))
    # Assert
    assert out.exists()


def test_save_hitmap_png_roundtrips_id_via_rgb(tmp_path):
    # Arrange
    hitmap = np.zeros((4, 4), dtype=np.uint32)
    hitmap[1, 1] = 0x010203
    out = tmp_path / "hm.png"
    save_hitmap_png(hitmap, str(out))
    # Act
    from PIL import Image

    arr = np.asarray(Image.open(out))
    recovered = (int(arr[1, 1, 0]) << 16) | (int(arr[1, 1, 1]) << 8) | int(arr[1, 1, 2])
    # Assert
    assert recovered == 0x010203


# EOF
