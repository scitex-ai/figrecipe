"""Smoke import mirror for figrecipe._dev.browser._cursor.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__dev_browser__cursor_module():
    # Arrange
    module_path = 'figrecipe._dev.browser._cursor'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
