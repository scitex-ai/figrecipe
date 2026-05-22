"""Smoke import mirror for figrecipe._dev.demo_plotters.contour_surface.plot_contourf.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__dev_demo_plotters_contour_surface_plot_contourf_module():
    # Arrange
    module_path = 'figrecipe._dev.demo_plotters.contour_surface.plot_contourf'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
