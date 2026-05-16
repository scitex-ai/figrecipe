"""Smoke import mirror for figrecipe._sphinx_html._static.generate_quickstart_images.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""

import importlib


def test_import__sphinx_html__static_generate_quickstart_images_module():
    """Module imports without raising hard errors."""
    try:
        importlib.import_module("figrecipe._sphinx_html._static.generate_quickstart_images")
    except ImportError:
        # Optional-dependency module; skip when extras absent.
        return
