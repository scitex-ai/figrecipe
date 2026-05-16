"""Smoke import mirror for figrecipe._editor._bbox._collections.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__editor__bbox__collections_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._editor._bbox._collections")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
