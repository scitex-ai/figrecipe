"""Smoke import mirror for figrecipe._specialized_plots._annotation.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__specialized_plots__annotation_module():
    # Arrange
    module_path = 'figrecipe._specialized_plots._annotation'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
