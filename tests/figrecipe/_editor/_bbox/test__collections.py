"""Smoke import mirror for figrecipe._editor._bbox._collections.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__editor__bbox__collections_module():
    # Arrange
    module_path = 'figrecipe._editor._bbox._collections'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
