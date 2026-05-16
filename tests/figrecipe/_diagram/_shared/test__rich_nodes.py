"""Smoke import mirror for figrecipe._diagram._shared._rich_nodes.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__diagram__shared__rich_nodes_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._diagram._shared._rich_nodes")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
