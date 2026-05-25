"""Smoke tests for scitex_dev.plt (ported from umbrella)."""

import pytest

pytest.importorskip("numpy")
pytest.importorskip("matplotlib")

import scitex_dev.plt as plt_mod  # noqa: E402


def test_plt_module_has_dunder_path():
    # Arrange
    # Act
    # Assert
    assert hasattr(plt_mod, "__path__")


def test_plt_subpackages_importable():
    # Arrange
    # Act
    # Assert
    import scitex_dev.plt.demo_plotters  # noqa: F401
    import scitex_dev.plt.mpl  # noqa: F401

    assert True
