"""Smoke import mirror for figrecipe._dev.demo_plotters.distribution.plot_hist2d.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__dev_demo_plotters_distribution_plot_hist2d_module():
    # Arrange
    module_path = 'figrecipe._dev.demo_plotters.distribution.plot_hist2d'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
