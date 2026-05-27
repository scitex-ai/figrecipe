#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the flat SCITEX_STYLE preset and its value-parity with scitex.plt."""

import os

import pytest


def test_scitex_style_top_level_is_a_dict():
    # Arrange
    import figrecipe as fr

    # Act
    style = fr.SCITEX_STYLE

    # Assert
    assert isinstance(style, dict)


def test_scitex_style_has_expected_font_family_value():
    # Arrange
    import figrecipe as fr

    # Act
    family = fr.SCITEX_STYLE["font_family"]

    # Assert
    assert family == "Arial"


def test_scitex_style_has_expected_margin_left_value():
    # Arrange
    import figrecipe as fr

    # Act
    margin = fr.SCITEX_STYLE["margin_left_mm"]

    # Assert
    assert margin == 20


def test_scitex_style_presets_namespace_matches_top_level():
    # Arrange
    import figrecipe as fr
    from figrecipe import presets

    # Act
    same = fr.SCITEX_STYLE == presets.SCITEX_STYLE

    # Assert
    assert same


def test_scitex_style_pyplot_namespace_matches_presets():
    # Arrange
    from figrecipe import presets, pyplot

    # Act
    same = pyplot.SCITEX_STYLE == presets.SCITEX_STYLE

    # Assert
    assert same


def test_scitex_style_value_parity_with_scitex_plt_presets():
    # Arrange
    scitex_plt = pytest.importorskip("scitex.plt")
    import figrecipe as fr

    expected = scitex_plt.presets.SCITEX_STYLE

    # Act
    actual = fr.SCITEX_STYLE

    # Assert
    assert actual == expected


def test_presets_exposes_load_style_helper():
    # Arrange
    from figrecipe import presets

    # Act
    present = hasattr(presets, "load_style")

    # Assert
    assert present


def test_presets_exposes_resolve_style_value_helper():
    # Arrange
    from figrecipe import presets

    # Act
    present = hasattr(presets, "resolve_style_value")

    # Assert
    assert present


def test_load_style_returns_the_flat_style_dict():
    # Arrange
    from figrecipe import presets

    # Act
    style = presets.load_style()

    # Assert
    assert style == presets.SCITEX_STYLE


def test_save_style_writes_a_yaml_file(tmp_path):
    # Arrange
    from figrecipe import presets

    out = tmp_path / "style.yaml"

    # Act
    presets.save_style(out)

    # Assert
    assert out.exists()


def test_save_style_round_trip_preserves_axes_width(tmp_path):
    # Arrange
    from figrecipe import presets

    out = tmp_path / "style.yaml"
    presets.save_style(out)

    # Act
    reloaded = presets.load_style(out)

    # Assert
    assert reloaded["axes_width_mm"] == presets.SCITEX_STYLE["axes_width_mm"]


def test_get_default_dpi_returns_publication_value():
    # Arrange
    from figrecipe import presets

    # Act
    dpi = presets.get_default_dpi()

    # Assert
    assert dpi == 300


def test_get_display_dpi_returns_lower_resolution():
    # Arrange
    from figrecipe import presets

    # Act
    dpi = presets.get_display_dpi()

    # Assert
    assert dpi == 100


@pytest.fixture
def axes_width_env_override():
    # Arrange: set the env override, restore prior state on teardown.
    key = "SCITEX_PLT_AXES_WIDTH_MM"
    prior = os.environ.get(key)
    os.environ[key] = "55"
    yield
    if prior is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = prior


def test_resolve_style_value_honors_env_override(axes_width_env_override):
    # Arrange
    from figrecipe import presets

    # Act
    value = presets.resolve_style_value("axes.width_mm", None, 40, float)

    # Assert
    assert value == 55.0


# EOF
