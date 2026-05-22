"""Smoke import mirror for figrecipe.styles._themes.

Auto-generated subpackage mirror placeholder; replace with real tests
as the module matures. Satisfies the src<->tests mirror audit rule.
"""


import pytest


def test_import_styles__themes_module():
    # Arrange
    module_path = 'figrecipe.styles._themes'
    # Act
    mod = pytest.importorskip(module_path)
    # Assert
    assert mod.__name__ == module_path
