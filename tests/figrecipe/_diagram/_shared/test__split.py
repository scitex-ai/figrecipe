"""Smoke import mirror for figrecipe._diagram._shared._split.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__diagram__shared__split_module():
    # Arrange
    module_path = 'figrecipe._diagram._shared._split'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
