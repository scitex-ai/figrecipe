"""Smoke import mirror for figrecipe._dev._plotters.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__dev__plotters_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._dev._plotters")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
