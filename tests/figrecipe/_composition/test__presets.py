#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for figrecipe._composition._presets (named compose layout aliases).

Card figrecipe-bioinformatics-figure-beauty-20261006, source-adoption phase:
the adoption map's last open item -- layout presets as named compose
aliases. These are names for grid shapes ``fr.compose`` already accepts
(``layout=(nrows, ncols)``), so the layer is behaviour-neutral: it only
spells ``(1, 2)`` as ``\"side_by_side\"``. Tiled/bento layouts stay explicit
``layout=[[...]]`` (see _tile.py).
"""

import pytest

from figrecipe._composition._presets import (
    COMPOSE_LAYOUT_PRESETS,
    list_compose_presets,
    resolve_compose_preset,
)


class TestResolveComposePreset:
    def test_side_by_side_resolves_to_one_row_two_cols(self):
        # Arrange
        # Act
        layout = resolve_compose_preset("side_by_side")
        # Assert
        assert layout == (1, 2)

    def test_quad_resolves_to_two_by_two(self):
        # Arrange
        # Act
        layout = resolve_compose_preset("quad")
        # Assert
        assert layout == (2, 2)

    def test_every_preset_value_is_a_positive_grid_shape(self):
        # Arrange
        # Act
        # Assert -- every alias must be consumable as layout=(nrows, ncols).
        for name in COMPOSE_LAYOUT_PRESETS:
            rows, cols = resolve_compose_preset(name)
            assert rows >= 1 and cols >= 1

    def test_unknown_preset_raises(self):
        # Arrange
        name = "bento_tiled_not_a_grid_alias"
        # Act
        # Assert
        with pytest.raises(KeyError, match="bento_tiled_not_a_grid_alias"):
            resolve_compose_preset(name)


class TestListComposePresets:
    def test_lists_every_defined_preset(self):
        # Arrange
        # Act
        presets = list_compose_presets()
        # Assert
        assert set(presets) == set(COMPOSE_LAYOUT_PRESETS)

    def test_every_listed_preset_has_a_description(self):
        # Arrange
        # Act
        presets = list_compose_presets()
        # Assert
        assert all(isinstance(v, str) and v for v in presets.values())
