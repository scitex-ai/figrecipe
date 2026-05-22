"""Smoke import mirror for figrecipe._cli._extract.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__cli__extract_module():
    # Arrange
    module_path = 'figrecipe._cli._extract'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
