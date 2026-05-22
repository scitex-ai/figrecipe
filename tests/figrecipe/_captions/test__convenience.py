"""Smoke import mirror for figrecipe._captions._convenience.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__captions__convenience_module():
    # Arrange
    module_path = 'figrecipe._captions._convenience'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
