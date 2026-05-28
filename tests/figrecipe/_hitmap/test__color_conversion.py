#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for ID <-> RGB encoding used to label hitmap elements."""

import pytest

from figrecipe._hitmap._color_conversion import id_to_rgb, rgb_to_id, rgb_to_id_lookup


@pytest.mark.parametrize(
    "rgb,expected",
    [
        ((0, 0, 0), 0),
        ((0, 0, 1), 1),
        ((0, 1, 0), 256),
        ((1, 0, 1), 0x010001),
        ((255, 255, 255), 0xFFFFFF),
    ],
)
def test_rgb_to_id_packs_24bit(rgb, expected):
    # Arrange
    r, g, b = rgb
    # Act
    packed = rgb_to_id(r, g, b)
    # Assert
    assert packed == expected


def test_id_to_rgb_background_is_black():
    # Arrange
    element_id = 0
    # Act
    rgb = id_to_rgb(element_id)
    # Assert
    assert rgb == (0, 0, 0)


def test_id_to_rgb_is_deterministic():
    # Arrange
    element_id = 12345
    # Act
    first, second = id_to_rgb(element_id), id_to_rgb(element_id)
    # Assert
    assert first == second


def test_id_to_rgb_returns_three_channel_tuple():
    # Arrange
    element_id = 12345
    # Act
    rgb = id_to_rgb(element_id)
    # Assert
    assert len(rgb) == 3


def test_id_to_rgb_channels_are_byte_range():
    # Arrange
    element_id = 16777215
    # Act
    r, g, b = id_to_rgb(element_id)
    # Assert
    assert all(0 <= c <= 255 for c in (r, g, b))


def test_rgb_to_id_lookup_finds_known_id():
    # Arrange
    element_id = 4321
    r, g, b = id_to_rgb(element_id)
    color_map = {element_id: {"rgb": [r, g, b], "type": "line"}}
    # Act
    found = rgb_to_id_lookup(r, g, b, color_map)
    # Assert
    assert found == element_id


def test_rgb_to_id_lookup_returns_zero_for_unknown_color():
    # Arrange
    color_map = {1: {"rgb": [1, 1, 1], "type": "line"}}
    r, g, b = id_to_rgb(999999)
    # Act
    found = rgb_to_id_lookup(r, g, b, color_map)
    # Assert
    assert found == 0


# EOF
