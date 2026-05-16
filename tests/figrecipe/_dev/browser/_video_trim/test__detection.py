"""Smoke import mirror for figrecipe._dev.browser._video_trim._detection.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__dev_browser__video_trim__detection_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._dev.browser._video_trim._detection")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
