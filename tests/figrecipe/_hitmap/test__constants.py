#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for hitmap reserved colors and the numpy->native serialiser."""

import numpy as np

from figrecipe._hitmap._constants import (
    HITMAP_AXES_COLOR,
    HITMAP_BACKGROUND_COLOR,
    to_native,
)


def test_background_color_is_hex_string():
    # Arrange
    color = HITMAP_BACKGROUND_COLOR
    # Act
    is_hex = isinstance(color, str) and color.startswith("#") and len(color) == 7
    # Assert
    assert is_hex


def test_axes_color_is_hex_string():
    # Arrange
    color = HITMAP_AXES_COLOR
    # Act
    is_hex = isinstance(color, str) and color.startswith("#") and len(color) == 7
    # Assert
    assert is_hex


def test_to_native_converts_numpy_integer_to_python_int():
    # Arrange
    value = np.int64(7)
    # Act
    result = to_native(value)
    # Assert
    assert isinstance(result, int)


def test_to_native_converts_numpy_float_to_python_float():
    # Arrange
    value = np.float64(1.5)
    # Act
    result = to_native(value)
    # Assert
    assert isinstance(result, float)


def test_to_native_converts_ndarray_to_list():
    # Arrange
    value = np.array([1, 2, 3])
    # Act
    result = to_native(value)
    # Assert
    assert result == [1, 2, 3]


def test_to_native_recurses_into_nested_dict():
    # Arrange
    value = {"a": np.int64(1), "b": [np.float64(2.0)]}
    # Act
    result = to_native(value)
    # Assert
    assert result == {"a": 1, "b": [2.0]}


# EOF
