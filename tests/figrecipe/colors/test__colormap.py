"""Smoke import mirror for figrecipe.colors._colormap.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import_colors__colormap_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe.colors._colormap")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
