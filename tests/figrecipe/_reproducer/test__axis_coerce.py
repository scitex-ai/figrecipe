#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coercion of replayed axis-limit / axis-line values (figrecipe).

``set_xlim`` / ``set_ylim`` / ``axvline`` / ``axhline`` are inherently numeric or
datetime. A recipe may still carry the value as a string: an ISO datetime
(datetime axes) or a stringified number like ``'0'`` from recipes predating
native numpy-scalar serialization. ``coerce_axis_value`` turns numeric strings
into ``float`` and ISO strings into ``datetime`` so matplotlib can apply them on
replay (otherwise ``ConversionError: Failed to convert value(s) to axis units``).
"""

import datetime as _dt

import pytest

from figrecipe._reproducer._axis_coerce import coerce_axis_value


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_stringified_number_coerced_to_float():
    # Arrange
    value = "0"
    # Act
    result = coerce_axis_value(value)
    # Assert
    assert result == 0.0


def test_stringified_number_warns_about_stale_recipe():
    # Arrange
    value = "1.5"
    # Act
    # Assert
    with pytest.warns(UserWarning, match="predates native numpy-scalar"):
        coerce_axis_value(value)


def test_iso_datetime_string_parsed_to_datetime():
    # Arrange
    value = "2024-01-02"
    # Act
    result = coerce_axis_value(value)
    # Assert
    assert result == _dt.datetime(2024, 1, 2)


def test_non_numeric_string_returned_unchanged():
    # Arrange
    value = "category-label"
    # Act
    result = coerce_axis_value(value)
    # Assert
    assert result == "category-label"


def test_numeric_value_passes_through_unchanged():
    # Arrange
    value = 1.5
    # Act
    result = coerce_axis_value(value)
    # Assert
    assert result == 1.5
