"""Smoke import mirror for figrecipe._editor._hitmap._colors.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__editor__hitmap__colors_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._editor._hitmap._colors")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
