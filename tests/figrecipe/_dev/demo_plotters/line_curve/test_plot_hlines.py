"""Smoke import mirror for figrecipe._dev.demo_plotters.line_curve.plot_hlines.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import pytest


def test_import__dev_demo_plotters_line_curve_plot_hlines_module():
    # Arrange
    # Act
    module_path = "figrecipe._dev.demo_plotters.line_curve.plot_hlines"
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
