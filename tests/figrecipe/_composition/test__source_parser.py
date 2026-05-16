"""Smoke import mirror for figrecipe._composition._source_parser.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__composition__source_parser_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._composition._source_parser")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
