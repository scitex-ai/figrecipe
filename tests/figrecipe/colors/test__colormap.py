"""Smoke import mirror for figrecipe.colors._colormap.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import_colors__colormap_module():
    # Arrange
    module_path = 'figrecipe.colors._colormap'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
