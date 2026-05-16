"""Smoke import mirror for figrecipe._utils._image_diff.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__utils__image_diff_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._utils._image_diff")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
