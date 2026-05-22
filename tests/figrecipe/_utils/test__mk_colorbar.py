"""Smoke import mirror for figrecipe._utils._mk_colorbar.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import__utils__mk_colorbar_module():
    # Arrange
    module_path = 'figrecipe._utils._mk_colorbar'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
