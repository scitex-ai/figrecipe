"""Smoke tests for scitex_dev.plt.demo_plotters."""

import pytest

pytest.importorskip("numpy")
pytest.importorskip("matplotlib")

import scitex_dev.plt.demo_plotters as dp_mod  # noqa: E402


def test_demo_plotters_module_loads():
    assert hasattr(dp_mod, "__path__")
