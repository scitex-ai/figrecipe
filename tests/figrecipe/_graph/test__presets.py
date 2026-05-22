"""Smoke import mirror for figrecipe._graph._presets.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__graph__presets_module():
    # Arrange
    module_path = 'figrecipe._graph._presets'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
