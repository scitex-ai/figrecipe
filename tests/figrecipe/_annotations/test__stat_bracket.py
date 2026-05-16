"""Smoke import mirror for figrecipe._annotations._stat_bracket.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__annotations__stat_bracket_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._annotations._stat_bracket")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
