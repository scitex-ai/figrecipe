"""Smoke import mirror for figrecipe._dev.demo_plotters.scatter_points.plot_scatter.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__dev_demo_plotters_scatter_points_plot_scatter_module():
    # Arrange
    module_path = 'figrecipe._dev.demo_plotters.scatter_points.plot_scatter'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
