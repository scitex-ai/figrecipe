"""Smoke tests for scitex_dev.plt.demo_plotters."""

import pytest

pytest.importorskip("numpy")
pytest.importorskip("matplotlib")


def test_demo_plotters_module_loads():
    # Arrange
    dp_mod = pytest.importorskip("scitex_dev.plt.demo_plotters")
    # Act
    # Assert
    assert hasattr(dp_mod, "__path__")
