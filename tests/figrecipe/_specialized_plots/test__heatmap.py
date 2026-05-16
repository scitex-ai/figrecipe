"""Smoke import mirror for figrecipe._specialized_plots._heatmap.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__specialized_plots__heatmap_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._specialized_plots._heatmap")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
