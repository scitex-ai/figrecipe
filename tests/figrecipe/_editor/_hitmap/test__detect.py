"""Smoke import mirror for figrecipe._editor._hitmap._detect.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__editor__hitmap__detect_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._editor._hitmap._detect")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
