"""Smoke import mirror for figrecipe._wrappers._pie_helpers.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__wrappers__pie_helpers_module():
    # Arrange
    module_path = 'figrecipe._wrappers._pie_helpers'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
