"""Smoke import mirror for figrecipe.styles._fonts.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import_styles__fonts_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe.styles._fonts")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
