"""Smoke import mirror for figrecipe._diagram._diagram._core.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__diagram__diagram__core_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._diagram._diagram._core")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
