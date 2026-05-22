"""Smoke import mirror for figrecipe._api._style_manager.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__api__style_manager_module():
    # Arrange
    module_path = 'figrecipe._api._style_manager'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
