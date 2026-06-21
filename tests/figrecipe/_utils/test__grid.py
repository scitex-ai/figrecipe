#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the shared grid-id helper (single source of truth for panel keys)."""

from figrecipe._utils._grid import grid_id, parse_grid_id


def test_grid_id_origin_returns_r0c0():
    # Arrange
    row, col = 0, 0
    # Act
    result = grid_id(row, col)
    # Assert
    assert result == "r0c0"


def test_grid_id_arbitrary_position_returns_canonical_string():
    # Arrange
    row, col = 1, 2
    # Act
    result = grid_id(row, col)
    # Assert
    assert result == "r1c2"


def test_grid_id_double_digit_position_returns_canonical_string():
    # Arrange
    row, col = 10, 11
    # Act
    result = grid_id(row, col)
    # Assert
    assert result == "r10c11"


def test_parse_grid_id_canonical_form_returns_row_col():
    # Arrange
    key = "r1c2"
    # Act
    result = parse_grid_id(key)
    # Assert
    assert result == (1, 2)


def test_parse_grid_id_legacy_form_still_parses():
    # Arrange
    key = "ax_1_2"  # legacy form must still load (back-compat)
    # Act
    result = parse_grid_id(key)
    # Assert
    assert result == (1, 2)


def test_parse_grid_id_mm_key_returns_none():
    # Arrange
    key = "ax_mm_0"
    # Act
    result = parse_grid_id(key)
    # Assert
    assert result is None


def test_parse_grid_id_garbage_returns_none():
    # Arrange
    key = "garbage"
    # Act
    result = parse_grid_id(key)
    # Assert
    assert result is None


def test_parse_grid_id_empty_returns_none():
    # Arrange
    key = ""
    # Act
    result = parse_grid_id(key)
    # Assert
    assert result is None


def test_grid_id_roundtrip_recovers_position():
    # Arrange
    row, col = 2, 3
    # Act
    result = parse_grid_id(grid_id(row, col))
    # Assert
    assert result == (row, col)
