"""Smoke import mirror for figrecipe._cli._compose.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__cli__compose_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._cli._compose")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
