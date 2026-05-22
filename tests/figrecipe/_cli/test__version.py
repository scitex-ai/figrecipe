"""Smoke import mirror for figrecipe._cli._version.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__cli__version_module():
    # Arrange
    # Arrange
    # Act
    # Assert
    module_path = 'figrecipe._cli._version'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
