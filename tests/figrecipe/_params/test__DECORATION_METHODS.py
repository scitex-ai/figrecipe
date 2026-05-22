"""Smoke import mirror for figrecipe._params._DECORATION_METHODS.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__params__DECORATION_METHODS_module():
    # Arrange
    module_path = 'figrecipe._params._DECORATION_METHODS'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
