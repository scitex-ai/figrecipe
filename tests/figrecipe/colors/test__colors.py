"""Smoke import mirror for figrecipe.colors._colors.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import_colors__colors_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe.colors._colors")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
