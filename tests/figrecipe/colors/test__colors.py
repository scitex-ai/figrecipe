"""Smoke import mirror for figrecipe.colors._colors.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import pytest


def test_import_colors__colors_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = "figrecipe.colors._colors"
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path


def test_rgb2rgba_rgba2rgb_round_trips_primary():
    # Arrange
    from figrecipe.colors._colors import rgb2rgba, rgba2rgb

    rgb = [255, 0, 0]
    # Act
    result = rgba2rgb(rgb2rgba(rgb))
    # Assert
    assert result == pytest.approx([255.0, 0.0, 0.0])


def test_rgb2rgba_rgba2rgb_round_trips_within_rounding_tolerance():
    # Arrange
    from figrecipe.colors._colors import rgb2rgba, rgba2rgb

    rgb = [128, 64, 32]
    # Act
    # rgb2rgba rounds to 2 decimals in the 0-1 space, so the back-conversion
    # is only exact to roughly +/-3 in the 0-255 space.
    result = rgba2rgb(rgb2rgba(rgb))
    # Assert
    assert result == pytest.approx(rgb, abs=3)


def test_rgb2rgba_appends_alpha():
    # Arrange
    from figrecipe.colors._colors import rgb2rgba

    # Act
    result = rgb2rgba([255, 0, 0], alpha=0.5)
    # Assert
    assert len(result) == 4 and result[-1] == 0.5


def test_bgr2rgb_reverses_channel_order():
    # Arrange
    from figrecipe.colors._colors import bgr2rgb

    # Act
    result = bgr2rgb([1, 2, 3])
    # Assert
    assert result == [3, 2, 1]


def test_bgr2rgb_rgb2bgr_round_trips():
    # Arrange
    from figrecipe.colors._colors import bgr2rgb, rgb2bgr

    rgb = [10, 20, 30]
    # Act
    result = bgr2rgb(rgb2bgr(rgb))
    # Assert
    assert result == rgb


def test_bgra2rgba_reverses_rgb_and_preserves_alpha():
    # Arrange
    from figrecipe.colors._colors import bgra2rgba

    # Act
    result = bgra2rgba([1, 2, 3, 4])
    # Assert: rgb reversed to [3, 2, 1], alpha (4) preserved in place.
    assert result == [3, 2, 1, 4] and result[3] == 4


def test_bgra2rgba_rgba2bgra_round_trips_preserving_alpha():
    # Arrange
    from figrecipe.colors._colors import bgra2rgba, rgba2bgra

    rgba = [10, 20, 30, 40]
    # Act
    result = bgra2rgba(rgba2bgra(rgba))
    # Assert: round-trip is identity, alpha (40) preserved.
    assert result == rgba and result[3] == 40


def test_rgba2hex_formats_known_value():
    # Arrange
    from figrecipe.colors._colors import rgba2hex

    # Act
    # rgb components are 0-255 ints; alpha is 0-1 and scaled by 255.
    result = rgba2hex([255, 128, 0, 1.0])
    # Assert
    assert result == "#ff8000ff"


def test_update_alpha_replaces_last_and_keeps_rgb():
    # Arrange
    from figrecipe.colors._colors import update_alpha

    # Act
    result = update_alpha([1, 2, 3, 4], 9)
    # Assert
    assert result == [1, 2, 3, 9]
