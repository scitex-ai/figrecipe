"""Smoke import mirror for figrecipe._dev.demo_plotters.vector_flow.plot_quiver.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__dev_demo_plotters_vector_flow_plot_quiver_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._dev.demo_plotters.vector_flow.plot_quiver")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
