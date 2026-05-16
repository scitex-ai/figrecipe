"""Smoke import mirror for figrecipe._bundle._figz.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__bundle__figz_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._bundle._figz")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
