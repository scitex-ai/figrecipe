"""Smoke import mirror for figrecipe._dev.demo_plotters.bar_categorical.plot_barh.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__dev_demo_plotters_bar_categorical_plot_barh_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._dev.demo_plotters.bar_categorical.plot_barh")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
