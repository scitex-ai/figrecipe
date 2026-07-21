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


def test_str2bgra_honours_alpha():
    # Arrange
    mod = pytest.importorskip("figrecipe.colors._colors")
    alpha = 0.3
    # Act
    bgra = mod.str2bgra("blue", alpha=alpha)
    # Assert
    assert bgra[-1] == alpha


def test_str2bgra_defaults_to_opaque():
    # Arrange
    mod = pytest.importorskip("figrecipe.colors._colors")
    # Act
    bgra = mod.str2bgra("blue")
    # Assert
    assert bgra[-1] == 1.0


def test_str2bgra_channels_are_reversed_str2rgba():
    # Arrange
    mod = pytest.importorskip("figrecipe.colors._colors")
    alpha = 0.3
    # Act
    rgba = mod.str2rgba("blue", alpha=alpha)
    bgra = mod.str2bgra("blue", alpha=alpha)
    # Assert
    assert bgra == [rgba[2], rgba[1], rgba[0], alpha]
