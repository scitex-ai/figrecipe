"""Tests for figrecipe.colors._colors conversion helpers."""


import pytest


def test_import_colors__colors_module():
    # Arrange
    module_path = "figrecipe.colors._colors"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_rgb2rgba_round_trip_rgb_channels():
    # Arrange
    mod = pytest.importorskip("figrecipe.colors._colors")
    rgb = [255, 0, 0]
    # Act
    rgba = mod.rgb2rgba(rgb)
    back = mod.rgba2rgb(rgba)
    # Assert
    assert back == [255.0, 0.0, 0.0]
    assert rgba[3] == 1.0


def test_bgr2rgb_reverses_channel_order_and_round_trips():
    # Arrange
    mod = pytest.importorskip("figrecipe.colors._colors")
    bgr = [0, 128, 255]
    # Act
    rgb = mod.bgr2rgb(bgr)
    back = mod.rgb2bgr(rgb)
    # Assert
    assert rgb == [255, 128, 0]
    assert back == bgr


def test_bgra2rgba_preserves_alpha_and_round_trips():
    # Arrange
    mod = pytest.importorskip("figrecipe.colors._colors")
    bgra = [10, 20, 30, 0.5]
    # Act
    rgba = mod.bgra2rgba(bgra)
    back = mod.rgba2bgra(rgba)
    # Assert
    assert rgba == [30, 20, 10, 0.5]
    assert back == bgra


def test_rgba2hex_known_value():
    # Arrange
    mod = pytest.importorskip("figrecipe.colors._colors")
    # rgba2hex expects rgb 0-255 ints and alpha 0-1
    rgba = [255, 0, 0, 1.0]
    # Act
    hx = mod.rgba2hex(rgba)
    # Assert
    assert hx == "#ff0000ff"


def test_update_alpha_replaces_last_only():
    # Arrange
    mod = pytest.importorskip("figrecipe.colors._colors")
    rgba = [0.1, 0.2, 0.3, 1.0]
    # Act
    out = mod.update_alpha(rgba, 0.4)
    # Assert
    assert out[:3] == [0.1, 0.2, 0.3]
    assert out[3] == 0.4
