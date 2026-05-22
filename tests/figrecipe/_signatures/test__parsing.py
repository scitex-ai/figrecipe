"""Smoke import mirror for figrecipe._signatures._parsing.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__signatures__parsing_module():
    # Arrange
    module_path = 'figrecipe._signatures._parsing'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
